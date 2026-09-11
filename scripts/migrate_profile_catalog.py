"""Deprecated: use scripts/migrate_profile_yaml.py for unified profile YAML.

This script still writes a legacy `.catalog.yaml` sidecar only. Prefer migrating
to a single `.config/<id>.yaml` that includes secrets and catalog.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MCP_ROOT = _REPO_ROOT / "mcp"
if str(_MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(_MCP_ROOT))

# Preserve previous CLI for operators mid-migration.
from dotenv import dotenv_values  # noqa: E402

from oracle_cpq_mcp.core.catalog import (  # noqa: E402
    catalog_from_flat_env,
    catalog_path,
    dump_catalog_yaml,
)
from oracle_cpq_mcp.core.config import config_dir, profile_env_path  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "DEPRECATED: write .catalog.yaml sidecar. "
            "Prefer: python scripts/migrate_profile_yaml.py <id>"
        )
    )
    parser.add_argument("customer_id")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print(
        "WARNING: migrate_profile_catalog.py is deprecated. "
        "Use scripts/migrate_profile_yaml.py for a single profile YAML.\n",
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


if __name__ == "__main__":
    raise SystemExit(main())
