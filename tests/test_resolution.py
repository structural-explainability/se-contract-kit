"""Tests for se_contract_kit.resolution."""

from pathlib import Path

import pytest

from se_contract_kit.declarations.config import RepoConfig
from se_contract_kit.declarations.contracts import (
    ContractArtifactDeclaration,
    ContractConfigDeclaration,
    ContractConsumesDeclaration,
    ContractProvidesDeclaration,
)
from se_contract_kit.declarations.manifests import (
    ContractManifestDeclaration,
    DependencyDeclaration,
    LayerDeclaration,
    ManifestDeclaration,
    ProvidesDeclaration,
    RepoDeclaration,
)
from se_contract_kit.resolution.artifacts import (
    DeclaredArtifact,
    ResolvedArtifact,
    artifact_ids,
    find_declared_artifact,
    find_resolved_artifact,
    require_unique_artifact_ids,
)
from se_contract_kit.resolution.authorities import (
    choose_authority_source,
    resolve_external_authority_artifact,
    resolve_local_authority_artifact,
)
from se_contract_kit.resolution.dependencies import (
    build_dependency_set,
    parse_dependency_reference,
    parse_dependency_references,
)
from se_contract_kit.resolution.lockfile import (
    LOCKFILE_SCHEMA,
    ContractLockfile,
    LockedArtifact,
    LockedDependency,
    artifact_to_locked,
    build_lockfile,
    dependency_to_locked,
    lockfile_from_json,
    lockfile_to_json,
    read_lockfile,
    write_lockfile,
)
from se_contract_kit.resolution.resolver import ResolverOptions, resolve_repo_config


def _manifest_declaration() -> ManifestDeclaration:
    return ManifestDeclaration(
        path=Path("MANIFEST.toml"),
        schema="se-manifest-schema",
        schema_url="https://example.com/manifest-schema.toml",
        repo=RepoDeclaration(
            name="accountable-record",
            org="structural-explainability",
            repo_class="contract",
            kind="accountable-record",
            status="active",
            since="2026",
            summary="Accountable Record contract.",
        ),
        layer=LayerDeclaration(
            space="application",
            role="language-neutral-contract",
        ),
        depends=DependencyDeclaration(
            required=("structural-explainability/se-manifest-schema@v0.4.0",),
            optional=("structural-explainability/se-formal-contract@v0.1.0",),
        ),
        provides=ProvidesDeclaration(
            artifacts=("accountable-record-contract",),
        ),
        contract=ContractManifestDeclaration(
            contract_version="0.1.0",
            contract_role="authority",
            contract_authority="accountable-record",
            exports_verified_contract=False,
        ),
    )


def _contract_config() -> ContractConfigDeclaration:
    return ContractConfigDeclaration(
        path=Path("contract.toml"),
        provides=ContractProvidesDeclaration(
            artifacts=(
                ContractArtifactDeclaration(
                    artifact_id="accountable-record-contract",
                    kind="contract",
                    path=Path("data/contract.toml"),
                    owner="accountable-record",
                ),
            ),
        ),
        consumes=ContractConsumesDeclaration(contracts=()),
    )


def _repo_config(repo_root: Path) -> RepoConfig:
    return RepoConfig(
        repo_root=repo_root,
        manifest=_manifest_declaration(),
        contract_config=_contract_config(),
    )


def test_parse_dependency_reference_with_owner() -> None:
    reference = parse_dependency_reference(
        "structural-explainability/accountable-record@v0.1.0"
    )

    assert reference.raw == "structural-explainability/accountable-record@v0.1.0"
    assert reference.owner == "structural-explainability"
    assert reference.name == "accountable-record"
    assert reference.version == "v0.1.0"
    assert reference.qualified_name == "structural-explainability/accountable-record"


def test_parse_dependency_reference_without_owner() -> None:
    reference = parse_dependency_reference("accountable-record@v0.1.0")

    assert reference.owner is None
    assert reference.name == "accountable-record"
    assert reference.version == "v0.1.0"
    assert reference.qualified_name == "accountable-record"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "accountable-record",
        "accountable-record@",
        "@v0.1.0",
        "/accountable-record@v0.1.0",
        "a/b/c@v0.1.0",
        "accountable-record@v0.1.0@extra",
    ],
)
def test_parse_dependency_reference_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_dependency_reference(value)


def test_parse_dependency_references_preserves_order() -> None:
    references = parse_dependency_references(
        (
            "a@v1.0.0",
            "org/b@v2.0.0",
        )
    )

    assert tuple(reference.qualified_name for reference in references) == (
        "a",
        "org/b",
    )


def test_build_dependency_set_excludes_optional_by_default_shape() -> None:
    dependency_set = build_dependency_set(
        required=("a@v1.0.0",),
        optional=("b@v2.0.0",),
    )

    assert tuple(item.qualified_name for item in dependency_set.required) == ("a",)
    assert tuple(item.qualified_name for item in dependency_set.optional) == ("b",)


