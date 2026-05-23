# SE Contract Kit

[![PyPI](https://img.shields.io/pypi/v/se-contract-kit?logo=pypi&label=pypi)](https://pypi.org/project/se-contract-kit/)
[![Docs Site](https://img.shields.io/badge/docs-site-blue?logo=github)](https://structural-explainability.github.io/se-contract-kit/)
[![Repo](https://img.shields.io/badge/repo-GitHub-black?logo=github)](https://github.com/structural-explainability/se-contract-kit)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue?logo=python)](./pyproject.toml)
[![Python 3.15 Ready](https://github.com/structural-explainability/se-contract-kit/actions/workflows/python-315-ready.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-contract-kit/actions/workflows/python-315-ready.yml)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)

[![CI](https://github.com/structural-explainability/se-contract-kit/actions/workflows/ci-python-zensical.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-contract-kit/actions/workflows/ci-python-zensical.yml)
[![Docs-Deploy](https://github.com/structural-explainability/se-contract-kit/actions/workflows/deploy-zensical.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-contract-kit/actions/workflows/deploy-zensical.yml)
[![Release](https://github.com/structural-explainability/se-contract-kit/actions/workflows/release-pypi.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-contract-kit/actions/workflows/release-pypi.yml)
[![Links](https://github.com/structural-explainability/se-contract-kit/actions/workflows/links.yml/badge.svg?branch=main)](https://github.com/structural-explainability/se-contract-kit/actions/workflows/links.yml)
[![Dependabot](https://img.shields.io/badge/Dependabot-enabled-brightgreen.svg)](https://github.com/structural-explainability/se-contract-kit/security)

> Provides generic contract loading, resolution, and validation
> machinery for Structural Explainability contract repositories.

It is a Python package and command-line tool.

## Role

Owns reusable machinery for contract repositories.
It does not own Accountable Record, Judicial Record, Civic Record, or any
domain-specific contract content.

## Package

```shell
uv add se-contract-kit
```

## Command

```shell
uv run se-contract-kit check --strict
```

## Source layout

```text
base/          Dependency-free utilities for errors, file IO, JSON, and paths.
declarations/  Load repository manifest and contract declarations.
resolution/    Resolve dependencies, artifacts, authorities, lockfiles, and run context.
validation/    Run generic contract checks and produce validation results.
cli.py         Command-line entry point.
```

## Command Reference

<details>
<summary>Show command reference</summary>

### In a machine terminal

Open a machine terminal where you want the project:

```shell
git clone https://github.com/structural-explainability/se-contract-kit

cd se-contract-kit
code .
```

### In a VS Code terminal

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

# save progress
git add -A
git commit -m "update"
git push -u origin main
```

</details>

## Citation

[CITATION.cff](./CITATION.cff)

## License

[MIT](./LICENSE)

## Manifest

[MANIFEST.toml](./MANIFEST.toml)
