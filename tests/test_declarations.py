"""Tests for se_contract_kit.declarations."""

from pathlib import Path

import pytest

from se_contract_kit.declarations.config import load_repo_config
from se_contract_kit.declarations.contracts import (
    ContractConfigParser,
    load_contract_config_declaration,
)
from se_contract_kit.declarations.manifests import (
    ManifestDeclarationParser,
    load_manifest_declaration,
)


def _write_manifest(path: Path) -> None:
    path.write_text(
        """
schema = "se-manifest-schema"
schema_url = "https://example.com/manifest-schema.toml"

[repo]
name = "accountable-record"
org = "structural-explainability"
class = "contract"
kind = "accountable-record"
status = "active"
since = "2026"
summary = "Accountable Record contract."

[layer]
space = "application"
role = "language-neutral-contract"

[contract]
contract_version = "0.1.0"
contract_role = "authority"
contract_authority = "accountable-record"
exports_verified_contract = false

[depends]
required = ["structural-explainability/se-manifest-schema@v0.4.0"]
optional = []

[provides]
artifacts = ["accountable-record-contract"]
""",
        encoding="utf-8",
    )


def _write_contract_config(path: Path) -> None:
    path.write_text(
        """
[provides]
artifacts = [
  {id = "accountable-record-contract", kind = "contract", path = "data/contract.toml", owner = "accountable-record"},
  {id = "accountable-record-outcomes", kind = "outcomes", path = "data/conformance/outcomes.toml"},
]

[consumes]
contracts = []
""",
        encoding="utf-8",
    )


def test_manifest_parser_reads_contract_authority_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "MANIFEST.toml"
    _write_manifest(manifest_path)

    declaration = load_manifest_declaration(manifest_path)

    assert declaration.path == manifest_path
    assert declaration.schema == "se-manifest-schema"
    assert declaration.repo.name == "accountable-record"
    assert declaration.repo.repo_class == "contract"
    assert declaration.layer.role == "language-neutral-contract"
    assert declaration.depends.required == (
        "structural-explainability/se-manifest-schema@v0.4.0",
    )
    assert declaration.depends.optional == ()
    assert declaration.provides.artifacts == ("accountable-record-contract",)
    assert declaration.contract is not None
    assert declaration.contract.contract_role == "authority"
    assert declaration.contract.contract_authority == "accountable-record"
    assert declaration.contract.contract_version == "0.1.0"
    assert declaration.contract.exports_verified_contract is False
    assert declaration.contract.consumes_contract_from is None


def test_manifest_parser_reads_domain_contract_consume_field(tmp_path: Path) -> None:
    manifest_path = tmp_path / "MANIFEST.toml"
    _write_manifest(manifest_path)
    text = manifest_path.read_text(encoding="utf-8")
    text = text.replace(
        'contract_role = "authority"', 'contract_role = "domain-contract"'
    )
    text = text.replace(
        'exports_verified_contract = false',
        'exports_verified_contract = false\nconsumes_contract_from = "accountable-record"',
    )
    manifest_path.write_text(text, encoding="utf-8")

    declaration = load_manifest_declaration(manifest_path)

    assert declaration.contract is not None
    assert declaration.contract.contract_role == "domain-contract"
    assert declaration.contract.consumes_contract_from == "accountable-record"


def test_manifest_parser_allows_manifest_without_contract_section(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "MANIFEST.toml"
    _write_manifest(manifest_path)
    text = manifest_path.read_text(encoding="utf-8")
    start = text.index("[contract]")
    end = text.index("[depends]")
    manifest_path.write_text(text[:start] + text[end:], encoding="utf-8")

    declaration = load_manifest_declaration(manifest_path)

    assert declaration.contract is None


def test_manifest_parser_requires_top_level_schema(tmp_path: Path) -> None:
    manifest_path = tmp_path / "MANIFEST.toml"
    _write_manifest(manifest_path)
    text = manifest_path.read_text(encoding="utf-8").replace(
        'schema = "se-manifest-schema"\n',
        "",
    )
    manifest_path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="schema"):
        load_manifest_declaration(manifest_path)


def test_manifest_parser_requires_repo_table() -> None:
    parser = ManifestDeclarationParser(data={}, path=Path("MANIFEST.toml"))

    with pytest.raises(ValueError, match=r"schema: required nonempty string missing"):
        parser.parse()


