"""Tests for Prompt Studio probe/auto-start helper."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from oracle_cpq_mcp.core import prompt_studio_process as psp


def test_resolve_port_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CPQ_PROMPT_STUDIO_PORT", raising=False)
    assert psp.resolve_port() == 8765


def test_resolve_port_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CPQ_PROMPT_STUDIO_PORT", "9001")
    assert psp.resolve_port() == 9001


def test_resolve_port_invalid_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CPQ_PROMPT_STUDIO_PORT", "nope")
    assert psp.resolve_port() == 8765


def test_ensure_already_running_skips_spawn(tmp_path: Path) -> None:
    calls: list[str] = []

    def probe(**_kwargs: object) -> bool:
        return True

    def spawn(_root: Path) -> SimpleNamespace:
        calls.append("spawn")
        return SimpleNamespace(pid=1)

    result = psp.ensure_prompt_studio(
        root=tmp_path,
        probe_fn=probe,
        spawn_fn=spawn,
    )
    assert result["running"] is True
    assert result["started"] is False
    assert result["url"] == "http://127.0.0.1:8765"
    assert calls == []


def test_ensure_starts_when_down_then_healthy(tmp_path: Path) -> None:
    state = {"n": 0}

    def probe(**_kwargs: object) -> bool:
        state["n"] += 1
        return state["n"] > 1

    def spawn(_root: Path) -> SimpleNamespace:
        return SimpleNamespace(pid=4242)

    result = psp.ensure_prompt_studio(
        root=tmp_path,
        probe_fn=probe,
        spawn_fn=spawn,
        poll_timeout_s=2.0,
        poll_interval_s=0.01,
    )
    assert result["running"] is True
    assert result["started"] is True
    assert result["pid"] == 4242
    assert "4242" in result["message"] or result["url"].startswith("http://")


def test_ensure_start_timeout_returns_commands(tmp_path: Path) -> None:
    def probe(**_kwargs: object) -> bool:
        return False

    def spawn(_root: Path) -> SimpleNamespace:
        return SimpleNamespace(pid=99)

    result = psp.ensure_prompt_studio(
        root=tmp_path,
        probe_fn=probe,
        spawn_fn=spawn,
        poll_timeout_s=0.05,
        poll_interval_s=0.01,
    )
    assert result["running"] is False
    assert result["started"] is False
    assert result["pid"] == 99
    assert "activation_commands" in result
    assert "apps.prompt_studio" in result["activation_commands"]["powershell"]
    assert result["error"]


def test_ensure_spawn_oserror_returns_commands(tmp_path: Path) -> None:
    def probe(**_kwargs: object) -> bool:
        return False

    def spawn(_root: Path) -> SimpleNamespace:
        raise OSError("boom")

    result = psp.ensure_prompt_studio(
        root=tmp_path,
        probe_fn=probe,
        spawn_fn=spawn,
    )
    assert result["running"] is False
    assert result["started"] is False
    assert "boom" in result["error"]
    assert "pip install" in result["activation_commands"]["powershell"]


def test_ensure_custom_port(tmp_path: Path) -> None:
    def probe(*, host: str, port: int, **_kwargs: object) -> bool:
        assert host == "127.0.0.1"
        assert port == 9001
        return True

    result = psp.ensure_prompt_studio(
        root=tmp_path,
        port=9001,
        probe_fn=probe,
        spawn_fn=lambda _r: SimpleNamespace(pid=1),
    )
    assert result["port"] == 9001
    assert result["url"] == "http://127.0.0.1:9001"


def test_activation_commands_include_restart() -> None:
    cmds = psp.activation_commands()
    assert "restart" in cmds["powershell"]
    assert "restart" in cmds["unix"]
    assert cmds["restart"].endswith("restart")
    assert "restart-prompt-studio" in cmds["restart_script"]


def test_local_addr_matches_port() -> None:
    assert psp._local_addr_matches_port("127.0.0.1:8765", 8765)
    assert psp._local_addr_matches_port("0.0.0.0:8765", 8765)
    assert psp._local_addr_matches_port("[::]:8765", 8765)
    assert not psp._local_addr_matches_port("127.0.0.1:8766", 8765)


def test_stop_prompt_studio_no_listeners(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(psp, "list_pids_listening_on_port", lambda _port: [])
    result = psp.stop_prompt_studio(port=8765)
    assert result["stopped"] == []
    assert result["already_stopped"] is True
    assert result["port"] == 8765


def test_stop_prompt_studio_kills_pids(monkeypatch: pytest.MonkeyPatch) -> None:
    killed: list[int] = []

    monkeypatch.setattr(psp, "list_pids_listening_on_port", lambda _port: [111, 222])
    monkeypatch.setattr(psp, "_kill_pid", lambda pid: killed.append(pid) or True)

    result = psp.stop_prompt_studio(port=8765)
    assert result["stopped"] == [111, 222]
    assert result["failed"] == []
    assert result["already_stopped"] is False
    assert killed == [111, 222]


def test_stop_prompt_studio_reports_kill_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def kill(pid: int) -> bool:
        return pid != 222

    monkeypatch.setattr(psp, "list_pids_listening_on_port", lambda _port: [111, 222])
    monkeypatch.setattr(psp, "_kill_pid", kill)

    result = psp.stop_prompt_studio(port=8765)
    assert result["stopped"] == [111]
    assert result["failed"] == [222]
