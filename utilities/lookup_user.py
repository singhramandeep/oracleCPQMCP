"""Lookup a CPQ user by login."""

from __future__ import annotations

import json
import sys

from oracle_cpq_mcp.core.config import load_profile
from oracle_cpq_mcp.core.cpq_client import CPQClient


def main() -> None:
    login = sys.argv[1] if len(sys.argv) > 1 else "hmohammed"
    client = CPQClient(load_profile())

    for q in (
        f"{{'login':{{'$eq':'{login}'}}}}",
        f"{{'login':{{'$like':'%{login}%'}}}}",
    ):
        result = client.get("/users", params={"q": q, "limit": 10})
        items = result.get("items", [])
        if items:
            break
    else:
        print(json.dumps({"error": f"User '{login}' not found"}, indent=2))
        sys.exit(1)

    party = items[0]["partyNumber"]
    full = client.get(f"/users/{party}")
    groups = client.get(f"/users/{party}/groups")
    print(json.dumps({"user": full, "groups": groups}, indent=2))


if __name__ == "__main__":
    main()
