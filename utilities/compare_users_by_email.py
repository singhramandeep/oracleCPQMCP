"""Compare users across CPQ environments by email address."""

from __future__ import annotations

from oracle_cpq_mcp.core.config import load_profile
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.exporters.users_excel import fetch_all_users


def normalize_email(user: dict) -> str | None:
    email = user.get("email")
    if not email:
        return None
    if isinstance(email, dict):
        email = email.get("value") or email.get("displayValue")
    if email is None:
        return None
    normalized = str(email).strip().lower()
    return normalized or None


def status_display(user: dict) -> str:
    status = user.get("status")
    if isinstance(status, dict):
        return str(status.get("displayValue") or status.get("value") or "")
    return str(status or "")


def emails_for_env(env: str) -> tuple[list[dict], dict[str, list[dict]]]:
    client = CPQClient(load_profile(None, env))
    users = fetch_all_users(client, status_filter="all").items
    by_email: dict[str, list[dict]] = {}
    for user in users:
        email = normalize_email(user)
        if not email:
            continue
        by_email.setdefault(email, []).append(user)
    return users, by_email


def main() -> None:
    dev_users, dev_by_email = emails_for_env("dev")
    test_users, test_by_email = emails_for_env("test")

    dev_emails = set(dev_by_email)
    test_emails = set(test_by_email)
    both = sorted(dev_emails & test_emails)

    print(f"DEV total users: {len(dev_users)}")
    print(f"TEST total users: {len(test_users)}")
    print(f"DEV users with email: {len(dev_emails)}")
    print(f"TEST users with email: {len(test_emails)}")
    print(f"Users in BOTH (by email): {len(both)}")
    print("---")
    for email in both:
        dev_user = dev_by_email[email][0]
        test_user = test_by_email[email][0]
        print(
            f"{email} | "
            f"dev: {dev_user.get('login')} ({status_display(dev_user)}) | "
            f"test: {test_user.get('login')} ({status_display(test_user)})"
        )


if __name__ == "__main__":
    main()
