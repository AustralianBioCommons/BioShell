#!/usr/bin/env python3

import re
import sys

PKR_FILE = "build/openstack-bioshell.pkr.hcl"


def bump_minor(version):
    major, minor, patch = (int(p) for p in version.split("."))
    return f"{major}.{minor + 1}.0"


def main():
    with open(PKR_FILE) as f:
        text = f.read()

    pattern = re.compile(
        r'(variable\s+"image_version"\s*{\s*type\s*=\s*string\s*default\s*=\s*")'
        r'(\d+\.\d+\.\d+)'
        r'(")',
        re.DOTALL,
    )

    match = pattern.search(text)
    if not match:
        print(f"Could not find image_version variable block in {PKR_FILE}", file=sys.stderr)
        sys.exit(1)

    old_version = match.group(2)
    new_version = bump_minor(old_version)

    new_text = pattern.sub(lambda m: f"{m.group(1)}{new_version}{m.group(3)}", text, count=1)

    with open(PKR_FILE, "w") as f:
        f.write(new_text)

    print(f"image_version: {old_version} -> {new_version}")

    gha_output = sys.argv[1] if len(sys.argv) > 1 else None
    if gha_output:
        with open(gha_output, "a") as f:
            f.write(f"old_image_version={old_version}\n")
            f.write(f"new_image_version={new_version}\n")


if __name__ == "__main__":
    main()