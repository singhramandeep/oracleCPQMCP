"""Rich TUI smoke-test CLI for Oracle CPQ connectivity."""

from __future__ import annotations

import argparse
import sys

from dataclasses import dataclass

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from oracle_cpq_mcp.core.config import connection_mode_message, load_profile
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.errors import CPQAPIError

console = Console()


@dataclass(slots=True)
class CheckResult:
    label: str
    ok: bool
    detail: str


def _run_check(label: str, fn) -> CheckResult:
    try:
        result = fn()
        count = ""
        if isinstance(result, dict) and "count" in result:
            count = f" ({result['count']} items)"
        elif isinstance(result, dict) and "items" in result:
            count = f" ({len(result['items'])} items)"
        return CheckResult(label=label, ok=True, detail=f"OK{count}")
    except CPQAPIError as exc:
        tool_error = exc.to_tool_error()
        parts = [tool_error.get("message", str(exc))]
        if code := tool_error.get("code"):
            parts.append(f"code: {code}")
        if hint := tool_error.get("hint"):
            parts.append(f"hint: {hint}")
        details = tool_error.get("details") or {}
        if details.get("curl"):
            parts.append(f"curl: {details['curl']}")
        if details.get("response") is not None:
            parts.append(f"response: {details['response']}")
        return CheckResult(label=label, ok=False, detail=" | ".join(parts))
    except Exception as exc:  # noqa: BLE001 — surface unexpected errors in TUI
        return CheckResult(label=label, ok=False, detail=str(exc))


def main() -> None:
    parser = argparse.ArgumentParser(description="Oracle CPQ MCP smoke test")
    parser.add_argument("--profile", default=None, help="Customer profile id (e.g. mycompany)")
    parser.add_argument("--env", choices=["dev", "test", "prod"], default=None)
    args = parser.parse_args()

    console.print(
        Panel.fit(
            "[bold cyan]Oracle CPQ MCP[/] - connectivity smoke test",
            border_style="cyan",
            box=box.ASCII,
        )
    )

    profile_id = args.profile or Prompt.ask(
        "Customer profile",
        default="mycompany",
    )

    console.print("Loading profile...")
    try:
        profile = load_profile(profile_id, args.env)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Config error:[/] {exc}")
        sys.exit(1)
    console.print("[green]Profile loaded[/]")
    console.print(connection_mode_message(profile.read_only))

    info = Table(show_header=False, box=None)
    info.add_row("Customer", profile.customer_name)
    info.add_row("Profile", profile.customer_id)
    info.add_row("Environment", profile.environment)
    info.add_row("Base URL", profile.base_url)
    info.add_row("REST version", profile.rest_version)
    info.add_row("Company", profile.company_login_name)
    info.add_row("Read only", "true" if profile.read_only else "false")
    console.print(info)

    client = CPQClient(profile)
    checks = [
        ("List users", lambda: client.get("/users", params={"limit": 5})),
        (
            "List groups",
            lambda: client.get(
                f"/companies/{profile.company_login_name}/groups",
                params={"limit": 5},
            ),
        ),
        ("List data tables", lambda: client.get("/datatables", params={"limit": 5})),
    ]
    for table in profile.custom_data_table_names:
        checks.append(
            (
                f"Get table '{table}'",
                lambda table_name=table: client.get(f"/datatables/{table_name}"),
            )
        )

    results = Table(title="Smoke checks", show_lines=True, box=box.ASCII)
    results.add_column("Check", style="cyan")
    results.add_column("Status")
    results.add_column("Detail")
    check_results: list[CheckResult] = []

    for label, fn in checks:
        console.print(f"Running: {label}")
        result = _run_check(label, fn)
        check_results.append(result)
        style = "green" if result.ok else "red"
        results.add_row(
            result.label,
            f"[{style}]{'PASS' if result.ok else 'FAIL'}[/]",
            result.detail,
        )

    console.print(results)

    if any(not result.ok for result in check_results):
        sys.exit(1)


if __name__ == "__main__":
    main()
