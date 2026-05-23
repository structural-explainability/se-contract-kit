"""Resolved dependency and artifact lockfile support."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from se_contract_kit.base.io import read_json, write_json
from se_contract_kit.resolution.artifacts import ResolvedArtifact
from se_contract_kit.resolution.dependencies import DependencyReference

__all__ = [
    "LOCKFILE_SCHEMA",
    "ContractLockfile",
    "LockedArtifact",
    "LockedDependency",
    "artifact_to_locked",
    "build_lockfile",
    "dependency_to_locked",
    "lockfile_from_json",
    "lockfile_to_json",
    "read_lockfile",
    "write_lockfile",
]

LOCKFILE_SCHEMA = "se-contract-kit-lock-1"


@dataclass(frozen=True)
class LockedDependency:
    """A dependency recorded in the lockfile."""

    name: str
    version: str
    owner: str | None = None

    @property
    def qualified_name(self) -> str:
        """Return owner/name when an owner is present; otherwise name."""
        if self.owner is None:
            return self.name
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True)
class LockedArtifact:
    """An artifact recorded in the lockfile."""

    artifact_id: str
    kind: str
    path: str
    source_repo: str
    authority_repo: str
    is_local: bool


@dataclass(frozen=True)
class ContractLockfile:
    """Resolved contract dependency and artifact state."""

    schema: str
    dependencies: tuple[LockedDependency, ...]
    artifacts: tuple[LockedArtifact, ...]


def dependency_to_locked(dependency: DependencyReference) -> LockedDependency:
    """Convert a parsed dependency reference to a lockfile dependency."""
    return LockedDependency(
        name=dependency.name,
        owner=dependency.owner,
        version=dependency.version,
    )


def artifact_to_locked(artifact: ResolvedArtifact) -> LockedArtifact:
    """Convert a resolved artifact to a lockfile artifact."""
    return LockedArtifact(
        artifact_id=artifact.artifact_id,
        kind=artifact.kind,
        path=artifact.path.as_posix(),
        source_repo=artifact.source_repo,
        authority_repo=artifact.authority_repo,
        is_local=artifact.is_local,
    )


def build_lockfile(
    *,
    dependencies: tuple[DependencyReference, ...],
    artifacts: tuple[ResolvedArtifact, ...],
) -> ContractLockfile:
    """Build a contract lockfile from resolved dependency state."""
    return ContractLockfile(
        schema=LOCKFILE_SCHEMA,
        dependencies=tuple(dependency_to_locked(item) for item in dependencies),
        artifacts=tuple(artifact_to_locked(item) for item in artifacts),
    )


def lockfile_to_json(lockfile: ContractLockfile) -> dict[str, Any]:
    """Convert a lockfile to JSON-compatible data."""
    return {
        "schema": lockfile.schema,
        "dependencies": [
            {
                "owner": dependency.owner,
                "name": dependency.name,
                "version": dependency.version,
            }
            for dependency in lockfile.dependencies
        ],
        "artifacts": [
            {
                "artifact_id": artifact.artifact_id,
                "kind": artifact.kind,
                "path": artifact.path,
                "source_repo": artifact.source_repo,
                "authority_repo": artifact.authority_repo,
                "is_local": artifact.is_local,
            }
            for artifact in lockfile.artifacts
        ],
    }


def lockfile_from_json(data: dict[str, Any]) -> ContractLockfile:
    """Parse a lockfile from JSON-compatible data."""
    schema = data.get("schema")
    if schema != LOCKFILE_SCHEMA:
        raise ValueError(f"unsupported lockfile schema: {schema!r}")

    dependencies_raw = data.get("dependencies", [])
    if not isinstance(dependencies_raw, list):
        raise ValueError("lockfile dependencies must be a list")

    artifacts_raw = data.get("artifacts", [])
    if not isinstance(artifacts_raw, list):
        raise ValueError("lockfile artifacts must be a list")

    dependencies = tuple(
        _locked_dependency_from_json(cast(dict[str, Any], item), index)
        for index, item in enumerate(cast(list[Any], dependencies_raw))
    )
    artifacts = tuple(
        _locked_artifact_from_json(cast(dict[str, Any], item), index)
        for index, item in enumerate(cast(list[Any], artifacts_raw))
    )

    return ContractLockfile(
        schema=schema,
        dependencies=dependencies,
        artifacts=artifacts,
    )


def read_lockfile(path: Path) -> ContractLockfile:
    """Read a contract lockfile."""
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError("lockfile root must be an object")
    return lockfile_from_json(cast(dict[str, Any], data))


def write_lockfile(path: Path, lockfile: ContractLockfile) -> None:
    """Write a contract lockfile."""
    write_json(path, lockfile_to_json(lockfile))


def _locked_dependency_from_json(
    item: dict[str, Any],
    index: int,
) -> LockedDependency:
    """Parse one locked dependency."""
    owner = item.get("owner")
    name = item.get("name")
    version = item.get("version")

    if owner is not None and not isinstance(owner, str):
        raise ValueError(f"dependencies[{index}].owner must be a string or null")
    if not isinstance(name, str) or not name:
        raise ValueError(f"dependencies[{index}].name must be a nonempty string")
    if not isinstance(version, str) or not version:
        raise ValueError(f"dependencies[{index}].version must be a nonempty string")

    return LockedDependency(
        owner=owner,
        name=name,
        version=version,
    )


def _locked_artifact_from_json(
    item: dict[str, Any],
    index: int,
) -> LockedArtifact:
    """Parse one locked artifact."""
    artifact_id = item.get("artifact_id")
    kind = item.get("kind")
    path = item.get("path")
    source_repo = item.get("source_repo")
    authority_repo = item.get("authority_repo")
    is_local = item.get("is_local")

    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError(f"artifacts[{index}].artifact_id must be a nonempty string")
    if not isinstance(kind, str) or not kind:
        raise ValueError(f"artifacts[{index}].kind must be a nonempty string")
    if not isinstance(path, str) or not path:
        raise ValueError(f"artifacts[{index}].path must be a nonempty string")
    if not isinstance(source_repo, str) or not source_repo:
        raise ValueError(f"artifacts[{index}].source_repo must be a nonempty string")
    if not isinstance(authority_repo, str) or not authority_repo:
        raise ValueError(f"artifacts[{index}].authority_repo must be a nonempty string")
    if not isinstance(is_local, bool):
        raise ValueError(f"artifacts[{index}].is_local must be a boolean")

    return LockedArtifact(
        artifact_id=artifact_id,
        kind=kind,
        path=path,
        source_repo=source_repo,
        authority_repo=authority_repo,
        is_local=is_local,
    )
