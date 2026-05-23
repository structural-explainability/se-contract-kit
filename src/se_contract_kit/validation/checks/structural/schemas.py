"""Structural check: schema-kind artifacts are valid JSON Schema documents.

Generic by the kit test: any SE contract repo that declares schema artifacts
must have them be well-formed schemas, regardless of domain. The kit does not
know what the schema describes; it only checks that a schema-kind artifact is
valid JSON and carries the structural marks of a JSON Schema document.

A "schema-kind" artifact is identified by ResolvedArtifact.kind == "schema".
The kit treats kind as opaque elsewhere; here it is the one generic kind the
kit recognizes, because "is a valid schema" is checkable without domain
knowledge.

Reads resolver-provided paths via base/io. Existence and JSON-parse are the
source check's job (structural.source); this check assumes the artifact parsed
and validates schema-specific shape, re-reading defensively.
"""

from collections.abc import Iterable
from typing import Any

from se_contract_kit.base.errors import ContractKitError
from se_contract_kit.base.io import read_json
from se_contract_kit.resolution.context import ResolutionContext
from se_contract_kit.validation.registry import Check
from se_contract_kit.validation.results import CheckResult, failure, ok, partial

__all__ = ["CHECK_ID", "SCHEMA_KIND", "check_schemas", "CHECK"]

CHECK_ID = "structural.schemas"
SCHEMA_KIND = "schema"

# WHY: a JSON Schema document declares its dialect via "$schema". Requiring it
# is the minimal generic structural mark; the kit does not validate the schema
# against a metaschema (that needs a metaschema artifact and is not universal).
_SCHEMA_DIALECT_KEY = "$schema"


def check_schemas(context: ResolutionContext) -> Iterable[CheckResult]:
    """Verify schema-kind artifacts are valid JSON Schema documents."""
    results: list[CheckResult] = []

    schema_artifacts = [
        artifact for artifact in context.all_artifacts if artifact.kind == SCHEMA_KIND
    ]

    if not schema_artifacts:
        return [partial(CHECK_ID, "no schema-kind artifacts to check")]

    for artifact in schema_artifacts:
        try:
            data: Any = read_json(artifact.path)
        except ContractKitError as exc:
            results.append(
                failure(
                    CHECK_ID,
                    f"schema artifact does not parse as JSON: {exc}",
                    artifact_id=artifact.artifact_id,
                    detail={"path": str(artifact.path)},
                )
            )
            continue

        if not isinstance(data, dict):
            results.append(
                failure(
                    CHECK_ID,
                    "schema artifact is not a JSON object",
                    artifact_id=artifact.artifact_id,
                    detail={"path": str(artifact.path)},
                )
            )
            continue

        if _SCHEMA_DIALECT_KEY not in data:
            results.append(
                failure(
                    CHECK_ID,
                    f"schema artifact missing {_SCHEMA_DIALECT_KEY!r} dialect "
                    f"declaration",
                    artifact_id=artifact.artifact_id,
                    detail={"path": str(artifact.path)},
                )
            )

    if not results:
        results.append(
            ok(CHECK_ID, f"all {len(schema_artifacts)} schema artifacts valid")
        )

    return results


CHECK = Check(
    check_id=CHECK_ID,
    title="Schema-kind artifacts are valid JSON Schema",
    run=check_schemas,
)
