"""Unit tests for local data/ snapshot store and policy helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet, load_profile
from oracle_cpq_mcp.core.local_data import (
    list_snapshots,
    load_snapshot_summary,
    parse_local_data_policy,
    persist_bml_functions_snapshot,
    persist_bml_zip_snapshot,
    persist_users_snapshot,
    sanitize_for_disk,
)


def _profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="acme",
        environment="dev",
        base_url="https://dev.example.com",
        rest_version="v18",
        credentials=[CredentialSet(username="u", password="p")],
        local_data_policy="ask",
    )


def test_parse_local_data_policy() -> None:
    assert parse_local_data_policy(None) == "prefer"
    assert parse_local_data_policy("prefer") == "prefer"
    assert parse_local_data_policy("ask") == "ask"
    assert parse_local_data_policy("NEVER") == "never"
    assert parse_local_data_policy("yes") == "prefer"
    assert parse_local_data_policy("true") == "prefer"
    with pytest.raises(ValueError):
        parse_local_data_policy("sometimes")


def test_parse_post_response_export_aliases() -> None:
    from oracle_cpq_mcp.core.config import _resolve_post_response_export

    assert _resolve_post_response_export({}) == "always_excel"
    assert _resolve_post_response_export({"POST_RESPONSE_EXPORT": "yes"}) == "always_excel"
    assert _resolve_post_response_export({"POST_RESPONSE_EXPORT": "ask"}) == "ask"
    assert (
        _resolve_post_response_export({"POST_RESPONSE_EXPORT": "never"}) == "never"
    )


def test_sanitize_strips_secrets() -> None:
    cleaned = sanitize_for_disk(
        {"login": "a", "password": "secret", "nested": {"access_token": "x", "ok": 1}}
    )
    assert cleaned == {"login": "a", "nested": {"ok": 1}}


def test_persist_users_and_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CPQ_LOCAL_DATA_DIR", str(tmp_path))
    profile = _profile()
    result = persist_users_snapshot(
        profile,
        [{"partyNumber": "1", "login": "alice"}],
        b"PK\x03\x04fake",
        source_tool="sync_users_local",
        filters={"status_filter": "active"},
    )
    assert Path(result["paths"]["users_json"]).is_file()
    assert Path(result["paths"]["users_xlsx"]).is_file()
    snaps = list_snapshots(profile)
    assert len(snaps) == 1
    assert snaps[0]["domain"] == "users"
    assert snaps[0]["item_count"] == 1
    summary = load_snapshot_summary(profile, "users")
    assert summary["available"] is True
    assert "users_json" in summary["files"]
    assert "payloads" not in summary
    with_payload = load_snapshot_summary(profile, "users", include_payload=True)
    assert with_payload["payloads"]["users_json"]["count"] == 1


def test_persist_bml_writes_bml_and_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CPQ_LOCAL_DATA_DIR", str(tmp_path))
    profile = _profile()
    functions = [
        {
            "namespace": "util",
            "variableName": "helloWorld",
            "scriptText": "return \"hi\";",
            "resourceId": "util.helloWorld",
        }
    ]
    result = persist_bml_functions_snapshot(
        profile,
        functions,
        source_tool="sync_bml_local",
    )
    root = Path(result["snapshot_dir"])
    bml = root / "functions" / "util" / "helloWorld.bml"
    meta = root / "functions" / "util" / "helloWorld.json"
    assert bml.is_file()
    assert "return" in bml.read_text(encoding="utf-8")
    assert meta.is_file()
    assert "scriptText" not in meta.read_text(encoding="utf-8")


def _make_zip_bytes(members: dict[str, bytes]) -> bytes:
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_persist_bml_zip_extracts_site_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CPQ_LOCAL_DATA_DIR", str(tmp_path))
    profile = _profile()
    zip_bytes = _make_zip_bytes(
        {
            "a/b/c.bml": b'return "ok";\n',
            "a/meta.json": b'{"k":1}\n',
        }
    )
    result = persist_bml_zip_snapshot(
        profile,
        zip_bytes,
        source_tool="get_all_bml_code",
        filename="acme_dev_bml_export.zip",
    )
    root = Path(result["snapshot_dir"])
    zip_path = Path(result["paths"]["bml_zip"])
    site_dir = Path(result["paths"]["site_dir"])
    assert zip_path.is_file()
    assert site_dir == root / "site"
    extracted = site_dir / "a" / "b" / "c.bml"
    assert extracted.is_file()
    assert 'return "ok"' in extracted.read_text(encoding="utf-8")
    assert (site_dir / "a" / "meta.json").is_file()
    assert result["item_count"] == 2


def test_persist_bml_zip_rejects_zip_slip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CPQ_LOCAL_DATA_DIR", str(tmp_path))
    profile = _profile()
    zip_bytes = _make_zip_bytes(
        {
            "safe/ok.bml": b"safe\n",
            "../escape.txt": b"pwned\n",
            "nested/../../outside.txt": b"nope\n",
        }
    )
    result = persist_bml_zip_snapshot(
        profile,
        zip_bytes,
        source_tool="get_all_bml_code",
        filename="slip.zip",
    )
    root = Path(result["snapshot_dir"])
    site = root / "site"
    assert (site / "safe" / "ok.bml").is_file()
    assert not (tmp_path / "escape.txt").exists()
    assert not (root / "escape.txt").exists()
    assert not (root / "outside.txt").exists()
    assert not (site / "outside.txt").exists()
    assert result["item_count"] == 1


def test_fs_path_adds_windows_extended_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    from oracle_cpq_mcp.core.local_data import _fs_path

    monkeypatch.setattr("oracle_cpq_mcp.core.local_data.os.name", "nt")
    longish = Path("C:/Users/RamandeepSingh/workspaces/oracleCPQMCP/data") / (
        "a" * 50
    )
    prefixed = str(_fs_path(longish))
    assert prefixed.startswith("\\\\?\\")
    unc = Path("\\\\server\\share\\folder\\file.txt")
    assert str(_fs_path(unc)).startswith("\\\\?\\UNC\\")


def test_persist_bml_zip_extracts_deep_windows_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deep Commerce BML trees exceed classic Windows MAX_PATH (~260)."""
    monkeypatch.setenv("CPQ_LOCAL_DATA_DIR", str(tmp_path))
    profile = _profile()
    deep_rel = "/".join(
        [
            "commerceAndDocuments",
            "processDefinition",
            "terexMPCommerceProcess",
            "transaction",
            "libraries",
            "gEtTheCurrentStepBeforeFixingTheQuoteVisibilityIssue_c",
            "gEtTheCurrentStepBeforeFixingTheQuoteVisibilityIssue_c-meta.json",
        ]
    )
    zip_bytes = _make_zip_bytes({deep_rel: b'{"ok":true}\n'})
    result = persist_bml_zip_snapshot(
        profile,
        zip_bytes,
        source_tool="start_bml_site_export",
        filename="deep.zip",
    )
    site = Path(result["paths"]["site_dir"])
    extracted = site.joinpath(*deep_rel.split("/"))
    assert extracted.is_file()
    assert extracted.read_text(encoding="utf-8").startswith("{")
    assert result["item_count"] == 1


def test_load_profile_local_data_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / ".config"
    cfg.mkdir()
    (cfg / "acme.env").write_text(
        "CUSTOMER_NAME=Acme\nDEFAULT_ENVIRONMENT=dev\n"
        "DEV_URL=https://dev.example.com\n"
        "DEV_USERNAME=u\nDEV_PASSWORD=p\n"
        "LOCAL_DATA_POLICY=prefer\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CPQ_CONFIG_DIR", str(cfg))
    monkeypatch.delenv("CPQ_LOCAL_DATA_POLICY", raising=False)
    monkeypatch.setenv("CPQ_CUSTOMER_PROFILE", "acme")
    profile = load_profile()
    assert profile.local_data_policy == "prefer"
    monkeypatch.setenv("CPQ_LOCAL_DATA_POLICY", "never")
    profile2 = load_profile()
    assert profile2.local_data_policy == "never"
