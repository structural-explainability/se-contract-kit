"""Validation layer: checks, registry, runner, and the default check set.

Public surface:
  - Check, CheckRegistry          the check contract and its catalogue
  - CheckResult, CheckStatus, ...  the result vocabulary
  - RunReport, run_checks          execution with crash isolation
  - default_registry, DEFAULT_CHECKS  the kit's fixed generic check set
"""

from se_contract_kit.validation.defaults import DEFAULT_CHECKS, default_registry
from se_contract_kit.validation.registry import Check, CheckFunc, CheckRegistry
from se_contract_kit.validation.results import (
    CheckResult,
    CheckSeverity,
    CheckStatus,
)
from se_contract_kit.validation.runner import RunReport, run_checks

__all__ = [
    "Check",
    "CheckFunc",
    "CheckRegistry",
    "CheckResult",
    "CheckSeverity",
    "CheckStatus",
    "RunReport",
    "run_checks",
    "default_registry",
    "DEFAULT_CHECKS",
]
