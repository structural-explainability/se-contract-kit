"""Repository manifest declarations."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from se_contract_kit.base.io import read_toml
from se_contract_kit.base.paths import find_manifest_path

__all__ = [
    "ContractManifestDeclaration",
    "DependencyDeclaration",
    "LayerDeclaration",
    "ManifestDeclaration",
    "ManifestDeclarationParser",
    "ProvidesDeclaration",
    "RepoDeclaration",
    "load_manifest_declaration",
]


@dataclass(frozen=True)
class RepoDeclaration:
    """Repository identity declared in MANIFEST.toml or SE_MANIFEST.toml."""

    name: str
    org: str
    repo_class: str
    kind: str
    status: str
    since: str
    summary: str


@dataclass(frozen=True)
class LayerDeclaration:
    """Layer placement declared in the repository manifest."""

    space: str
    role: str


@dataclass(frozen=True)
class ContractManifestDeclaration:
    """Contract metadata declared in the repository manifest."""

    contract_version: str | None = None
    contract_role: str | None = None
    contract_authority: str | None = None
    exports_verified_contract: bool | None = None
    consumes_contract_from: str | None = None


@dataclass(frozen=True)
class DependencyDeclaration:
    """Repository dependencies declared in the repository manifest."""

    required: tuple[str, ...]
    optional: tuple[str, ...]


@dataclass(frozen=True)
class ProvidesDeclaration:
    """Logical artifacts declared as provided by the repository."""

    artifacts: tuple[str, ...]


@dataclass(frozen=True)
class ManifestDeclaration:
    """Typed repository manifest declaration."""

    path: Path
    schema: str
    schema_url: str
    repo: RepoDeclaration
    layer: LayerDeclaration
    depends: DependencyDeclaration
    provides: ProvidesDeclaration
    contract: ContractManifestDeclaration | None


def load_manifest_declaration(path: Path | None = None) -> ManifestDeclaration:
    """Load a repository manifest declaration."""
    manifest_path = path if path is not None else find_manifest_path()
    data = read_toml(manifest_path)
    return ManifestDeclarationParser(data=data, path=manifest_path).parse()


class ManifestDeclarationParser:
    """Parser for repository manifest declarations."""

    def __init__(self, *, data: dict[str, Any], path: Path) -> None:
        """Initialize the parser with raw data and the source path."""
        self._data = data
        self._path = path

    def parse(self) -> ManifestDeclaration:
        """Parse the manifest declaration."""
        return ManifestDeclaration(
            path=self._path,
            schema=self._required_string_top_level("schema"),
            schema_url=self._required_string_top_level("schema_url"),
            repo=self._parse_repo(),
            layer=self._parse_layer(),
            depends=self._parse_depends(),
            provides=self._parse_provides(),
            contract=self._parse_contract(),
        )

    def _parse_repo(self) -> RepoDeclaration:
        section = self._required_table("repo")
        return RepoDeclaration(
            name=self._required_string(section, "name", "repo"),
            org=self._required_string(section, "org", "repo"),
            repo_class=self._required_string(section, "class", "repo"),
            kind=self._required_string(section, "kind", "repo"),
            status=self._required_string(section, "status", "repo"),
            since=self._required_string(section, "since", "repo"),
            summary=self._required_string(section, "summary", "repo"),
        )

    def _parse_layer(self) -> LayerDeclaration:
        section = self._required_table("layer")
        return LayerDeclaration(
            space=self._required_string(section, "space", "layer"),
            role=self._required_string(section, "role", "layer"),
        )

    def _parse_depends(self) -> DependencyDeclaration:
        section = self._required_table("depends")
        return DependencyDeclaration(
            required=self._string_tuple(section, "required", "depends"),
            optional=self._string_tuple(section, "optional", "depends"),
        )

    def _parse_provides(self) -> ProvidesDeclaration:
        section = self._required_table("provides")
        return ProvidesDeclaration(
            artifacts=self._string_tuple(section, "artifacts", "provides"),
        )

    def _parse_contract(self) -> ContractManifestDeclaration | None:
        section_raw = self._data.get("contract")
        if section_raw is None:
            return None
        if not isinstance(section_raw, dict):
            raise ValueError("[contract] must be a table")

        section = cast(dict[str, Any], section_raw)
        return ContractManifestDeclaration(
            contract_version=self._optional_string(
                section, "contract_version", "contract"
            ),
            contract_role=self._optional_string(section, "contract_role", "contract"),
            contract_authority=self._optional_string(
                section, "contract_authority", "contract"
            ),
            exports_verified_contract=self._optional_bool(
                section, "exports_verified_contract", "contract"
            ),
            consumes_contract_from=self._optional_string(
                section, "consumes_contract_from", "contract"
            ),
        )

    def _required_string_top_level(self, key: str) -> str:
        value = self._data.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"{key}: required nonempty string missing")
        return value

    def _required_table(self, section_name: str) -> dict[str, Any]:
        value = self._data.get(section_name)
        if not isinstance(value, dict):
            raise ValueError(f"[{section_name}]: required table missing")
        return cast(dict[str, Any], value)

    def _required_string(
        self, section: dict[str, Any], field_name: str, section_name: str
    ) -> str:
        value = section.get(field_name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"[{section_name}].{field_name}: required string missing")
        return value

    def _required_bool(
        self, section: dict[str, Any], field_name: str, section_name: str
    ) -> bool:
        value = section.get(field_name)
        if not isinstance(value, bool):
            raise ValueError(f"[{section_name}].{field_name}: required boolean missing")
        return value

    def _optional_string(
        self, section: dict[str, Any], field_name: str, section_name: str
    ) -> str | None:
        value = section.get(field_name)
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            raise ValueError(
                f"[{section_name}].{field_name}: must be a nonempty string if present"
            )
        return value

    def _optional_bool(
        self, section: dict[str, Any], field_name: str, section_name: str
    ) -> bool | None:
        value = section.get(field_name)
        if value is None:
            return None
        if not isinstance(value, bool):
            raise ValueError(
                f"[{section_name}].{field_name}: must be a boolean if present"
            )
        return value

    def _string_tuple(
        self, section: dict[str, Any], field_name: str, section_name: str
    ) -> tuple[str, ...]:
        value = section.get(field_name)
        if not isinstance(value, list):
            raise ValueError(f"[{section_name}].{field_name}: required list missing")

        items: list[str] = []
        for item in cast(list[Any], value):
            if not isinstance(item, str) or not item:
                raise ValueError(
                    f"[{section_name}].{field_name}: all values must be strings"
                )
            items.append(item)

        return tuple(items)
