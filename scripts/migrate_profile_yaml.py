"""Migrate a legacy `.config/<id>.env` into a unified `.config/<id>.yaml`.

Writes secrets, flags, commerce/tables/metrics, and product families into one
gitignored YAML file. Does not delete the `.env` — review and remove it after
verifying MCP loads the YAML.

Usage:
  python scripts/migrate_profile_yaml.py mycompany
  python scripts/migrate_profile_yaml.py mycompany --force
  python scripts/migrate_profile_yaml.py mycompany --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import dotenv_values

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MCP_ROOT = _REPO_ROOT / "mcp"
if str(_MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(_MCP_ROOT))

from oracle_cpq_mcp.core.config import (  # noqa: E402
    config_dir,
    profile_env_path,
    profile_yaml_path,
)
from oracle_cpq_mcp.core.profile_yaml import (  # noqa: E402
    dump_profile_yaml,
    profile_document_from_flat_env,
)


def migrate(
    customer_id: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> Path:
    env_path = profile_env_path(customer_id)
    if not env_path.is_file():
        raise SystemExit(f"Legacy profile .env not found: {env_path}")

    raw = dotenv_values(env_path)
    document = profile_document_from_flat_env(raw)
    out_path = profile_yaml_path(customer_id)
    yaml_text = dump_profile_yaml(document)

    print(f"Source:  {env_path}")
    print(f"Target:  {out_path}")
    print(
        f"Extracted: envs={sorted(document.environments)} "
        f"commerce={len(document.commerce_processes)} "
        f"tables={len(document.data_tables)} metrics={len(document.metrics)} "
        f"families={len(document.product_families)}"
    )

    if out_path.is_file() and not force and not dry_run:
        raise SystemExit(
            f"Profile YAML already exists: {out_path}\n"
            "Pass --force to overwrite, or --dry-run to preview."
        )

    if dry_run:
        print("--- profile.yaml (dry-run) ---")
        print(yaml_text)
    else:
        out_path.write_text(yaml_text, encoding="utf-8")
        print(f"Wrote {out_path}")

    print(
        "Next: reload MCP (CPQ_CUSTOMER_PROFILE still = profile id). "
        "When verified, delete the legacy .env (and any .catalog.yaml)."
    )
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Migrate legacy .env into unified .config/<id>.yaml"
    )
    parser.add_argument("customer_id", help="Profile id (stem of .config/<id>.env)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing .yaml",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print YAML without writing",
    )
    args = parser.parse_args(argv)
    _ = config_dir()
    migrate(args.customer_id, force=args.force, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
