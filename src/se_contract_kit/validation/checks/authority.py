"""Authority check: provide-or-consume, never locally redefine upstream artifacts.

This is one of the two checks that exist specifically because the kit uses
dependency-resolve. It enforces the ecosystem rule:

    A repo may either PROVIDE an artifact or CONSUME it, but it must not
    locally redefine an artifact owned by an upstream authority.

It answers a different question than constraints.py:
  - authority.py: did this repo redefine something it does not own?
  - constraints.py: do this repo's mappings stay within the resolved vocabulary?

A repo could pass one and fail the other, so both run.

What this check inspects (all from the resolved context, no filesystem access):
  - provided artifacts (resolved from this repo, is_local=True)
  - consumed artifacts (resolved from an upstream authority, is_local=False)

Violations:
  1. Redefinition: an artifact id appears in BOTH provided and consumed. The
     repo consumes it from an authority AND declares its own local copy.
  2. Self-authority on a consumed artifact: a consumed artifact whose
     authority_repo equals this repo. Consuming implies an upstream authority;
     naming yourself as the authority of a consumed artifact is incoherent.
  3. Foreign provider: a provided artifact whose authority_repo is some other
     repo. Providing implies you are the authority; a provided artifact must be
     authored here.
"""

from collections.abc import Iterable

from se_contract_kit.resolution.context import ResolutionContext
from se_contract_kit.validation.registry import Check
from se_contract_kit.validation.results import CheckResult, failure, ok

__all__ = ["CHECK_ID", "check_authority", "CHECK"]

CHECK_ID = "authority"


def check_authority(context: ResolutionContext) -> Iterable[CheckResult]:
    """Verify provide-or-consume and the absence of local redefinition."""
    results: list[CheckResult] = []

    repo = context.repo_name
    provided = context.provided_artifacts
    consumed = context.consumed_artifacts

    provided_ids = {artifact.artifact_id for artifact in provided}
    consumed_ids = {artifact.artifact_id for artifact in consumed}

    # Violation 1: same artifact both provided locally and consumed upstream.
    redefined = sorted(provided_ids & consumed_ids)
    for artifact_id in redefined:
        results.append(
            failure(
                CHECK_ID,
                (
                    f"artifact {artifact_id!r} is both provided locally and "
                    f"consumed from an upstream authority; a repo must provide "
                    f"or consume an artifact, not redefine an upstream-owned one"
                ),
                artifact_id=artifact_id,
            )
        )

    # Violation 2: a consumed artifact that names this repo as its authority.
    for artifact in consumed:
        if artifact.authority_repo == repo:
            results.append(
                failure(
                    CHECK_ID,
                    (
                        f"consumed artifact {artifact.artifact_id!r} names this "
                        f"repo ({repo!r}) as its authority; a consumed artifact "
                        f"must be authored by an upstream authority"
                    ),
                    artifact_id=artifact.artifact_id,
                    detail={"authority_repo": artifact.authority_repo},
                )
            )

    # Violation 3: a provided artifact authored by a foreign authority.
    for artifact in provided:
        if artifact.authority_repo != repo:
            results.append(
                failure(
                    CHECK_ID,
                    (
                        f"provided artifact {artifact.artifact_id!r} names "
                        f"{artifact.authority_repo!r} as its authority, not this "
                        f"repo ({repo!r}); a provided artifact must be authored here"
                    ),
                    artifact_id=artifact.artifact_id,
                    detail={"authority_repo": artifact.authority_repo},
                )
            )

    if not results:
        results.append(
            ok(
                CHECK_ID,
                f"provide-or-consume satisfied: {len(provided_ids)} provided, "
                f"{len(consumed_ids)} consumed, no redefinition",
            )
        )

    return results


CHECK = Check(
    check_id=CHECK_ID,
    title="Provide-or-consume authority rule",
    run=check_authority,
)