def test_manifest_parser_requires_repo_class(tmp_path: Path) -> None:
    manifest_path = tmp_path / "MANIFEST.toml"
    _write_manifest(manifest_path)
    text = manifest_path.read_text(encoding="utf-8").replace(
        'class = "contract"\n',
        "",
    )
    manifest_path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match=r"\[repo\].class"):
        load_manifest_declaration(manifest_path)


def test_manifest_parser_rejects_non_table_contract_section() -> None:
    parser = ManifestDeclarationParser(
        data={
            "schema": "se-manifest-schema",
            "schema_url": "https://example.com",
            "repo": {
                "name": "repo",
                "org": "org",
                "class": "contract",
                "kind": "contract",
                "status": "active",
                "since": "2026",
                "summary": "summary",
            },
            "layer": {"space": "application", "role": "language-neutral-contract"},
            "depends": {"required": [], "optional": []},
            "provides": {"artifacts": []},
            "contract": "bad",
        },
        path=Path("MANIFEST.toml"),
    )

    with pytest.raises(ValueError, match=r"\[contract\]"):
        parser.parse()


def test_manifest_parser_rejects_non_string_consume_field(tmp_path: Path) -> None:
    manifest_path = tmp_path / "MANIFEST.toml"
    _write_manifest(manifest_path)
    text = manifest_path.read_text(encoding="utf-8").replace(
        "exports_verified_contract = false",
        "exports_verified_contract = false\nconsumes_contract_from = 123",
    )
    manifest_path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="consumes_contract_from"):
        load_manifest_declaration(manifest_path)


def test_manifest_parser_rejects_non_bool_exports_verified_contract(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "MANIFEST.toml"
    _write_manifest(manifest_path)
    text = manifest_path.read_text(encoding="utf-8").replace(
        "exports_verified_contract = false",
        'exports_verified_contract = "false"',
    )
    manifest_path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="exports_verified_contract"):
        load_manifest_declaration(manifest_path)


def test_manifest_parser_rejects_non_list_depends_required() -> None:
    parser = ManifestDeclarationParser(
        data={
            "schema": "se-manifest-schema",
            "schema_url": "https://example.com",
            "repo": {
                "name": "repo",
                "org": "org",
                "class": "contract",
                "kind": "contract",
                "status": "active",
                "since": "2026",
                "summary": "summary",
            },
            "layer": {"space": "application", "role": "language-neutral-contract"},
            "depends": {"required": "bad", "optional": []},
            "provides": {"artifacts": []},
        },
        path=Path("MANIFEST.toml"),
    )

    with pytest.raises(ValueError, match=r"\[depends\].required"):
        parser.parse()


def test_manifest_parser_rejects_non_string_list_item() -> None:
    parser = ManifestDeclarationParser(
        data={
            "schema": "se-manifest-schema",
            "schema_url": "https://example.com",
            "repo": {
                "name": "repo",
                "org": "org",
                "class": "contract",
                "kind": "contract",
                "status": "active",
                "since": "2026",
                "summary": "summary",
            },
            "layer": {"space": "application", "role": "language-neutral-contract"},
            "depends": {"required": [123], "optional": []},
            "provides": {"artifacts": []},
        },
        path=Path("MANIFEST.toml"),
    )

    with pytest.raises(ValueError, match="all values must be strings"):
        parser.parse()


