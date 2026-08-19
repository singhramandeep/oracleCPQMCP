"""One-off helper: count users matching an email substring."""

from __future__ import annotations

import sys

from oracle_cpq_mcp.core.config import load_profile
from oracle_cpq_mcp.core.cpq_client import CPQClient


def main() -> None:
    needle = sys.argv[1] if len(sys.argv) > 1 else "@example.com"
    client = CPQClient(load_profile())
    matched: list[dict] = []
    offset = 0
    limit = 100
    total = None

    while True:
        response = client.get(
            "/users",
            params={"limit": limit, "offset": offset, "totalResults": "true"},
        )
        if total is None:
            total = response.get("totalResults") or response.get("count", 0)

        for user in response.get("items", []):
            email = user.get("email") or ""
            if needle.lower() in email.lower():
                matched.append(
                    {
                        "login": user.get("login"),
                        "email": email,
                        "partyNumber": user.get("partyNumber"),
                    }
                )

        if not response.get("hasMore", False):
            break
        offset += limit

    print(f"total_users={total}")
    print(f"match_count={len(matched)}")
    print(f"needle={needle}")
    for user in matched:
        print(f"  {user['login']}: {user['email']}")


if __name__ == "__main__":
    main()
