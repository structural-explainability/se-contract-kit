"""Dependency and artifact resolution.

Resolution turns declarations into resolved artifacts and authorities.

Resolution must not import from se_contract_kit.validation.
It resolves contract state; it does not check contract state.

Module roles:
  dependencies.py
    Parse dependency references.

  artifacts.py
    Model declared and resolved artifacts.

  authorities.py
    Decide local-authority versus pinned-dependency authority.

  lockfile.py
    Persist resolved dependency and artifact state.

  context.py
    Hold the complete resolved run state.

  resolver.py
    Orchestrate the resolution process.
"""
