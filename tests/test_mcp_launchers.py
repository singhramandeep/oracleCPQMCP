"""Tests for cross-platform MCP launcher scripts and example configs."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_launcher_scripts_exist() -> None:
    assert (REPO_ROOT / "scripts" / "mcp-server.sh").is_file()
    assert (REPO_ROOT / "scripts" / "mcp-server.cmd").is_file()


def test_launchers_invoke_oracle_cpq_mcp_module() -> None:
    sh = (REPO_ROOT / "scripts" / "mcp-server.sh").read_text(encoding="utf-8")
    cmd = (REPO_ROOT / "scripts" / "mcp-server.cmd").read_text(encoding="utf-8")
    assert "-m oracle_cpq_mcp" in sh
    assert "-m oracle_cpq_mcp" in cmd


def test_launchers_reference_venv_python() -> None:
    sh = (REPO_ROOT / "scripts" / "mcp-server.sh").read_text(encoding="utf-8")
    cmd = (REPO_ROOT / "scripts" / "mcp-server.cmd").read_text(encoding="utf-8")
    assert ".venv/bin/python" in sh
    assert ".venv\\Scripts\\python.exe" in cmd


def test_cursor_examples_use_launchers_not_direct_python() -> None:
    for name in ("mcp.json.example", "mcp.json.unix.example"):
        payload = json.loads((REPO_ROOT / ".cursor" / name).read_text(encoding="utf-8"))
        server = payload["mcpServers"]["oracle-cpq"]
        assert "mcp-server" in server["command"]
        assert server["args"] == []
        assert "Scripts/python.exe" not in server["command"]
        assert "/bin/python" not in server["command"]


def test_vscode_examples_use_launchers() -> None:
    for name in ("mcp.json.example", "mcp.json.unix.example"):
        payload = json.loads((REPO_ROOT / ".vscode" / name).read_text(encoding="utf-8"))
        server = payload["servers"]["oracle-cpq"]
        assert "mcp-server" in server["command"]
        assert server["args"] == []


def test_agents_example_uses_launcher() -> None:
    payload = json.loads(
        (REPO_ROOT / ".agents" / "mcp_config.example.json").read_text(encoding="utf-8")
    )
    server = payload["mcpServers"]["oracle-cpq"]
    assert "mcp-server.cmd" in server["command"]
    assert server["args"] == []


def test_committed_cursor_mcp_json_is_gitignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".cursor/mcp.json" in gitignore
