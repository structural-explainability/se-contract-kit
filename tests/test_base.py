"""Tests for se_contract_kit.base."""

from pathlib import Path

import pytest

from se_contract_kit.base.errors import (
    ContractKitFileError,
    ContractKitJsonError,
    ContractKitPathError,
)
from se_contract_kit.base.io import (
    read_json,
    read_text,
    read_toml,
    write_json,
    write_text,
)
from se_contract_kit.base.json_utils import (
    canonical_json_text,
    pretty_json_text,
    sha256_json,
    sha256_text,
)
from se_contract_kit.base.paths import (
    find_contract_config_path,
    find_manifest_path,
    find_repo_root,
    find_upward,
    normalize_path,
    repo_relative_path,
    resolve_repo_path,
)


def test_read_and_write_text(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "file.txt"

    write_text(path, "hello")

    assert read_text(path) == "hello"


def test_read_text_missing_file_raises_contract_file_error(tmp_path: Path) -> None:
    path = tmp_path / "missing.txt"

    with pytest.raises(ContractKitFileError):
        read_text(path)


def test_read_toml_reads_mapping(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('name = "example"\n', encoding="utf-8")

    assert read_toml(path) == {"name": "example"}


def test_read_toml_invalid_file_raises_contract_file_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.toml"
    path.write_text("name = \n", encoding="utf-8")

    with pytest.raises(ContractKitFileError):
        read_toml(path)


def test_read_and_write_json(tmp_path: Path) -> None:
    path = tmp_path / "data" / "value.json"
    value = {"b": 2, "a": 1}

    write_json(path, value)

    assert read_json(path) == value
    assert path.read_text(encoding="utf-8") == '{\n  "a": 1,\n  "b": 2\n}\n'


def test_read_json_invalid_file_raises_contract_json_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(ContractKitJsonError):
        read_json(path)


def test_write_json_unserializable_value_raises_contract_json_error(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bad.json"

    with pytest.raises(ContractKitJsonError):
        write_json(path, {"bad": object()})


def test_canonical_json_text_is_stable() -> None:
    value = {"b": 2, "a": 1}

    assert canonical_json_text(value) == '{"a":1,"b":2}'


def test_pretty_json_text_is_stable() -> None:
    value = {"b": 2, "a": 1}

    assert pretty_json_text(value) == '{\n  "a": 1,\n  "b": 2\n}\n'


def test_json_helpers_reject_unserializable_value() -> None:
    value = {"bad": object()}

    with pytest.raises(ContractKitJsonError):
        canonical_json_text(value)

    with pytest.raises(ContractKitJsonError):
        pretty_json_text(value)

    with pytest.raises(ContractKitJsonError):
        sha256_json(value)


def test_sha256_text_is_stable() -> None:
    assert sha256_text("abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_sha256_json_is_stable() -> None:
    assert sha256_json({"b": 2, "a": 1}) == sha256_text('{"a":1,"b":2}')


def test_normalize_path_returns_absolute_path(tmp_path: Path) -> None:
    path = normalize_path(tmp_path)

    assert path.is_absolute()


def test_find_upward_finds_file_in_parent(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    child = root / "a" / "b"
    child.mkdir(parents=True)
    marker = root / "pyproject.toml"
    marker.write_text("[project]\n", encoding="utf-8")

    assert find_upward("pyproject.toml", child) == marker


def test_find_upward_accepts_file_start_path(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    child = root / "a"
    child.mkdir(parents=True)
    marker = root / "pyproject.toml"
    marker.write_text("[project]\n", encoding="utf-8")
    start_file = child / "file.txt"
    start_file.write_text("x", encoding="utf-8")

    assert find_upward("pyproject.toml", start_file) == marker


def test_find_upward_returns_none_when_missing(tmp_path: Path) -> None:
    child = tmp_path / "a" / "b"
    child.mkdir(parents=True)

    assert find_upward("missing.txt", child) is None


def test_find_repo_root_prefers_pyproject(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    child = root / "src"
    child.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    assert find_repo_root(child) == root.resolve()


def test_find_repo_root_accepts_file_start_path(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    child = root / "src"
    child.mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    start_file = child / "module.py"
    start_file.write_text("", encoding="utf-8")

    assert find_repo_root(start_file) == root.resolve()


def test_find_repo_root_falls_back_to_git_dir(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    child = root / "src"
    child.mkdir(parents=True)
    (root / ".git").mkdir()

    assert find_repo_root(child) == root.resolve()


def test_find_repo_root_missing_raises_contract_path_error(tmp_path: Path) -> None:
    child = tmp_path / "a" / "b"
    child.mkdir(parents=True)

    with pytest.raises(ContractKitPathError):
        find_repo_root(child)


def test_find_manifest_path_prefers_manifest_toml(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    manifest = root / "MANIFEST.toml"
    manifest.write_text("schema = 'x'\n", encoding="utf-8")
    se_manifest = root / "SE_MANIFEST.toml"
    se_manifest.write_text("schema = 'y'\n", encoding="utf-8")

    assert find_manifest_path(root) == manifest.resolve()


def test_find_manifest_path_accepts_se_manifest(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    manifest = root / "SE_MANIFEST.toml"
    manifest.write_text("schema = 'x'\n", encoding="utf-8")

    assert find_manifest_path(root) == manifest.resolve()


def test_find_manifest_path_missing_raises_contract_path_error(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    with pytest.raises(ContractKitPathError):
        find_manifest_path(root)


def test_find_contract_config_path_finds_contract_toml(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    contract = root / "contract.toml"
    contract.write_text("[contract]\n", encoding="utf-8")

    assert find_contract_config_path(root) == contract.resolve()


def test_find_contract_config_path_missing_raises_contract_path_error(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    with pytest.raises(ContractKitPathError):
        find_contract_config_path(root)


def test_repo_relative_path_returns_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    path = root / "data" / "file.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")

    assert repo_relative_path(path, root) == Path("data") / "file.json"


def test_repo_relative_path_outside_root_raises_contract_path_error(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside.txt"
    root.mkdir()
    outside.write_text("x", encoding="utf-8")

    with pytest.raises(ContractKitPathError):
        repo_relative_path(outside, root)


def test_resolve_repo_path_returns_path_inside_repo(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    assert (
        resolve_repo_path(root, "data/file.json")
        == (root / "data" / "file.json").resolve()
    )


def test_resolve_repo_path_escape_raises_contract_path_error(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    with pytest.raises(ContractKitPathError):
        resolve_repo_path(root, "../outside.txt")
