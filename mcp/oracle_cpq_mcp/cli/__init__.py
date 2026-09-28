"""Installable maintainer CLI: ``oracle-cpq <subcommand>``."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    """Dispatch ``oracle-cpq`` subcommands."""
    parser = argparse.ArgumentParser(
        prog="oracle-cpq",
        description=(
            "Oracle CPQ MCP maintainer commands "
            "(migrate profiles, lint schemas, regenerate tool catalog)."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_migrate = sub.add_parser(
        "migrate-yaml",
        help="Migrate legacy .config/<id>.env to unified .config/<id>.yaml",
    )
    p_migrate.add_argument("customer_id")
    p_migrate.add_argument("--force", action="store_true")
    p_migrate.add_argument("--dry-run", action="store_true")

    p_catalog = sub.add_parser(
        "migrate-catalog",
        help="DEPRECATED: write legacy .catalog.yaml sidecar",
    )
    p_catalog.add_argument("customer_id")
    p_catalog.add_argument("--force", action="store_true")
    p_catalog.add_argument("--dry-run", action="store_true")

    sub.add_parser(
        "lint-schemas",
        help="Lint TOOL_CATALOG vs input models and Field descriptions",
    )

    p_gen = sub.add_parser(
        "generate-tool-catalog",
        help="Regenerate docs/TOOL_CATALOG.md from the live catalog",
    )
    p_gen.add_argument("--out", type=str, default=None)

    args = parser.parse_args(argv)

    if args.command == "migrate-yaml":
        from oracle_cpq_mcp.cli.migrate_yaml import main as migrate_main

        flags: list[str] = [args.customer_id]
        if args.force:
            flags.append("--force")
        if args.dry_run:
            flags.append("--dry-run")
        return migrate_main(flags)

    if args.command == "migrate-catalog":
        from oracle_cpq_mcp.cli.migrate_catalog import main as catalog_main

        flags = [args.customer_id]
        if args.force:
            flags.append("--force")
        if args.dry_run:
            flags.append("--dry-run")
        return catalog_main(flags)

    if args.command == "lint-schemas":
        from oracle_cpq_mcp.cli.lint_schemas import main as lint_main

        return lint_main([])

    if args.command == "generate-tool-catalog":
        from oracle_cpq_mcp.cli.generate_tool_catalog import main as gen_main

        gen_argv: list[str] = []
        if args.out:
            gen_argv.extend(["--out", args.out])
        return gen_main(gen_argv)

    parser.error(f"Unknown command: {args.command}")
    return 2


def run() -> None:
    """Console-script entry: exit with the subcommand return code."""
    raise SystemExit(main())


if __name__ == "__main__":
    run()
