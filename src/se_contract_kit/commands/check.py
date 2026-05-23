"""Check contract artifacts for internal consistency.

WHY: This is the repository's self-consistency gate. It loads the repository's
declarations, resolves its artifacts and dependencies into a ResolutionContext,
runs the kit's default check registry against it, and reports the result
deterministically.

It is not a domain verifier; it validates the contract source in this
repository, not external bundles. Manifest *schema* validation is delegated to
se-manifest-schema (run `se-manifest validate-manifest`); this command runs the
kit's own generic checks (resolved-artifact existence/parse, provide-or-consume,
vocabulary closure).
"""

import argparse
from pathlib import Path
import sys

from se_contract_kit.declarations.config import load_repo_config
from se_contract_kit.resolution.resolver import resolve_repo_config
from se_contract_kit.validation import default_registry, run_checks


def check_main(argv: list[str] | None = None) -> int:
    """Run repository-local contract consistency checks.

    Args:
        argv: Arguments after the ``check`` subcommand. ``None`` uses sys.argv.

    Returns:
        0 when all selected checks pass, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        prog="se-contract-kit check",
        description="Check se-contract-kit contract artifacts.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Run additional stricter checks (e.g. no-TODO in released artifacts).",
    )
    args = parser.parse_args(argv)

    # Load declarations -> resolve -> build context. Operational failures
    # (missing/unreadable manifest, unresolvable dependency) surface as
    # ContractKitError; let them propagate to a clear nonzero exit.
    repo_root = args.root if args.root is not None else Path.cwd()
    config = load_repo_config(repo_root=repo_root)
    context = resolve_repo_config(repo_root=repo_root, config=config)

    registry = default_registry()
    report = run_checks(registry=registry, context=context, strict=args.strict)

    if not report.passed:
        for failure in report.failures:
            location = f" [{failure.artifact_id}]" if failure.artifact_id else ""
            print(
                f"FAIL ({failure.check_id}){location}: {failure.message}",
                file=sys.stderr,
            )
        print(
            f"\n{len(report.failures)} failure(s) across "
            f"{len(report.results)} result(s); overall status "
            f"{report.overall_status.value}.",
            file=sys.stderr,
        )
        return report.exit_code

    print(
        f"OK: contract checks passed "
        f"({len(registry.checks)} checks, {len(report.results)} results)."
    )
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(check_main())
