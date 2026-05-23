"""Resolution orchestration.

The resolver turns declarations into a ResolutionContext.

It resolves local provided artifacts now. External dependency resolution is
represented explicitly but not fetched here yet.
"""

from dataclasses import dataclass
from pathlib import Path

from se_contract_kit.declarations.config import RepoConfig
from se_contract_kit.declarations.contracts import ContractArtifactDeclaration
from se_contract_kit.resolution.artifacts import (
    ArtifactResolutionSet,
    DeclaredArtifact,
    ResolvedArtifact,
    require_unique_artifact_ids,
)
from se_contract_kit.resolution.context import (
    ResolutionContext,
    build_resolution_context,
)
from se_contract_kit.resolution.dependencies import (
    DependencySet,
    build_dependency_set,
)

__all__ = [
    "ResolverOptions",
    "resolve_repo_config",
]


@dataclass(frozen=True)
class ResolverOptions:
    """Options for resolution."""

    include_optional_dependencies: bool = False


def resolve_repo_config(
    *,
    repo_root: Path,
    config: RepoConfig,
    options: ResolverOptions | None = None,
) -> ResolutionContext:
    """Resolve a loaded repository config into a run context."""
    active_options = options or ResolverOptions()

    dependencies = _resolve_dependencies(
        config=config,
        include_optional=active_options.include_optional_dependencies,
    )
    provided_artifacts = _resolve_provided_artifacts(
        repo_root=repo_root,
        repo_name=config.manifest.repo.name,
        config=config,
    )

    artifacts = ArtifactResolutionSet(
        provided=provided_artifacts,
        consumed=(),
    )

    return build_resolution_context(
        repo_root=repo_root,
        config=config,
        dependencies=dependencies,
        artifacts=artifacts,
    )


def _resolve_dependencies(
    *,
    config: RepoConfig,
    include_optional: bool,
) -> DependencySet:
    """Resolve declared dependency references into parsed dependency objects."""
    required = config.manifest.depends.required
    optional = config.manifest.depends.optional if include_optional else ()

    return build_dependency_set(
        required=required,
        optional=optional,
    )


def _resolve_provided_artifacts(
    *,
    repo_root: Path,
    repo_name: str,
    config: RepoConfig,
) -> tuple[ResolvedArtifact, ...]:
    """Resolve artifacts provided by the current repository."""
    if config.contract_config is None:
        return ()

    declared = tuple(
        _declared_artifact_from_contract_artifact(artifact)
        for artifact in config.contract_config.provides.artifacts
    )
    require_unique_artifact_ids(declared)

    return tuple(
        ResolvedArtifact(
            artifact_id=artifact.artifact_id,
            kind=artifact.kind,
            path=repo_root / artifact.path,
            source_repo=repo_name,
            authority_repo=repo_name,
            owner=artifact.owner,
            is_local=True,
        )
        for artifact in declared
    )


def _declared_artifact_from_contract_artifact(
    artifact: ContractArtifactDeclaration,
) -> DeclaredArtifact:
    """Convert a contract declaration artifact to a resolution artifact."""
    return DeclaredArtifact(
        artifact_id=artifact.artifact_id,
        kind=artifact.kind,
        path=artifact.path,
        owner=artifact.owner,
    )
