# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

---

## [Unreleased]

---

## [0.1.0] - 2026-05-23

### Added

- Established `se-contract-kit` as the generic contract loading, resolution,
  and validation engine for Structural Explainability contract repositories.
- Added staged source layout:
  - `base`
  - `declarations`
  - `resolution`
  - `validation`
- Added repository declaration loading for `MANIFEST.toml` and
  `SE_MANIFEST.toml`.
- Added contract configuration loading for `contract.toml`.
- Added dependency reference parsing.
- Added artifact and authority resolution primitives.
- Added lockfile data structures and JSON read/write support.
- Added immutable validation check registry for kit defaults and
  repository-specific extensions.
- Added validation result model using the shared check status vocabulary.
- Added validation runner with strict-mode support.
- Added initial generic validation checks.
- Added `se-contract-kit` command-line entry point.
- Added repository manifest, citation metadata, documentation, tests, and
  release configuration.

### Changed

- Separated generic contract-engine machinery from Accountable Record
  contract content.

---

## Notes on Versioning and Releases

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

- **MAJOR** versions indicate breaking changes.
- **MINOR** versions indicate backward-compatible additions or clarifications.
- **PATCH** versions indicate editorial fixes, documentation updates, or
  non-normative changes.

Versions are defined by git tags of the form `vX.Y.Z`.
Tagged releases are the authoritative source of version state.

## Release Procedure (Required)

Follow these steps exactly when creating a new release.

### Task 1. Update release metadata (manual edits)

1.1. `CITATION.cff` - update `version` and `date-released`
1.2. CHANGELOG.md: add section, move unreleased entries, update links

### Task 2. Validate

```shell
uv self update
uv python pin 3.14
uv sync --extra dev --extra docs --upgrade

uvx pre-commit install

git add -A
uvx pre-commit run --all-files
# repeat if changes were made
git add -A
uvx pre-commit run --all-files

# validate manifest
uv run se-manifest validate-manifest --path MANIFEST.toml --strict

# run contract-kit checks
uv run se-contract-kit check --strict

# types, tests, docs
uv run python -m pyright
uv run python -m pytest
uv run python -m zensical build
uvx pre-commit run --all-files
```

### Task 3. Commit, tag, push

```shell
git add -A
git commit -m "Prepare X.Y.Z"
git push -u origin main
```

Verify actions run on GitHub. After success:

```shell
git tag vX.Y.Z -m "X.Y.Z"
git push origin vX.Y.Z
```

### Task 4. Verify tag consistency

```shell
uv run python -m se_manifest_schema validate --strict --require-tag
```

Confirms CITATION.cff version matches the pushed git tag.
Run this after `git push origin vX.Y.Z`; it will fail before that point.

## Only As Needed (delete a tag)

```shell
git tag -d vX.Z.Y
git push origin :refs/tags/vX.Z.Y
```

## Links

[Unreleased]: https://github.com/structural-explainability/se-contract-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/structural-explainability/se-contract-kit/releases/tag/v0.1.0

<!-- markdownlint-enable MD024 -->
