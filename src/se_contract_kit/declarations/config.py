"""Combined repository declaration config."""

from dataclasses import dataclass
from pathlib import Path

from se_contract_kit.declarations.contracts import (
    ContractConfigDeclaration,
    load_contract_config_declaration,
)
from se_contract_kit.declarations.manifests import (
    ManifestDeclaration,
    load_manifest_declaration,
)

__all__ = [
    "RepoConfig",
    "load_repo_config",
]


@dataclass(frozen=True)
class RepoConfig:
    """Combined manifest and contract declarations for one repository."""

    repo_root: Path
    manifest: ManifestDeclaration
    contract_config: ContractConfigDeclaration | None


def load_repo_config(
    *,
    repo_root: Path,
    manifest_path: Path | None = None,
    contract_config_path: Path | None = None,
    require_contract_config: bool = False,
) -> RepoConfig:
    """Load repository declaration config."""
    manifest = load_manifest_declaration(manifest_path)

    contract_config: ContractConfigDeclaration | None = None
    if contract_config_path is not None:
        contract_config = load_contract_config_declaration(contract_config_path)
    elif require_contract_config:
        contract_config = load_contract_config_declaration()

    return RepoConfig(
        repo_root=repo_root,
        manifest=manifest,
        contract_config=contract_config,
    )