def test_contract_config_parser_reads_provides_and_consumes(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.toml"
    _write_contract_config(contract_path)

    declaration = load_contract_config_declaration(contract_path)

    assert declaration.path == contract_path
    assert len(declaration.provides.artifacts) == 2
    assert declaration.provides.artifacts[0].artifact_id == (
        "accountable-record-contract"
    )
    assert declaration.provides.artifacts[0].kind == "contract"
    assert declaration.provides.artifacts[0].path == Path("data/contract.toml")
    assert declaration.provides.artifacts[0].owner == "accountable-record"
    assert declaration.provides.artifacts[1].owner is None
    assert declaration.consumes.contracts == ()


def test_contract_config_parser_reads_consumed_contracts(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.toml"
    contract_path.write_text(
        """
[provides]
artifacts = []

[consumes]
contracts = ["accountable-record"]
""",
        encoding="utf-8",
    )

    declaration = load_contract_config_declaration(contract_path)

    assert declaration.consumes.contracts == ("accountable-record",)


def test_contract_config_parser_allows_missing_tables() -> None:
    parser = ContractConfigParser(data={}, path=Path("contract.toml"))

    declaration = parser.parse()

    assert declaration.provides.artifacts == ()
    assert declaration.consumes.contracts == ()


def test_contract_config_parser_rejects_non_table_provides() -> None:
    parser = ContractConfigParser(
        data={"provides": "bad"},
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\[provides\]"):
        parser.parse()


def test_contract_config_parser_rejects_non_list_artifacts() -> None:
    parser = ContractConfigParser(
        data={"provides": {"artifacts": "bad"}},
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\[provides\].artifacts"):
        parser.parse()


def test_contract_config_parser_rejects_non_table_artifact() -> None:
    parser = ContractConfigParser(
        data={"provides": {"artifacts": ["bad"]}},
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\[provides\].artifacts\[0\]"):
        parser.parse()


def test_contract_config_parser_rejects_missing_artifact_id() -> None:
    parser = ContractConfigParser(
        data={"provides": {"artifacts": [{"kind": "contract", "path": "x.toml"}]}},
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\.id"):
        parser.parse()


def test_contract_config_parser_rejects_missing_artifact_kind() -> None:
    parser = ContractConfigParser(
        data={"provides": {"artifacts": [{"id": "artifact", "path": "x.toml"}]}},
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\.kind"):
        parser.parse()


def test_contract_config_parser_rejects_missing_artifact_path() -> None:
    parser = ContractConfigParser(
        data={"provides": {"artifacts": [{"id": "artifact", "kind": "contract"}]}},
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\.path"):
        parser.parse()


def test_contract_config_parser_rejects_non_string_owner() -> None:
    parser = ContractConfigParser(
        data={
            "provides": {
                "artifacts": [
                    {
                        "id": "artifact",
                        "kind": "contract",
                        "path": "x.toml",
                        "owner": 123,
                    }
                ]
            }
        },
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\.owner"):
        parser.parse()


def test_contract_config_parser_rejects_non_table_consumes() -> None:
    parser = ContractConfigParser(
        data={"consumes": "bad"},
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\[consumes\]"):
        parser.parse()


def test_contract_config_parser_rejects_non_list_consumed_contracts() -> None:
    parser = ContractConfigParser(
        data={"consumes": {"contracts": "bad"}},
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\[consumes\].contracts"):
        parser.parse()


def test_contract_config_parser_rejects_non_string_consumed_contract() -> None:
    parser = ContractConfigParser(
        data={"consumes": {"contracts": [123]}},
        path=Path("contract.toml"),
    )

    with pytest.raises(ValueError, match=r"\[consumes\].contracts"):
        parser.parse()


def test_load_repo_config_without_contract_config(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    manifest_path = repo_root / "MANIFEST.toml"
    _write_manifest(manifest_path)

    config = load_repo_config(
        repo_root=repo_root,
        manifest_path=manifest_path,
    )

    assert config.repo_root == repo_root
    assert config.manifest.repo.name == "accountable-record"
    assert config.contract_config is None


def test_load_repo_config_with_explicit_contract_config(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    manifest_path = repo_root / "MANIFEST.toml"
    contract_path = repo_root / "contract.toml"
    _write_manifest(manifest_path)
    _write_contract_config(contract_path)

    config = load_repo_config(
        repo_root=repo_root,
        manifest_path=manifest_path,
        contract_config_path=contract_path,
    )

    assert config.contract_config is not None
    assert len(config.contract_config.provides.artifacts) == 2


def test_load_repo_config_requires_contract_config_when_requested(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    manifest_path = repo_root / "MANIFEST.toml"
    contract_path = repo_root / "contract.toml"
    (repo_root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    _write_manifest(manifest_path)
    _write_contract_config(contract_path)

    config = load_repo_config(
        repo_root=repo_root,
        manifest_path=manifest_path,
        contract_config_path=contract_path,
        require_contract_config=True,
    )

    assert config.contract_config is not None
    assert config.contract_config.path == contract_path.resolve()
