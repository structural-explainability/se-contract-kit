"""Structural check: resolved artifacts exist and parse.

Generic by the kit test: true of any SE contract repo, including one with an
empty domain model. The resolver tells us *where* each artifact is; this check
confirms the resolved path actually exists and parses as its declared format.

Format is inferred from the artifact's resolved path suffix (.toml/.json).
Artifacts with other or no suffix are checked for existence only, since the
kit makes no assumption about non-TOML/JSON artifact content.

Reads resolver-provided paths via base/io. Never constructs paths from layout
convention.
"""

from collections.abc import Iterable

from se_contract_kit.base.errors import ContractKitError
from se_contract_kit.base.io import read_json, read_toml
from se_contract_kit.resolution.context import ResolutionContext
from se_contract_kit.validation.registry import Check
from se_contract_kit.validation.results import CheckResult, failure, ok

__all__ = ["CHECK_ID", "check_source", "CHECK"]

CHECK_ID = "structural.source"


def check_source(context: ResolutionContext) -> Iterable[CheckResult]:
    """Verify each resolved artifact exists and parses as its declared format."""
    results: list[CheckResult] = []

    for artifact in context.all_artifacts:
        path = artifact.path

        if not path.is_file():
            results.append(
                failure(
                    CHECK_ID,
                    f"resolved artifact path does not exist: {path}",
                    artifact_id=artifact.artifact_id,
                    detail={"path": str(path)},
                )
            )
            continue

        suffix = path.suffix.lower()
        try:
            if suffix == ".toml":
                read_toml(path)
            elif suffix == ".json":
                read_json(path)
            # other suffixes: existence already confirmed; no content assumption
        except ContractKitError as exc:
            results.append(
                failure(
                    CHECK_ID,
                    f"resolved artifact does not parse: {exc}",
                    artifact_id=artifact.artifact_id,
                    detail={"path": str(path)},
                )
            )

    if not results:
        results.append(
            ok(
                CHECK_ID,
                f"all {len(context.all_artifacts)} resolved artifacts exist and parse",
            )
        )

    return results


CHECK = Check(
    check_id=CHECK_ID,
    title="Resolved artifacts exist and parse",
    run=check_source,
)
