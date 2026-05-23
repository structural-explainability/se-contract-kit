#Requires -Version 7.0

<#
Run the release sequence.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Setup..."
uv self update
uv python pin 3.14
uv sync --extra dev --extra docs --upgrade
uvx pre-commit install
git add -A
uvx pre-commit run --all-files
git add -A
uvx pre-commit run --all-files

Write-Host "Validating manifest..."
uv run se-manifest validate-manifest --path MANIFEST.toml --strict

Write-Host "Running checks..."
uv run se-contract-kit check --strict

Write-Host "Running tests..."
uv run python -m pytest

Write-Host "Running type checks..."
uv run python -m pyright

Write-Host "Building documentation..."
uv run python -m zensical build

Write-Host "Running pre-commit checks..."
uvx pre-commit run --all-files

Write-Host "Release validation completed successfully."
