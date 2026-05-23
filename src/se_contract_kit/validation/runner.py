"""Check runner: execute a registry against a context with crash isolation.

The runner is the only place that knows about strict mode and overall outcome.
It runs each selected check, isolates crashes (a check raising ContractKitError
becomes a cannot-verify result rather than aborting the run), collects all
results, and computes an exit code.

Strict mode is applied here, not in checks: checks report severity, and the
runner decides whether warning-severity findings fail the run.
"""

from dataclasses import dataclass

from se_contract_kit.base.errors import ContractKitError
from se_contract_kit.resolution.context import ResolutionContext
from se_contract_kit.validation.registry import CheckRegistry
from se_contract_kit.validation.results import (
    CheckResult,
    CheckSeverity,
    CheckStatus,
    cannot_verify,
    worst_status,
)

__all__ = [
    "RunReport",
    "run_checks",
]

EXIT_OK = 0
EXIT_FAILED = 1


@dataclass(frozen=True)
class RunReport:
    """The outcome of running a registry against a context.

    Attributes:
        results: Every finding from every check, in check order.
        strict: Whether the run was executed in strict mode.
        overall_status: Worst status across all results.
    """

    results: tuple[CheckResult, ...]
    strict: bool
    overall_status: CheckStatus

    @property
    def failures(self) -> tuple[CheckResult, ...]:
        """Return results that count as failures for this run's mode.

        Error-severity findings always count. Warning-severity findings count
        only under strict mode. cannot-verify always counts.
        """
        counted: list[CheckResult] = []
        for result in self.results:
            if (
                result.status == CheckStatus.CANNOT_VERIFY
                or result.status == CheckStatus.FAIL
                and (result.severity == CheckSeverity.ERROR or self.strict)
            ):
                counted.append(result)
        return tuple(counted)

    @property
    def passed(self) -> bool:
        """Return True when no findings count as failures for this mode."""
        return len(self.failures) == 0

    @property
    def exit_code(self) -> int:
        """Return the process exit code: 0 when passed, 1 otherwise."""
        return EXIT_OK if self.passed else EXIT_FAILED


def run_checks(
    *,
    registry: CheckRegistry,
    context: ResolutionContext,
    strict: bool = False,
) -> RunReport:
    """Run the selected checks against the context with crash isolation.

    Each check is executed independently. If a check raises ContractKitError
    (operational failure: missing or malformed input), it is recorded as a
    cannot-verify result and the run continues; one broken check never hides
    the results of the others.

    Args:
        registry: The checks to run (kit defaults plus any consumer checks).
        context: The resolved run context.
        strict: When True, run strict_only checks and treat warnings as failures.

    Returns:
        A RunReport with all results and the computed overall status.
    """
    collected: list[CheckResult] = []

    for check in registry.select(strict=strict):
        try:
            collected.extend(check.run(context))
        except ContractKitError as exc:
            collected.append(
                cannot_verify(
                    check.check_id,
                    f"check could not run: {exc}",
                )
            )

    return RunReport(
        results=tuple(collected),
        strict=strict,
        overall_status=worst_status(collected),
    )
