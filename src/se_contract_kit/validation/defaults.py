"""Default check registry: the kit's fixed set of generic checks.

This is the single place that knows which checks the kit ships. registry.py
is pure machinery (the Check and CheckRegistry types) and imports nothing from
checks; the individual checks import the Check type from registry. defaults.py
sits above both, importing the machinery and the checks to assemble the default
registry. The dependency arrow is one-way:

    registry  <-  checks  <-  defaults

so there is no cycle, and registry/checks can be reasoned about without knowing
the default set.

Consuming repos build their own registry by extending this one:

    from se_contract_kit.validation.defaults import default_registry
    registry = default_registry().extend(ar_conformance_check, ar_records_check)

The defaults are never edited by a consumer; extend() returns a new registry.

Default order (deterministic, foundational first):
  1. structural.source           resolved artifacts exist and parse
  2. structural.schemas          schema-kind artifacts are valid JSON Schema
  3. authority                   provide-or-consume, no local redefinition
  4. manifest-schema             manifest contract section conforms to schema
  5. constraints.closure         domain mappings close over resolved vocabulary
  6. structural.strict.no-todo   no unfinished-work markers (strict-only)
"""

from se_contract_kit.validation.checks.authority import CHECK as AUTHORITY_CHECK
from se_contract_kit.validation.checks.constraints import CHECK as CONSTRAINTS_CHECK
from se_contract_kit.validation.checks.structural.schemas import (
    CHECK as STRUCTURAL_SCHEMAS_CHECK,
)
from se_contract_kit.validation.checks.structural.source import (
    CHECK as STRUCTURAL_SOURCE_CHECK,
)
from se_contract_kit.validation.checks.structural.strict import (
    CHECK as STRUCTURAL_STRICT_CHECK,
)
from se_contract_kit.validation.registry import Check, CheckRegistry

__all__ = ["DEFAULT_CHECKS", "default_registry"]

# WHY: ordered foundational-first. structural.source runs first because every
# later check assumes its artifacts exist and parse; structural.strict runs
# last because it is strict-only and least likely to gate routine validation.
DEFAULT_CHECKS: tuple[Check, ...] = (
    STRUCTURAL_SOURCE_CHECK,
    STRUCTURAL_SCHEMAS_CHECK,
    AUTHORITY_CHECK,
    CONSTRAINTS_CHECK,
    STRUCTURAL_STRICT_CHECK,
)


def default_registry() -> CheckRegistry:
    """Return the kit's default registry of generic checks.

    Returns a fresh CheckRegistry each call. Consumers extend it to add
    repo-specific checks; the kit's defaults are never mutated.
    """
    return CheckRegistry(checks=DEFAULT_CHECKS)
