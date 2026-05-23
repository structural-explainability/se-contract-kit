# Agents

This repository owns generic contract loading, resolution, and validation
machinery for Structural Explainability contract repositories.

It does not own domain-specific contract content.

Respect the stage boundaries:

```text
base -> declarations -> resolution -> validation -> cli
```

Resolution must not import from validation.
Resolution resolves contract state; validation checks contract state.

## Required commands

Use `uv` for all Python project commands.

Install and update dependencies:

```shell
uv sync --extra dev --extra docs --upgrade
```

Run the standard checks:

```shell
uv run se-manifest validate-manifest --path MANIFEST.toml --strict
uv run se-contract-kit check --strict
uv run python -m pyright
uv run python -m pytest
uv run python -m zensical build
```

Run pre-commit before committing:

```shell
uvx pre-commit run --all-files
```

Check version consistency before release:

```shell
uv run se-manifest check-version
uv run se-manifest check-version --require-tag
```

Do not use alternate Python environment managers or direct `pip` workflows for this repository.

## Annotations

This repository uses the Structural Explainability annotation convention for
rationale-bearing comments in code, configuration, and generated-source
templates.

Common annotation prefixes include:

- `WHY:` rationale for a decision or structure
- `OBS:` observation about current behavior or known limitation
- `REQ:` requirement that should not be weakened casually
- `ALT:` alternative considered
- `CUSTOM:` intentional local customization

Do not remove rationale-bearing annotations unless the underlying decision,
requirement, or alternative is also being updated.

Reference:
<https://github.com/structural-explainability/.github/blob/main/ANNOTATIONS.md>
