"""Constraints check: domain mappings close over the resolved vocabulary.

One of the two checks that exist specifically because the kit uses
dependency-resolve. It enforces:

    Every value a domain maps onto an authority vocabulary must be a member of
    that resolved vocabulary. The domain may not invent a value outside it.

This is the kit-generic form of "every domain subject maps onto exactly one of
AR's nine kinds." It is VOCABULARY-AGNOSTIC by design: the kit never hardcodes
"nine", never knows the kinds' names. It resolves whatever vocabulary artifact
the domain consumes and checks closure against that artifact's contents. The
same machinery serves any domain mapping onto any authority vocabulary.

Inputs, all from the resolved context:
  - the resolved vocabulary artifact (an artifact whose kind is "vocabulary"):
    its parsed members define the allowed target set.
  - the resolved mapping artifact (kind "mapping"): its parsed entries are the
    domain's subject -> vocabulary-member assignments.

Closure violation: a mapping entry whose target is not a member of the resolved
vocabulary. (Totality - every subject is mapped - is a domain concern the domain
appends; the kit checks closure, the universal half.)

Reads resolver-provided paths via base/io. Never constructs paths or hardcodes
vocabulary contents.
"""

from collections.abc import Iterable

from se_contract_kit.base.errors import ContractKitError
from se_contract_kit.base.io import read_toml
from se_contract_kit.resolution.context import ResolutionContext
from se_contract_kit.validation.registry import Check
from se_contract_kit.validation.results import CheckResult, failure, ok, partial

__all__ = [
    "CHECK_ID",
    "VOCABULARY_KIND",
    "MAPPING_KIND",
    "check_constraints",
    "CHECK",
]

CHECK_ID = "constraints.closure"
VOCABULARY_KIND = "vocabulary"
MAPPING_KIND = "mapping"

# WHY: generic keys. A vocabulary artifact lists its members under "members";
# a mapping artifact lists entries under "entries", each with "subject" and
# "target". These are kit conventions for the generic closure check, not AR
# layout - a domain authors mapping/vocabulary artifacts in this shape.
_VOCAB_MEMBERS_KEY = "members"
_MAPPING_ENTRIES_KEY = "entries"
_ENTRY_SUBJECT_KEY = "subject"
_ENTRY_TARGET_KEY = "target"


def _read_toml_object(path: object) -> object:
    """Read TOML and return it as a plain object (stops Any at the boundary)."""
    # WHY: read_toml may be typed dict[str, Any]; binding to object here forces
    # all downstream narrowing to start from a known type, not from Any.
    parsed: object = read_toml(path)  # type: ignore[arg-type]
    return parsed


def _as_object_dict(value: object) -> dict[str, object] | None:
    """Return value as a string-keyed object dict if it is a dict, else None."""
    if not isinstance(value, dict):
        return None
    narrowed: dict[str, object] = {}
    for key, item in value.items():  # type: ignore[misc]
        narrowed[str(key)] = item  # type: ignore[index]
    return narrowed


def _as_str_list(value: object) -> list[str] | None:
    """Return value as a list of strings if it is a list, else None."""
    if not isinstance(value, list):
        return None
    return [str(item) for item in value]  # type: ignore[misc]


def _vocabulary_members(data: dict[str, object]) -> set[str]:
    """Extract the member id set from a parsed vocabulary artifact."""
    members = _as_str_list(data.get(_VOCAB_MEMBERS_KEY))
    return set(members) if members is not None else set()


def check_constraints(context: ResolutionContext) -> Iterable[CheckResult]:
    """Verify every mapping target is a member of the resolved vocabulary."""
    vocab_artifacts = [a for a in context.all_artifacts if a.kind == VOCABULARY_KIND]
    mapping_artifacts = [a for a in context.all_artifacts if a.kind == MAPPING_KIND]

    if not mapping_artifacts:
        return [partial(CHECK_ID, "no mapping artifacts to check")]
    if not vocab_artifacts:
        return [
            failure(
                CHECK_ID,
                "mappings present but no resolved vocabulary artifact to close "
                "over; cannot verify the domain stays within an authority "
                "vocabulary",
            )
        ]

    # Union of all resolved vocabulary members (typically one authority vocab).
    allowed: set[str] = set()
    for artifact in vocab_artifacts:
        try:
            vocab_data = _as_object_dict(_read_toml_object(artifact.path))
        except ContractKitError as exc:
            return [failure(CHECK_ID, f"vocabulary artifact unreadable: {exc}")]
        if vocab_data is not None:
            allowed |= _vocabulary_members(vocab_data)

    if not allowed:
        return [
            failure(
                CHECK_ID,
                "resolved vocabulary declares no members; closure is undefined",
            )
        ]

    findings: list[CheckResult] = []
    checked_entries = 0

    for artifact in mapping_artifacts:
        try:
            mapping_data = _as_object_dict(_read_toml_object(artifact.path))
        except ContractKitError as exc:
            findings.append(
                failure(
                    CHECK_ID,
                    f"mapping artifact unreadable: {exc}",
                    artifact_id=artifact.artifact_id,
                )
            )
            continue

        if mapping_data is None:
            findings.append(
                failure(
                    CHECK_ID,
                    "mapping artifact is not a table",
                    artifact_id=artifact.artifact_id,
                )
            )
            continue

        raw_entries = mapping_data.get(_MAPPING_ENTRIES_KEY)
        if not isinstance(raw_entries, list):
            findings.append(
                failure(
                    CHECK_ID,
                    f"mapping artifact has no {_MAPPING_ENTRIES_KEY!r} list",
                    artifact_id=artifact.artifact_id,
                )
            )
            continue

        entries: list[object] = list(raw_entries)  # type: ignore[misc]
        for raw_entry in entries:
            entry = _as_object_dict(raw_entry)
            if entry is None:
                continue
            checked_entries += 1

            subject_value = entry.get(_ENTRY_SUBJECT_KEY)
            target_value = entry.get(_ENTRY_TARGET_KEY)
            subject = "" if subject_value is None else str(subject_value)
            target = "" if target_value is None else str(target_value)

            if target not in allowed:
                findings.append(
                    failure(
                        CHECK_ID,
                        f"mapping target {target!r} (subject {subject!r}) is "
                        f"not a member of the resolved vocabulary; the domain "
                        f"may not map onto a value outside the authority "
                        f"vocabulary",
                        artifact_id=artifact.artifact_id,
                        detail={"subject": subject, "target": target},
                    )
                )

    if not findings:
        findings.append(
            ok(
                CHECK_ID,
                f"{checked_entries} mapping entries all close over the "
                f"resolved vocabulary ({len(allowed)} members)",
            )
        )

    return findings


CHECK = Check(
    check_id=CHECK_ID,
    title="Domain mappings close over the resolved authority vocabulary",
    run=check_constraints,
)
