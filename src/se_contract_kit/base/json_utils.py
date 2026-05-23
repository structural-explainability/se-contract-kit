"""Canonical JSON helpers."""

import hashlib
import json
from typing import Any

from se_contract_kit.base.errors import ContractKitJsonError

__all__ = [
    "canonical_json_text",
    "pretty_json_text",
    "sha256_text",
    "sha256_json",
]


def canonical_json_text(value: Any) -> str:
    """Return canonical JSON text for stable comparison and hashing."""
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except TypeError as exc:
        raise ContractKitJsonError("Could not serialize canonical JSON") from exc


def pretty_json_text(value: Any) -> str:
    """Return human-readable stable JSON text."""
    try:
        return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    except TypeError as exc:
        raise ContractKitJsonError("Could not serialize pretty JSON") from exc


def sha256_text(text: str) -> str:
    """Return the SHA-256 digest for UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    """Return the SHA-256 digest for canonical JSON."""
    return sha256_text(canonical_json_text(value))
