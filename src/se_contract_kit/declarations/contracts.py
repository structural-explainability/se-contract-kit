"""Contract configuration declarations."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from se_contract_kit.base.io import read_toml
from se_contract_kit.base.paths import find_contract_config_path

__all__ = [
    "ContractArtifactDeclaration",
    "ContractConfigDeclaration",
    "ContractConfigParser",
    "ContractConsumesDeclaration",
    "ContractProvidesDeclaration",
    "load_contract_config_declaration",
]


@dataclass(frozen=True)
class ContractArtifactDeclaration:
    """A contract artifact declared in contract.toml."""

    artifact_id: str
    kind: str
    path: Path
    owner: str | None = None


@dataclass(frozen=True)
class ContractProvidesDeclaration:
    """Artifacts provided by this contract repo."""

    artifacts: tuple[ContractArtifactDeclaration, ...]


@dataclass(frozen=True)
class ContractConsumesDeclaration:
    """Upstream contracts consumed by this contract repo."""

    contracts: tuple[str, ...]


@dataclass(frozen=True)
class ContractConfigDeclaration:
    """Typed contract.toml declaration."""

    path: Path
    provides: ContractProvidesDeclaration
    consumes: ContractConsumesDeclaration


def load_contract_config_declaration(
    path: Path | None = None,
) -> ContractConfigDeclaration:
    """Load contract.toml."""
    contract_path = path if path is not None else find_contract_config_path()
    data = read_toml(contract_path)
    return ContractConfigParser(data=data, path=contract_path).parse()


class ContractConfigParser:
    """Parser for contract.toml."""

    def __init__(self, *, data: dict[str, Any], path: Path) -> None:
        """Initialize the parser with raw data and the source path."""
        self._data = data
        self._path = path

    def parse(self) -> ContractConfigDeclaration:
        """Parse contract.toml."""
        return ContractConfigDeclaration(
            path=self._path,
            provides=self._parse_provides(),
            consumes=self._parse_consumes(),
        )

    def _parse_provides(self) -> ContractProvidesDeclaration:
        section_raw = self._data.get("provides", {})
        if not isinstance(section_raw, dict):
            raise ValueError("[provides] must be a table")

        section = cast(dict[str, Any], section_raw)
        artifacts_raw = section.get("artifacts", [])
        if not isinstance(artifacts_raw, list):
            raise ValueError("[provides].artifacts must be a list")

        artifacts: list[ContractArtifactDeclaration] = []
        for index, item in enumerate(cast(list[Any], artifacts_raw)):
            if not isinstance(item, dict):
                raise ValueError(f"[provides].artifacts[{index}] must be a table")
            artifacts.append(self._parse_artifact(cast(dict[str, Any], item), index))

        return ContractProvidesDeclaration(artifacts=tuple(artifacts))

    def _parse_consumes(self) -> ContractConsumesDeclaration:
        section_raw = self._data.get("consumes", {})
        if not isinstance(section_raw, dict):
            raise ValueError("[consumes] must be a table")

        section = cast(dict[str, Any], section_raw)
        contracts_raw = section.get("contracts", [])
        if not isinstance(contracts_raw, list):
            raise ValueError("[consumes].contracts must be a list")

        contracts: list[str] = []
        for item in cast(list[Any], contracts_raw):
            if not isinstance(item, str) or not item:
                raise ValueError("[consumes].contracts values must be strings")
            contracts.append(item)

        return ContractConsumesDeclaration(contracts=tuple(contracts))

    def _parse_artifact(
        self, item: dict[str, Any], index: int
    ) -> ContractArtifactDeclaration:
        artifact_id = item.get("id")
        kind = item.get("kind")
        path = item.get("path")
        owner = item.get("owner")

        if not isinstance(artifact_id, str) or not artifact_id:
            raise ValueError(f"[provides].artifacts[{index}].id required")
        if not isinstance(kind, str) or not kind:
            raise ValueError(f"[provides].artifacts[{index}].kind required")
        if not isinstance(path, str) or not path:
            raise ValueError(f"[provides].artifacts[{index}].path required")
        if owner is not None and not isinstance(owner, str):
            raise ValueError(f"[provides].artifacts[{index}].owner must be a string")

        return ContractArtifactDeclaration(
            artifact_id=artifact_id,
            kind=kind,
            path=Path(path),
            owner=owner,
        )
