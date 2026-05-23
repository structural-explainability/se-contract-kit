# DECISIONS

<!-- markdownlint-disable MD024 -->

Architectural decisions.
Records rationale, not vocabulary.

This document records the load-bearing choices.
Each decision is numbered, dated, and stated.

A decision recorded here is stable.
Reversing a decision is a breaking change to the contract.
The document is append-only by convention:
new decisions are added at the bottom, and decision numbers are never
renumbered.

A decision records why a choice was made.
It does not recreate any artifacts.

## Amendments to existing decisions

Refining or clarifying a decision is non-breaking and is recorded as an
amendment to that decision's entry, not as a new entry.

---

## CK-D-001: Own generic machinery, not contract content

### Date Recorded

2026-05

### Decision

Owns reusable machinery for loading, resolving, and validating
Structural Explainability contract repositories.

Does not own domain-specific contract content.

---

## CK-D-002: Keep manifest validation in se-manifest-schema

### Date Recorded

2026-05

### Decision

Repository manifest structure and manifest validation are owned by
`se-manifest-schema`.
`se-contract-kit` does not duplicate manifest validation logic.

---

## CK-D-003: Preserve one-way stage dependencies

### Date Recorded

2026-05

### Decision

Source is organized by dependency stage:

```text
base -> declarations -> resolution -> validation -> cli
```

Earlier stages must not import later stages.

---

## CK-D-004: Keep resolution separate from validation

### Date Recorded

2026-05

### Decision

Resolution turns declarations into resolved dependencies, artifacts, authorities,
lockfile state, and run context.
Resolution must not import from validation.
Validation checks resolved contract state.

---

## CK-D-005: Use the registry as the extension point

### Date Recorded

2026-05

### Decision

Contract authority and domain repositories add repository-specific checks through
the registry without modifying the kit.

---

<!-- markdownlint-enable MD024 -->
