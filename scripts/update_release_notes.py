#!/usr/bin/env python3
"""Regenerate the git-backed Unreleased commit list in docs/RELEASE_NOTES.md.

Idempotent: rewrites only the block between <!-- git-commits --> markers.
Exit 0 if unchanged, 1 if the file was modified (pre-commit re-stage pattern).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

MARKER_START = "<!-- git-commits -->"
MARKER_END = "<!-- /git-commits -->"

HEADER_TEMPLATE = """# Release notes

Changelog for the Oracle CPQ MCP server. Format inspired by [Keep a Changelog](https://keepachangelog.com/).

## How to refresh

```bash
python scripts/update_release_notes.py
```

The script regenerates the git-backed list under `## Unreleased` from `git log` (idempotent). A **pre-commit** hook runs the same command; if the file changes, re-stage `docs/RELEASE_NOTES.md` and commit again.

## How to cut a versioned release

1. Bump `version` in [`pyproject.toml`](../pyproject.toml).
2. Move the current Unreleased commit bullets (and any Pending notes you want to keep) under a new heading such as `## [0.2.0] - YYYY-MM-DD`.
3. Leave a fresh Unreleased section and keep the standalone git-commits HTML comment markers for future commits.
4. Commit and optionally tag: `git tag v0.2.0`.

## Unreleased

<!-- git-commits -->
<!-- /git-commits -->
"""


def repo_root() -> Path:
    out = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stderr=subprocess.STDOUT,
    )
    return Path(out.strip())


def git_commits(root: Path) -> list[tuple[str, str]]:
    """Return (shortsha, subject) newest first, skipping merges."""
    out = subprocess.check_output(
        [
            "git",
            "log",
            "--no-merges",
            "--pretty=format:%h%x00%s",
        ],
        cwd=root,
        text=True,
        stderr=subprocess.STDOUT,
    )
    commits: list[tuple[str, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line or "\x00" not in line:
            continue
        sha, subject = line.split("\x00", 1)
        commits.append((sha.strip(), subject.strip()))
    return commits


def format_commit_block(commits: list[tuple[str, str]]) -> str:
    if not commits:
        return f"{MARKER_START}\n{MARKER_END}\n"
    lines = [MARKER_START]
    for sha, subject in commits:
        lines.append(f"- `{sha}` {subject}")
    lines.append(MARKER_END)
    return "\n".join(lines) + "\n"


def ensure_markers(text: str) -> str:
    # Only count markers that sit alone on a line (avoids prose mentions).
    if re.search(rf"(?m)^{re.escape(MARKER_START)}$", text) and re.search(
        rf"(?m)^{re.escape(MARKER_END)}$", text
    ):
        return text
    if "## Unreleased" in text:
        return text.rstrip() + f"\n\n{MARKER_START}\n{MARKER_END}\n"
    return HEADER_TEMPLATE


def replace_commit_block(text: str, new_block: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(MARKER_START)}$"
        r".*?"
        rf"^{re.escape(MARKER_END)}$\n?",
        re.MULTILINE | re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit(
            f"Could not find standalone {MARKER_START} ... {MARKER_END} in release notes"
        )
    return pattern.sub(new_block.rstrip("\n") + "\n", text, count=1)


def main() -> int:
    root = repo_root()
    path = root / "docs" / "RELEASE_NOTES.md"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(HEADER_TEMPLATE, encoding="utf-8")
        print(f"Created {path.relative_to(root)}")

    original = path.read_text(encoding="utf-8")
    text = ensure_markers(original)
    block = format_commit_block(git_commits(root))
    updated = replace_commit_block(text, block)

    if updated == original:
        print("docs/RELEASE_NOTES.md already up to date")
        return 0

    path.write_text(updated, encoding="utf-8")
    print("Updated docs/RELEASE_NOTES.md from git log")
    return 1


if __name__ == "__main__":
    sys.exit(main())
