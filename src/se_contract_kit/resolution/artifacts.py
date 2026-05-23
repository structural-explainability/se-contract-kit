"""Declared and resolved contract artifacts."""

from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "ArtifactResolutionSet",
    "DeclaredArtifact",
    "ResolvedArtifact",
    "artifact_ids",
    "find_declared_artifact",
    "find_resolved_artifact",
    "require_unique_artifact_ids",
]


@dataclass(frozen=True)
class DeclaredArtifact:
    """An artifact declared by a contract repository."""

    artifact_id: str
    kind: str
    path: Path
    owner: str | None = None


@dataclass(frozen=True)
class ResolvedArtifact:
    """A declared artifact resolved to a concrete filesystem path."""

    artifact_id: str
    kind: str
    path: Path
    source_repo: str
    authority_repo: str
    owner: str | None = None
    is_local: bool = False


@dataclass(frozen=True)
class ArtifactResolutionSet:
    """Resolved provided and consumed artifacts."""

    provided: tuple[ResolvedArtifact, ...]
    consumed: tuple[ResolvedArtifact, ...]


def artifact_ids(artifacts: tuple[DeclaredArtifact, ...]) -> tuple[str, ...]:
    """Return artifact IDs in declaration order."""
    return tuple(artifact.artifact_id for artifact in artifacts)


def find_declared_artifact(
    artifacts: tuple[DeclaredArtifact, ...],
    artifact_id: str,
) -> DeclaredArtifact | None:
    """Find a declared artifact by ID."""
    for artifact in artifacts:
        if artifact.artifact_id == artifact_id:
            return artifact
    return None


def find_resolved_artifact(
    artifacts: tuple[ResolvedArtifact, ...],
    artifact_id: str,
) -> ResolvedArtifact | None:
    """Find a resolved artifact by ID."""
    for artifact in artifacts:
        if artifact.artifact_id == artifact_id:
            return artifact
    return None


def require_unique_artifact_ids(artifacts: tuple[DeclaredArtifact, ...]) -> None:
    """Require declared artifact IDs to be unique."""
    seen: set[str] = set()
    duplicates: list[str] = []

    for artifact in artifacts:
        if artifact.artifact_id in seen:
            duplicates.append(artifact.artifact_id)
        seen.add(artifact.artifact_id)

    if duplicates:
        duplicate_list = ", ".join(sorted(set(duplicates)))
        raise ValueError(f"duplicate artifact IDs declared: {duplicate_list}")
