# Glossary

## Contract kit

Reusable machinery for loading, resolving, and validating Structural
Explainability contract repositories.

## Declaration

Data a repository provides about itself through its manifest and contract
configuration.

## Resolution

The process of turning declarations into concrete dependencies, artifacts,
authorities, lockfile state, and run context.

## Authority-local resolution

The rule that artifacts provided by the current repository resolve locally, and
artifacts not provided locally resolve from the pinned authority dependency.

## Validation

The process of checking resolved contract state.

## Generic check

A check that applies without assuming a domain-specific artifact model.

## Domain-specific check

A check owned by a contract authority or domain repository because it depends on
that repository's contract content.
