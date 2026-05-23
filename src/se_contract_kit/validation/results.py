"""Check results: the output contract for every validation check.

A check reports findings as a sequence of CheckResult values. The status
vocabulary is the SE closed conformance vocabulary (pass, fail, partial,
cannot-verify), reused here so the kit speaks one status language internally
and when validating against that vocabulary.

Severity (error, warning) is orthogonal to status: it lets the runner decide,
under strict mode, whether a non-fatal finding should fail the run. Checks
report severity; they do not know whether strict mode is active.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum

__all__ = [
    "CheckSeverity",
    "CheckStatus",
    "CheckResult",
    "cannot_verify",
    "failure",
    "ok",
    "partial",
    "warning",
    "worst_status",
]


class CheckStatus(StrEnum):
    """Closed conformance status vocabulary.

    PASS:          the check ran and found no violations.
    FAIL:          the check ran and found at least one violation.
    PARTIAL:       the check ran but some inputs were absent or incomplete.
    CANNOT_VERIFY: the check could not run (missing/malformed input, env error).
    """

    PASS = "pass"  # noqa: E501, S105
    FAIL = "fail"
    PARTIAL = "partial"
    CANNOT_VERIFY = "cannot-verify"


class CheckSeverity(StrEnum):
    """Finding severity, independent of status.

    ERROR:   a violation that fails the run in all modes.
    WARNING: a concern that fails the run only under strict mode.
    """

    ERROR = "error"
    WARNING = "warning"


# WHY: status ordering for aggregation. A run's overall status is the worst
# status across its results. cannot-verify is worst because an unrun check is
# strictly less trustworthy than a failed one (we know nothing, vs we know it
# failed). Order: pass < partial < fail < cannot-verify.
_STATUS_RANK: dict[CheckStatus, int] = {
    CheckStatus.PASS: 0,
    CheckStatus.PARTIAL: 1,
    CheckStatus.FAIL: 2,
    CheckStatus.CANNOT_VERIFY: 3,
}


@dataclass(frozen=True)
class CheckResult:
    """A single finding from a check.

    Attributes:
        check_id: Stable id of the check that produced this result.
        status: Conformance status for this finding.
        message: Human-readable description of the finding.
        severity: Whether this finding is an error or a (strict-only) warning.
        artifact_id: Artifact this finding concerns, when applicable.
        detail: Optional structured key/value context for tooling.
    """

    check_id: str
    status: CheckStatus
    message: str
    severity: CheckSeverity = CheckSeverity.ERROR
    artifact_id: str | None = None
    detail: dict[str, str] = field(default_factory=lambda: {})

    @property
    def is_failure(self) -> bool:
        """Return True for a definitive non-pass outcome (fail/cannot-verify)."""
        return self.status in (CheckStatus.FAIL, CheckStatus.CANNOT_VERIFY)


def ok(check_id: str, message: str = "OK") -> CheckResult:
    """Build a passing result."""
    return CheckResult(check_id=check_id, status=CheckStatus.PASS, message=message)


def failure(
    check_id: str,
    message: str,
    *,
    severity: CheckSeverity = CheckSeverity.ERROR,
    artifact_id: str | None = None,
    detail: dict[str, str] | None = None,
) -> CheckResult:
    """Build a failing result (default severity error)."""
    return CheckResult(
        check_id=check_id,
        status=CheckStatus.FAIL,
        message=message,
        severity=severity,
        artifact_id=artifact_id,
        detail=detail or {},
    )


def warning(
    check_id: str,
    message: str,
    *,
    artifact_id: str | None = None,
    detail: dict[str, str] | None = None,
) -> CheckResult:
    """Build a warning-severity finding (fails only under strict mode).

    Status is FAIL with WARNING severity: the finding is a real violation, but
    the runner may downgrade it to non-fatal when not in strict mode.
    """
    return CheckResult(
        check_id=check_id,
        status=CheckStatus.FAIL,
        message=message,
        severity=CheckSeverity.WARNING,
        artifact_id=artifact_id,
        detail=detail or {},
    )


def partial(check_id: str, message: str) -> CheckResult:
    """Build a partial result: ran, but some inputs were absent."""
    return CheckResult(check_id=check_id, status=CheckStatus.PARTIAL, message=message)


def cannot_verify(check_id: str, message: str) -> CheckResult:
    """Build a cannot-verify result: the check could not run."""
    return CheckResult(
        check_id=check_id, status=CheckStatus.CANNOT_VERIFY, message=message
    )


def worst_status(results: Iterable[CheckResult]) -> CheckStatus:
    """Return the worst status across results, or PASS when there are none."""
    worst = CheckStatus.PASS
    for result in results:
        if _STATUS_RANK[result.status] > _STATUS_RANK[worst]:
            worst = result.status
    return worst
