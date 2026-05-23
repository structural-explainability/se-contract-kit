"""cli.py: Command-line interface."""

import argparse

from se_contract_kit.commands.check import check_main


def main(argv: list[str] | None = None) -> int:
    """Dispatch se-contract-kit subcommands.

    Args:
        argv: CLI arguments. ``None`` uses sys.argv.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(
        prog="se-contract-kit",
        description="Check contract artifacts for internal consistency.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    subparsers.add_parser(
        "check",
        help="Check contract artifacts for internal consistency.",
    )
    subparsers.add_parser(
        "validate-source",
        help="Alias for check: validate authored source artifacts.",
    )

    args, remaining = parser.parse_known_args(argv)

    # check, its alias, and the no-command default all route to the checker.
    if args.command in ("check", "validate-source") or args.command is None:
        return check_main(remaining)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
