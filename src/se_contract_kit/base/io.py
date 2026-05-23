"""File IO helpers."""

import json
from pathlib import Path
import tomllib

from se_contract_kit.base.errors import ContractKitFileError, ContractKitJsonError

__all__ = [
    "read_text",
    "write_text",
    "read_toml",
    "read_json",
    "write_json",
]


def read_text(path: Path) -> str:
    """Read a UTF-8 text file."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractKitFileError(f"Could not read text file: {path}") from exc


def write_text(path: Path, text: str) -> None:
    """Write a UTF-8 text file, creating parent directories as needed."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise ContractKitFileError(f"Could not write text file: {path}") from exc


def read_toml(path: Path) -> dict[str, object]:
    """Read a TOML file.

    Returns dict[str, object], not dict[str, Any]: parsed TOML is untyped data,
    and returning object forces callers to narrow at the boundary rather than
    letting Any leak unchecked through downstream code.
    """
    try:
        return tomllib.loads(read_text(path))
    except tomllib.TOMLDecodeError as exc:
        raise ContractKitFileError(f"Could not parse TOML file: {path}") from exc


def read_json(path: Path) -> object:
    """Read a JSON file.

    Returns object, not Any: callers narrow the parsed value at the boundary.
    """
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise ContractKitJsonError(f"Could not parse JSON file: {path}") from exc


def write_json(path: Path, value: object) -> None:
    """Write a JSON file using stable formatting."""
    try:
        text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
    except TypeError as exc:
        raise ContractKitJsonError(f"Could not serialize JSON for: {path}") from exc

    write_text(path, f"{text}\n")
