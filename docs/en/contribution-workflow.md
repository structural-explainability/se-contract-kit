# Contribution Workflow

## Standard workflow

```shell
uv sync --extra dev --extra docs --upgrade
uvx pre-commit run --all-files
```

## Source boundaries

The source tree follows this dependency direction:

```text
base -> declarations -> resolution -> validation -> cli
```

Earlier stages must not import later stages.

Resolution must not import validation.
