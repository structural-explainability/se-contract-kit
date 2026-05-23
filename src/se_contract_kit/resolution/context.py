"""Resolved contract run context.

A context is the complete resolved state needed by validation.
It is built after declarations are loaded and dependencies/artifacts are resolved.
"""

from dataclasses import dataclass
from pathlib import Path

from se_contract_kit.declarations.config import RepoConfig
from se_contract_kit.resolution.artifacts import ArtifactResolutionSet, ResolvedArtifact
from se_contract_kit.resolution.dependencies import DependencySet

__all__ = [
    "ResolutionContext",
    "build_resolution_context",
]


@dataclass(frozen=True)
class ResolutionContext:
    """Resolved state for one contract-kit run."""

    repo_root: Path
    config: RepoConfig
    dependencies: DependencySet
    artifacts: ArtifactResolutionSet

    @property
    def repo_name(self) -> str:
        """Return the current repository name."""
        return self.config.manifest.repo.name

    @property
    def provided_artifacts(self) -> tuple[ResolvedArtifact, ...]:
        """Return artifacts resolved from the current repository."""
        return self.artifacts.provided

    @property
    def consumed_artifacts(self) -> tuple[ResolvedArtifact, ...]:
        """Return artifacts resolved from consumed authorities."""
        return self.artifacts.consumed

    @property
    def all_artifacts(self) -> tuple[ResolvedArtifact, ...]:
        """Return all resolved artifacts."""
        return (*self.artifacts.provided, *self.artifacts.consumed)


def build_resolution_context(
    *,
    repo_root: Path,
    config: RepoConfig,
    dependencies: DependencySet,
    artifacts: ArtifactResolutionSet,
) -> ResolutionContext:
    """Build the resolved run context."""
    return ResolutionContext(
        repo_root=repo_root,
        config=config,
        dependencies=dependencies,
        artifacts=artifacts,
    )