def test_artifact_ids_preserves_order() -> None:
    artifacts = (
        DeclaredArtifact("a", "kind", Path("a.toml")),
        DeclaredArtifact("b", "kind", Path("b.toml")),
    )

    assert artifact_ids(artifacts) == ("a", "b")


def test_find_declared_artifact_returns_match_or_none() -> None:
    artifacts = (
        DeclaredArtifact("a", "kind", Path("a.toml")),
        DeclaredArtifact("b", "kind", Path("b.toml")),
    )

    assert find_declared_artifact(artifacts, "b") == artifacts[1]
    assert find_declared_artifact(artifacts, "missing") is None


def test_find_resolved_artifact_returns_match_or_none() -> None:
    artifacts = (
        ResolvedArtifact(
            artifact_id="a",
            kind="kind",
            path=Path("a.toml"),
            source_repo="repo",
            authority_repo="repo",
            is_local=True,
        ),
    )

    assert find_resolved_artifact(artifacts, "a") == artifacts[0]
    assert find_resolved_artifact(artifacts, "missing") is None


def test_require_unique_artifact_ids_accepts_unique_ids() -> None:
    require_unique_artifact_ids(
        (
            DeclaredArtifact("a", "kind", Path("a.toml")),
            DeclaredArtifact("b", "kind", Path("b.toml")),
        )
    )


def test_require_unique_artifact_ids_rejects_duplicates() -> None:
    with pytest.raises(ValueError, match="duplicate artifact IDs"):
        require_unique_artifact_ids(
            (
                DeclaredArtifact("a", "kind", Path("a.toml")),
                DeclaredArtifact("a", "kind", Path("b.toml")),
            )
        )


def test_resolve_local_authority_artifact(tmp_path: Path) -> None:
    artifact = DeclaredArtifact(
        artifact_id="contract",
        kind="contract",
        path=Path("data/contract.toml"),
        owner="accountable-record",
    )

    resolution = resolve_local_authority_artifact(
        artifact=artifact,
        repo_name="accountable-record",
        repo_root=tmp_path,
    )

    assert resolution.authority.repo_name == "accountable-record"
    assert resolution.authority.repo_root == tmp_path
    assert resolution.authority.is_local is True
    assert resolution.artifact.path == tmp_path / "data" / "contract.toml"
    assert resolution.artifact.source_repo == "accountable-record"
    assert resolution.artifact.authority_repo == "accountable-record"
    assert resolution.artifact.is_local is True


def test_resolve_external_authority_artifact(tmp_path: Path) -> None:
    artifact = DeclaredArtifact(
        artifact_id="outcomes",
        kind="outcomes",
        path=Path("data/outcomes.toml"),
    )

    resolution = resolve_external_authority_artifact(
        artifact=artifact,
        source_repo="judicial-record",
        authority_repo="accountable-record",
        authority_root=tmp_path,
    )

    assert resolution.authority.repo_name == "accountable-record"
    assert resolution.authority.is_local is False
    assert resolution.artifact.path == tmp_path / "data" / "outcomes.toml"
    assert resolution.artifact.source_repo == "judicial-record"
    assert resolution.artifact.authority_repo == "accountable-record"
    assert resolution.artifact.is_local is False


