# Changelog

All notable changes to BioShell will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

See [docs/MAINTENANCE.md](docs/MAINTENANCE.md) for the versioning policy and release process.

## [Unreleased]

### Added
- GitHub Action (`update-tool-versions`) that checks pinned tool versions against upstream on a schedule (1 January and 1 July) and opens a pull request with any updates. See [docs/MAINTENANCE.md](docs/MAINTENANCE.md#5-github-actions-automation).

### Fixed
- Update tools to the latest version [PR #13](https://github.com/AustralianBioCommons/BioShell/pull/13).
- Updated README based on review feedback [Issue #14](https://github.com/AustralianBioCommons/BioShell/issues/14).

### Changed
- Renamed Shelley and updated installation to use `uv`.
