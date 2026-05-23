"""Dependency declarations and references.

This module parses dependency references declared by a repository.

It does not resolve, fetch, cache, validate, or inspect dependency contents.
"""

from dataclasses import dataclass

__all__ = [
    "DependencyReference",
    "DependencySet",
    "build_dependency_set",
    "parse_dependency_reference",
    "parse_dependency_references",
]


@dataclass(frozen=True)
class DependencyReference:
    """A parsed dependency reference."""

    raw: str
    owner: str | None
    name: str
    version: str

    @property
    def qualified_name(self) -> str:
        """Return owner/name when an owner is present; otherwise name."""
        if self.owner is None:
            return self.name
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True)
class DependencySet:
    """Parsed required and optional dependency references."""

    required: tuple[DependencyReference, ...]
    optional: tuple[DependencyReference, ...]


def parse_dependency_reference(value: str) -> DependencyReference:
    """Parse a dependency reference.

    Accepted forms:
      name@version
      owner/name@version
    """
    if not value:
        raise ValueError("dependency reference must be a nonempty string")

    if value.count("@") != 1:
        raise ValueError(
            "dependency reference must have exactly one '@': "
            "expected name@version or owner/name@version"
        )

    name_part, version = value.split("@", maxsplit=1)
    if not name_part:
        raise ValueError("dependency reference missing dependency name")
    if not version:
        raise ValueError("dependency reference missing version")

    parts = name_part.split("/")
    if len(parts) == 1:
        owner = None
        name = parts[0]
    elif len(parts) == 2:
        owner, name = parts
        if not owner:
            raise ValueError("dependency reference missing owner before '/'")
    else:
        raise ValueError(
            "dependency reference must use name@version or owner/name@version"
        )

    if not name:
        raise ValueError("dependency reference missing dependency name")

    return DependencyReference(
        raw=value,
        owner=owner,
        name=name,
        version=version,
    )


def parse_dependency_references(
    values: tuple[str, ...],
) -> tuple[DependencyReference, ...]:
    """Parse dependency references in declared order."""
    return tuple(parse_dependency_reference(value) for value in values)


def build_dependency_set(
    *,
    required: tuple[str, ...],
    optional: tuple[str, ...],
) -> DependencySet:
    """Build a parsed dependency set."""
    return DependencySet(
        required=parse_dependency_references(required),
        optional=parse_dependency_references(optional),
    )
