# Command Reference

## Manifest validation

Manifest validation is provided by `se-manifest-schema`.

```shell
uv run se-manifest validate-manifest --path MANIFEST.toml --strict
```

## Contract checks

Contract checks are provided by `se-contract-kit`.

```shell
uv run se-contract-kit check --strict
```

## Repository checks

Run the repository's configured pre-commit checks:

```shell
uvx pre-commit run --all-files
```
