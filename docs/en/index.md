# SE Contract Kit

Provides generic contract loading, resolution, and validation machinery for
Structural Explainability contract repositories.

## Contents

- [Architecture](./architecture.md)
- [Command Reference](./commands.md)
- [Contribution Workflow](./contribution-workflow.md)
- [Glossary](./glossary.md)

## What this repo owns

This repository owns reusable machinery for contract repositories:

- declaration loading
- dependency reference parsing
- artifact resolution
- authority-local resolution
- lockfile support
- generic validation checks
- validation result reporting

It does not own contract authority content or domain-specific contract content.
