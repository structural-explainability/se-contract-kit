"""Path discovery and normalization."""

from pathlib import Path

from se_contract_kit.base.errors import ContractKitPathError

__all__ = [
    "normalize_path",
    "find_upward",
    "find_repo_root",
    "find_manifest_path",
    "find_contract_config_path",
    "repo_relative_path",
    "resolve_repo_path",
]

CONTRACT_CONFIG_FILENAMES = ("contract.toml",)
MANIFEST_FILENAMES = ("MANIFEST.toml", "SE_MANIFEST.toml")


def normalize_path(path: Path) -> Path:
    """Return an absolute resolved path."""
    return path.expanduser().resolve()


def find_upward(filename: str, start: Path | None = None) -> Path | None:
    """Find a file by walking upward from start or the current directory."""
    current = normalize_path(start or Path.cwd())

    if current.is_file():
        current = current.parent

    for candidate_dir in (current, *current.parents):
        candidate = candidate_dir / filename
        if candidate.is_file():
            return candidate

    return None


def find_repo_root(start: Path | None = None) -> Path:
    """Find the repository root.

    The root is identified by a pyproject.toml file or a .git directory.
    """
    current = normalize_path(start or Path.cwd())

    if current.is_file():
        current = current.parent

    for candidate_dir in (current, *current.parents):
        if (candidate_dir / "pyproject.toml").is_file():
            return candidate_dir
        if (candidate_dir / ".git").exists():
            return candidate_dir

    raise ContractKitPathError(f"Could not find repository root from: {current}")


def find_manifest_path(start: Path | None = None) -> Path:
    """Find a supported repository manifest file."""
    repo_root = find_repo_root(start)

    for filename in MANIFEST_FILENAMES:
        candidate = repo_root / filename
        if candidate.is_file():
            return candidate

    names = ", ".join(MANIFEST_FILENAMES)
    raise ContractKitPathError(
        f"No repository manifest found. Expected one of: {names}"
    )


def find_contract_config_path(start: Path | None = None) -> Path:
    """Find contract.toml in the repository root."""
    repo_root = find_repo_root(start)

    for filename in CONTRACT_CONFIG_FILENAMES:
        candidate = repo_root / filename
        if candidate.is_file():
            return candidate

    names = ", ".join(CONTRACT_CONFIG_FILENAMES)
    raise ContractKitPathError(f"No contract config found. Expected one of: {names}")


def repo_relative_path(path: Path, repo_root: Path) -> Path:
    """Return path relative to repo_root."""
    resolved_path = normalize_path(path)
    resolved_root = normalize_path(repo_root)

    try:
        return resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ContractKitPathError(
            f"Path is not inside repository root: {resolved_path}"
        ) from exc


def resolve_repo_path(repo_root: Path, relative_path: str | Path) -> Path:
    """Resolve a repo-relative path and ensure it stays inside the repo."""
    resolved_root = normalize_path(repo_root)
    candidate = normalize_path(resolved_root / relative_path)

    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ContractKitPathError(
            f"Path escapes repository root: {relative_path}"
        ) from exc

    return candidate
