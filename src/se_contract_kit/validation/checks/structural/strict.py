"""Structural check: released artifacts contain no unfinished-work markers.

Generic by the kit test: any SE contract repo, at release, should not ship
placeholder/TODO content in its resolved artifacts. This is a strict-only
check — it runs in strict mode (release validation), not on every routine
validation, because in-progress drafts legitimately contain TODOs.

Scans the text of resolved TOML/JSON artifacts for unfinished-work markers.
Reads resolver-provided paths via base/io; never constructs paths from layout.
"""

from collections.abc import Iterable

from se_contract_kit.base.errors import ContractKitError
from se_contract_kit.base.io import read_text
from se_contract_kit.resolution.context import ResolutionContext
from se_contract_kit.validation.registry import Check
from se_contract_kit.validation.results import CheckResult, failure, ok

__all__ = ["CHECK_ID", "TODO_MARKERS", "check_strict_no_todo", "CHECK"]

CHECK_ID = "structural.strict.no-todo"

# WHY: the markers the SE annotation convention treats as unfinished work.
# WHY: matched case-insensitively as whole tokens to avoid false hits inside
# ordinary words (e.g. "fixture" must not match "FIXME").
TODO_MARKERS: tuple[str, ...] = ("TODO", "FIXME", "XXX")

_TEXT_SUFFIXES: frozenset[str] = frozenset({".toml", ".json"})


def _markers_in_text(text: str) -> list[str]:
    """Return the markers present as standalone tokens in text."""
    upper = text.upper()
    found: list[str] = []
    for marker in TODO_MARKERS:
        index = upper.find(marker)
        while index != -1:
            before = upper[index - 1] if index > 0 else ""
            after_index = index + len(marker)
            after = upper[after_index] if after_index < len(upper) else ""
            if not before.isalnum() and not after.isalnum():
                found.append(marker)
                break
            index = upper.find(marker, index + 1)
    return found


def check_strict_no_todo(context: ResolutionContext) -> Iterable[CheckResult]:
    """Verify no released artifact contains an unfinished-work marker."""
    results: list[CheckResult] = []

    for artifact in context.all_artifacts:
        if artifact.path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        try:
            text = read_text(artifact.path)
        except ContractKitError:
            # existence/parse is structural.source's job; skip quietly here
            continue

        markers = _markers_in_text(text)
        if markers:
            results.append(
                failure(
                    CHECK_ID,
                    f"released artifact contains unfinished-work marker(s): "
                    f"{', '.join(sorted(set(markers)))}",
                    artifact_id=artifact.artifact_id,
                    detail={"path": str(artifact.path)},
                )
            )

    if not results:
        results.append(ok(CHECK_ID, "no unfinished-work markers in artifacts"))

    return results


CHECK = Check(
    check_id=CHECK_ID,
    title="No TODO/FIXME markers in released artifacts",
    run=check_strict_no_todo,
    strict_only=True,
)