def test_choose_authority_source_uses_local_when_artifact_is_provided(
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local"
    external_root = tmp_path / "external"

    source = choose_authority_source(
        artifact_id="contract",
        local_provided_artifact_ids=("contract",),
        local_repo_name="accountable-record",
        local_repo_root=local_root,
        external_authority_repo_name="upstream",
        external_authority_repo_root=external_root,
    )

    assert source.repo_name == "accountable-record"
    assert source.repo_root == local_root
    assert source.is_local is True


def test_choose_authority_source_uses_external_when_artifact_is_not_provided(
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local"
    external_root = tmp_path / "external"

    source = choose_authority_source(
        artifact_id="outcomes",
        local_provided_artifact_ids=("contract",),
        local_repo_name="judicial-record",
        local_repo_root=local_root,
        external_authority_repo_name="accountable-record",
        external_authority_repo_root=external_root,
    )

    assert source.repo_name == "accountable-record"
    assert source.repo_root == external_root
    assert source.is_local is False


def test_dependency_to_locked_preserves_reference_fields() -> None:
    reference = parse_dependency_reference("org/repo@v1.2.3")

    locked = dependency_to_locked(reference)

    assert locked.owner == "org"
    assert locked.name == "repo"
    assert locked.version == "v1.2.3"
    assert locked.qualified_name == "org/repo"


def test_artifact_to_locked_preserves_artifact_fields() -> None:
    artifact = ResolvedArtifact(
        artifact_id="contract",
        kind="contract",
        path=Path("data/contract.toml"),
        source_repo="repo",
        authority_repo="repo",
        is_local=True,
    )

    locked = artifact_to_locked(artifact)

    assert locked.artifact_id == "contract"
    assert locked.kind == "contract"
    assert locked.path == "data/contract.toml"
    assert locked.source_repo == "repo"
    assert locked.authority_repo == "repo"
    assert locked.is_local is True


def test_build_lockfile_and_json_round_trip() -> None:
    dependencies = (parse_dependency_reference("org/repo@v1.2.3"),)
    artifacts = (
        ResolvedArtifact(
            artifact_id="contract",
            kind="contract",
            path=Path("data/contract.toml"),
            source_repo="repo",
            authority_repo="repo",
            is_local=True,
        ),
    )

    lockfile = build_lockfile(dependencies=dependencies, artifacts=artifacts)
    data = lockfile_to_json(lockfile)
    parsed = lockfile_from_json(data)

    assert parsed == lockfile
    assert data["schema"] == LOCKFILE_SCHEMA


def test_read_and_write_lockfile(tmp_path: Path) -> None:
    path = tmp_path / "se-contract-lock.json"
    lockfile = ContractLockfile(
        schema=LOCKFILE_SCHEMA,
        dependencies=(LockedDependency(owner="org", name="repo", version="v1.2.3"),),
        artifacts=(
            LockedArtifact(
                artifact_id="contract",
                kind="contract",
                path="data/contract.toml",
                source_repo="repo",
                authority_repo="repo",
                is_local=True,
            ),
        ),
    )

    write_lockfile(path, lockfile)

    assert read_lockfile(path) == lockfile


def test_lockfile_from_json_rejects_bad_schema() -> None:
    with pytest.raises(ValueError, match="unsupported lockfile schema"):
        lockfile_from_json(
            {
                "schema": "bad-schema",
                "dependencies": [],
                "artifacts": [],
            }
        )


def test_lockfile_from_json_rejects_non_list_dependencies() -> None:
    with pytest.raises(ValueError, match="dependencies"):
        lockfile_from_json(
            {
                "schema": LOCKFILE_SCHEMA,
                "dependencies": "bad",
                "artifacts": [],
            }
        )


def test_lockfile_from_json_rejects_non_list_artifacts() -> None:
    with pytest.raises(ValueError, match="artifacts"):
        lockfile_from_json(
            {
                "schema": LOCKFILE_SCHEMA,
                "dependencies": [],
                "artifacts": "bad",
            }
        )


def test_lockfile_from_json_rejects_bad_dependency_item() -> None:
    with pytest.raises(ValueError, match=r"dependencies\[0\].name"):
        lockfile_from_json(
            {
                "schema": LOCKFILE_SCHEMA,
                "dependencies": [{"owner": "org", "version": "v1.2.3"}],
                "artifacts": [],
            }
        )


def test_lockfile_from_json_rejects_bad_artifact_item() -> None:
    with pytest.raises(ValueError, match=r"artifacts\[0\].artifact_id"):
        lockfile_from_json(
            {
                "schema": LOCKFILE_SCHEMA,
                "dependencies": [],
                "artifacts": [
                    {
                        "kind": "contract",
                        "path": "data/contract.toml",
                        "source_repo": "repo",
                        "authority_repo": "repo",
                        "is_local": True,
                    }
                ],
            }
        )


def test_resolve_repo_config_resolves_required_dependencies_and_local_artifacts(
    tmp_path: Path,
) -> None:
    config = _repo_config(tmp_path)

    context = resolve_repo_config(repo_root=tmp_path, config=config)

    assert context.repo_root == tmp_path
    assert context.repo_name == "accountable-record"
    assert tuple(item.qualified_name for item in context.dependencies.required) == (
        "structural-explainability/se-manifest-schema",
    )
    assert context.dependencies.optional == ()
    assert len(context.provided_artifacts) == 1
    assert context.provided_artifacts[0].artifact_id == "accountable-record-contract"
    assert context.provided_artifacts[0].path == tmp_path / "data" / "contract.toml"
    assert context.provided_artifacts[0].is_local is True
    assert context.consumed_artifacts == ()
    assert context.all_artifacts == context.provided_artifacts


def test_resolve_repo_config_can_include_optional_dependencies(tmp_path: Path) -> None:
    config = _repo_config(tmp_path)

    context = resolve_repo_config(
        repo_root=tmp_path,
        config=config,
        options=ResolverOptions(include_optional_dependencies=True),
    )

    assert tuple(item.qualified_name for item in context.dependencies.optional) == (
        "structural-explainability/se-formal-contract",
    )


def test_resolve_repo_config_without_contract_config_has_no_artifacts(
    tmp_path: Path,
) -> None:
    config = RepoConfig(
        repo_root=tmp_path,
        manifest=_manifest_declaration(),
        contract_config=None,
    )

    context = resolve_repo_config(repo_root=tmp_path, config=config)

    assert context.provided_artifacts == ()
    assert context.consumed_artifacts == ()
    assert context.all_artifacts == ()
