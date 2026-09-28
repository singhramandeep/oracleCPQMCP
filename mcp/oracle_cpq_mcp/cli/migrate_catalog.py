"""Deprecated: write a legacy `.catalog.yaml` sidecar only."""

from __future__ import annotations

import argparse
import sys

from dotenv import dotenv_values

from oracle_cpq_mcp.core.catalog import (
    catalog_from_flat_env,
    catalog_path,
    dump_catalog_yaml,
)
from oracle_cpq_mcp.core.config import config_dir, profile_env_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "DEPRECATED: write .catalog.yaml sidecar. "
            "Prefer: oracle-cpq migrate-yaml <id>"
        )
    )
    parser.add_argument("customer_id")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print(
        "WARNING: migrate-catalog is deprecated. "
        "Use oracle-cpq migrate-yaml (or scripts/migrate_profile_yaml.py) "
        "for a single profile YAML.\n",
        file=sys.stderr,
    )
    _ = config_dir()
    env_path = profile_env_path(args.customer_id)
    if not env_path.is_file():
        raise SystemExit(f"Profile .env not found: {env_path}")
    raw = dotenv_values(env_path)
    catalog = catalog_from_flat_env(raw)
    out_path = catalog_path(args.customer_id)
    yaml_text = dump_catalog_yaml(catalog)
    print(f"Profile: {env_path}")
    print(f"Catalog: {out_path}")
    if out_path.is_file() and not args.force and not args.dry_run:
        raise SystemExit(f"Exists: {out_path} (use --force)")
    if args.dry_run:
        print(yaml_text)
    else:
        out_path.write_text(yaml_text, encoding="utf-8")
        print(f"Wrote {out_path}")
    return 0
