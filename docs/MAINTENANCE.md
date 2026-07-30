# BioShell Operational Update Schedule & Maintenance Plan

## 1. Background & Context

This document defines the update cadence, automated tooling, roles, and review workflow that keeps BioShell images current, reproducible, and compatible across all supported infrastructures.

## 2. Versioning

BioShell follows [Semantic Versioning](https://semver.org/) (SemVer): `MAJOR.MINOR.PATCH`

| Version increment | Trigger | Action | Example |
|---|---|---|---|
| MAJOR (`X.0.0`) | Breaking changes — users must change how they work | Manual | New base OS, dropping an infrastructure platform, restructured access model |
| MINOR (`1.X.0`) | New features, backwards compatible | GitHub Action (~6 monthly), or manual for larger additions | New software bundle, new interface (RStudio), new platform supported, significant new dataset |
| PATCH (`1.1.X`) | Bug fixes and small updates | Manual | Patched config, corrected dataset, minor documentation fix |

The version number is defined by the `image_version` variable in [`build/openstack-bioshell.pkr.hcl`](../build/openstack-bioshell.pkr.hcl) and is tied to a specific VM image snapshot — not to documentation or policy changes alone.

Pre-1.0.0, release-candidate labels (e.g. `1.0.0-rc1`) may be used to signal a build intended for validation ahead of a production release. The jump to `1.0.0` signals production readiness.

## 3. Objectives of the Update Process

- Maintain a predictable update cadence aligned with infrastructure maintenance windows.
- Automate routine base-tool version bumps via GitHub Actions, reducing manual effort.
- Ensure build reproducibility through modularised Ansible roles.
- Guarantee image compatibility across Nectar, Nirin, and future cloud platforms.
- Provide a consistent versioning and release workflow through GitHub.
- Maintain automated checks to validate tool versions before release.
- Facilitate timely cross-infrastructure review and approval.

## 4. Update Frequency & Cadence

Scheduled updates run twice a year (January and July), aligned to infrastructure maintenance windows, with patch releases as required outside that cycle.

## 5. GitHub Actions Automation

Routine base-tool version bumps are automated by the [`update-tool-versions`](../.github/workflows/update-tool-versions.yml) workflow. This removes the need for manual monitoring of upstream tool releases and ensures updates are reviewed through a consistent pull request workflow.

| Element | Detail |
|---|---|
| Trigger | Scheduled cron job, `0 3 1 1,7 *` (03:00 UTC on 1 January and 1 July); also runnable on demand via `workflow_dispatch` |
| Check | [`check-versions.py`](../.github/scripts/check-versions.py) compares the pinned versions in [`build/ansible/vars/tool-versions.yml`](../build/ansible/vars/tool-versions.yml) against upstream (GitHub releases, PyPI, apt, vendor endpoints) for Singularity, shpc, Go, Nextflow, nf-core, RStudio, Snakemake, and R |
| Bump | If any tool version changed, [`bump-image-version.py`](../.github/scripts/bump-image-version.py) increments the MINOR version of `image_version` in `build/openstack-bioshell.pkr.hcl` |
| Output | Opens a pull request with a summary table of the tool versions changed |
| Review | PR reviewed  |
| Merge & tag | Product owner (or delegate) merges the approved PR and tags the new version in GitHub |

Notes on what the workflow does **not** cover:
- `java_version` is a major-LTS selector and is intentionally excluded from auto-bumping.
- Manual or ad-hoc updates outside the cron cycle remain possible for urgent security patches — these follow the same PR-review-merge workflow, just triggered manually (`workflow_dispatch` or a direct PR) instead of waiting for the next cron run.
- The workflow only bumps *pinned tool versions*. New software bundles, new platforms, or other MINOR/MAJOR changes are made by hand and versioned manually per the table in [Section 2](#2-versioning).

## 6. Release Checklist

When merging a version bump (automated or manual):

1. Confirm the automated version-check PR (or manual change) has been reviewed by both platform collaborators.
2. Build and smoke-test the image on at least one of Nectar or Nirin before merge, where practical.
3. Merge the PR.
4. Tag the release in GitHub matching `image_version` (e.g. `v1.1.0`).
