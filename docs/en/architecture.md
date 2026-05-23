# Architecture

`se-contract-kit` is organized by dependency stage:

```text
base -> declarations -> resolution -> validation -> cli
```

## Base

Dependency-free utilities for errors, file IO, JSON, and paths.

## Declarations

Loads repository manifest and contract declarations.

## Resolution

Resolves dependencies, artifacts, authorities, lockfiles, and run context.

Resolution does not check contract state.

## Validation

Runs generic contract checks against resolved contract state.

Validation does not resolve contract state.

## CLI

Provides the command-line entry point.
