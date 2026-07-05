#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

import yaml

VARS_FILE = "build/ansible/vars/tool-versions.yml"
USER_AGENT = "tool-version-checker (+https://github.com)"

def http_get_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def http_get_text(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode()

def github_latest_release_tag(repo):
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = http_get_json(f"https://api.github.com/repos/{repo}/releases/latest", headers=headers)
    return data["tag_name"]

def strip_v_prefix(tag):
    return tag[1:] if tag.lower().startswith("v") else tag

def semver_tuple(v):
    parts = re.findall(r"\d+", v)
    return tuple(int(p) for p in parts) if parts else (0,)


# ---------------------------------------------------------------------------
# Per-tool checkers
# ---------------------------------------------------------------------------

def check_singularity(current):
    tag = github_latest_release_tag("sylabs/singularity")
    latest = strip_v_prefix(tag)
    if semver_tuple(latest) > semver_tuple(current):
        return latest, f"https://github.com/sylabs/singularity/releases/tag/{tag}"
    return None, None

def check_shpc(current):
    tag = github_latest_release_tag("singularityhub/singularity-hpc")
    latest = strip_v_prefix(tag)
    if semver_tuple(latest) > semver_tuple(current):
        return latest, f"https://github.com/singularityhub/singularity-hpc/releases/tag/{tag}"
    return None, None

def check_go(current):
    data = http_get_json("https://go.dev/dl/?mode=json")
    stable = [d for d in data if d.get("stable")]
    if not stable:
        return None, None
    latest_tag = stable[0]["version"]
    latest = latest_tag[2:] if latest_tag.startswith("go") else latest_tag
    if semver_tuple(latest) > semver_tuple(current):
        return latest, "https://go.dev/dl/"
    return None, None

def check_nextflow(current):
    tag = github_latest_release_tag("nextflow-io/nextflow")
    latest = strip_v_prefix(tag)
    if semver_tuple(latest) > semver_tuple(current):
        return latest, f"https://github.com/nextflow-io/nextflow/releases/tag/{tag}"
    return None, None

def check_nfcore(current):
    data = http_get_json("https://pypi.org/pypi/nf-core/json")
    latest = data["info"]["version"]
    if semver_tuple(latest) > semver_tuple(current):
        return latest, "https://pypi.org/project/nf-core/"
    return None, None

RSTUDIO_VERSION_PATTERN = re.compile(r"^\d{4}\.\d{1,2}\.\d+[+-]\d+$")

def find_rstudio_version_in_json(data):
    if isinstance(data, str):
        return data if RSTUDIO_VERSION_PATTERN.match(data) else None
    if isinstance(data, dict):
        for value in data.values():
            found = find_rstudio_version_in_json(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_rstudio_version_in_json(item)
            if found:
                return found
    return None


def check_rstudio(current_full):
    data = http_get_json("https://www.rstudio.com/wp-content/downloads.json")
    version_full_raw = find_rstudio_version_in_json(data)

    if version_full_raw is None:
        shape = list(data.keys()) if isinstance(data, dict) else type(data).__name__
        raise RuntimeError(
            f"could not find an RStudio version string in downloads.json response "
            f"(top-level shape: {shape})"
        )

    version_full = version_full_raw.replace("+", "-")
    version_short = version_full.split("-")[0]

    if semver_tuple(version_full) > semver_tuple(current_full):
        return {"rstudio_version_full": version_full, "rstudio_version": version_short}, \
               "https://www.rstudio.com/wp-content/downloads.json"
    return None, None


def check_apt_package(package_name, current):
    result = subprocess.run(
        ["apt-cache", "madison", package_name],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"apt-cache madison {package_name} failed: {result.stderr.strip()}")

    first_line = result.stdout.strip().splitlines()[0]
    pkg_version = [p.strip() for p in first_line.split("|")][1]

    latest = pkg_version.split("-")[0]

    if semver_tuple(latest) > semver_tuple(current):
        return latest, f"apt-cache madison {package_name} (ubuntu noble/universe)"
    return None, None

def check_r(current):
    return check_apt_package("r-base", current)

def check_snakemake_apt(current):
    return check_apt_package("snakemake", current)

def check_jupyter(current):
    now_stamp = datetime.now(timezone.utc).strftime("%Y.%m")
    if now_stamp != current:
        return now_stamp, "(timestamp - not an upstream version)"
    return None, None


CHECKS = [
    ("Singularity", "singularity_version", check_singularity),
    ("shpc", "shpc_version", check_shpc),
    ("Go", "go_version", check_go),
    ("Nextflow", "nextflow_version", check_nextflow),
    ("nf-core", "nfcore_version", check_nfcore),
    ("RStudio", "rstudio_version_full", check_rstudio),
    ("Snakemake (apt)", "snakemake_version", check_snakemake_apt),
    ("R (apt)", "r_version", check_r),
    ("Jupyter (timestamp)", "jupyter_version", check_jupyter),
]


def main():
    with open(VARS_FILE) as f:
        raw_text = f.read()
    tool_vars = yaml.safe_load(raw_text)

    changes = []  # list of dicts: {label, key, old, new, source}
    errors = []   # list of (label, error message)

    for label, key, checker in CHECKS:
        current = tool_vars.get(key)
        if current is None:
            errors.append((label, f"key '{key}' not found in {VARS_FILE}"))
            continue
        try:
            new_value, source = checker(current)
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError,
                json.JSONDecodeError, RuntimeError, subprocess.SubprocessError) as e:
            errors.append((label, str(e)))
            continue

        if new_value is None:
            continue

        if isinstance(new_value, dict):
            # multi-key update (RStudio: full + short)
            for sub_key, sub_new in new_value.items():
                old = tool_vars.get(sub_key)
                if old != sub_new:
                    changes.append({"label": label, "key": sub_key, "old": old, "new": sub_new, "source": source})
        else:
            old = tool_vars.get(key)
            if old != new_value:
                changes.append({"label": label, "key": key, "old": old, "new": new_value, "source": source})

    updated_text = raw_text
    for change in changes:
        pattern = re.compile(
            rf'^({re.escape(change["key"])}[ \t]*:[ \t]*)"?{re.escape(str(change["old"]))}"?[ \t]*$',
            re.MULTILINE,
        )
        replacement = f'{change["key"]}: "{change["new"]}"'
        new_text, count = pattern.subn(replacement, updated_text)
        if count == 0:
            key_name = change["key"]
            old_val = change["old"]
            errors.append((change["label"], f"could not locate '{key_name}: {old_val}' in file to replace"))
            continue
        updated_text = new_text

    if changes:
        with open(VARS_FILE, "w") as f:
            f.write(updated_text)

    # Write outputs for the GitHub Actions workflow to consume
    with open("version_check_summary.md", "w") as f:
        if changes:
            f.write("## Tool version updates found\n\n")
            f.write("| Tool | Variable | Old | New | Source |\n")
            f.write("|---|---|---|---|---|\n")
            for c in changes:
                f.write(f"| {c['label']} | `{c['key']}` | `{c['old']}` | `{c['new']}` | {c['source']} |\n")
        else:
            f.write("No tool version updates found.\n")

        if errors:
            f.write("\n### Checks that could not complete\n\n")
            for label, msg in errors:
                f.write(f"- **{label}**: {msg}\n")

        f.write("\n### Tools intentionally not auto-checked\n\n")
        f.write("- `java_version` - major LTS selector, not an auto-bump target.\n")

    # Set a GitHub Actions output so the workflow knows whether to open a PR
    gha_output = sys.argv[1] if len(sys.argv) > 1 else None
    if gha_output:
        with open(gha_output, "a") as f:
            f.write(f"changes_found={'true' if changes else 'false'}\n")

    print(f"Checked {len(CHECKS)} tools: {len(changes)} updates found, {len(errors)} errors.")
    for c in changes:
        print(f"  {c['label']}: {c['key']} {c['old']} -> {c['new']}")
    for label, msg in errors:
        print(f"  [error] {label}: {msg}", file=sys.stderr)


if __name__ == "__main__":
    main()