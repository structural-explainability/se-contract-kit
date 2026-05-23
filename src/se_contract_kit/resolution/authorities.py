"""Authority resolution.

Resolution authority decides where an artifact should be read from.

This module resolves authority location only. It does not check whether a repo
violated an authority rule. Authority-rule checks live in validation.
"""

from dataclasses import dataclass
from pathlib import Path

from se_contract_kit.resolution.artifacts import DeclaredArtifact, ResolvedArtifact

__all__ = [
    "AuthorityResolution",
    "AuthoritySource",
    "choose_authority_source",
    "resolve_external_authority_artifact",
    "resolve_local_authority_artifact",
]


@dataclass(frozen=True)
class AuthoritySource:
    """A repository that may provide authoritative artifacts."""

    repo_name: str
    repo_root: Path
    is_local: bool


@dataclass(frozen=True)
class AuthorityResolution:
    """A declared artifact resolved through an authority source."""

    artifact: ResolvedArtifact
    authority: AuthoritySource


def resolve_local_authority_artifact(
    *,
    artifact: DeclaredArtifact,
    repo_name: str,
    repo_root: Path,
) -> AuthorityResolution:
    """Resolve an artifact provided by the current repository."""
    authority = AuthoritySource(
        repo_name=repo_name,
        repo_root=repo_root,
        is_local=True,
    )

    resolved = ResolvedArtifact(
        artifact_id=artifact.artifact_id,
        kind=artifact.kind,
        path=repo_root / artifact.path,
        source_repo=repo_name,
        authority_repo=repo_name,
        owner=artifact.owner,
        is_local=True,
    )

    return AuthorityResolution(
        artifact=resolved,
        authority=authority,
    )


def resolve_external_authority_artifact(
    *,
    artifact: DeclaredArtifact,
    source_repo: str,
    authority_repo: str,
    authority_root: Path,
) -> AuthorityResolution:
    """Resolve an artifact provided by an external authority repository."""
    authority = AuthoritySource(
        repo_name=authority_repo,
        repo_root=authority_root,
        is_local=False,
    )

    resolved = ResolvedArtifact(
        artifact_id=artifact.artifact_id,
        kind=artifact.kind,
        path=authority_root / artifact.path,
        source_repo=source_repo,
        authority_repo=authority_repo,
        owner=artifact.owner,
        is_local=False,
    )

    return AuthorityResolution(
        artifact=resolved,
        authority=authority,
    )


def choose_authority_source(
    *,
    artifact_id: str,
    local_provided_artifact_ids: tuple[str, ...],
    local_repo_name: str,
    local_repo_root: Path,
    external_authority_repo_name: str,
    external_authority_repo_root: Path,
) -> AuthoritySource:
    """Choose local authority when the current repo provides the artifact.

    If the current repo provides the artifact, resolve it locally. Otherwise,
    resolve it from the pinned external authority.
    """
    if artifact_id in local_provided_artifact_ids:
        return AuthoritySource(
            repo_name=local_repo_name,
            repo_root=local_repo_root,
            is_local=True,
        )

    return AuthoritySource(
        repo_name=external_authority_repo_name,
        repo_root=external_authority_repo_root,
        is_local=False,
    )
