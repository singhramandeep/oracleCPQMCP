"""Tests for unified `.config/<id>.yaml` profiles."""

from __future__ import annotations

from pathlib import Path

import pytest

from oracle_cpq_mcp.core.config import (
    load_profile,
    resolve_custom_data_table_alias,
    update_profile_env_key,
)

PROFILE_YAML = """\
version: 1
customer_name: Yaml Corp
default_environment: dev
rest_api_version: v18
company_login_name: _host
read_only: true
refined_prompt: true
auto_save_refined_prompt: false
local_data_policy: ask
post_response_export: ask
customer_knowledge_file: acme.md
environments:
  dev:
    url: https://yaml-dev.example.com
    credentials:
      - username: yaml_user
        password: yaml_pass
  test:
    url: https://yaml-test.example.com
    credentials:
      - username: yaml_test
        password: yaml_test_pass
commerce_processes:
  - var_name: yaml_process
    alias: YAML Commerce
    enabled: true
  - var_name: off_proc
    alias: "Off Process"
    enabled: false
data_tables:
  - name: YamlTable
    alias: yaml table
metrics:
  QUOTES: From profile YAML
product_families:
  - var_name: laptop
    alias: Laptop Family
    enabled: true
    lines:
      - var_name: hp
        alias: HP Line
        enabled: true
        models:
          - var_name: elite840
            alias: Elite 840
            enabled: true
"""

LEGACY_ENV = """\
CUSTOMER_NAME=Legacy Corp
DEV_URL=https://legacy-dev.example.com
DEV_USERNAME=legacy_user
DEV_PASSWORD=legacy_pass
DEFAULT_ENVIRONMENT=dev
REST_API_VERSION=v18
COMMERCE_PROCESS_VAR_NAME=legacy_process
"""


@pytest.fixture()
def config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cfg = tmp_path / ".config"
    cfg.mkdir()
    monkeypatch.setenv("CPQ_CONFIG_DIR", str(cfg))
    monkeypatch.delenv("CPQ_ENVIRONMENT", raising=False)
    monkeypatch.delenv("CPQ_CUSTOMER_PROFILE", raising=False)
    monkeypatch.delenv("CPQ_CREDENTIAL_INDEX", raising=False)
    monkeypatch.delenv("CPQ_READ_ONLY", raising=False)
    monkeypatch.delenv("CPQ_REFINED_PROMPT", raising=False)
    monkeypatch.delenv("CPQ_AUTO_SAVE_REFINED_PROMPT", raising=False)
    monkeypatch.delenv("CPQ_POST_RESPONSE_EXPORT", raising=False)
    monkeypatch.delenv("CPQ_DEBUG_MODE", raising=False)
    monkeypatch.delenv("CPQ_LOCAL_DATA_POLICY", raising=False)
    monkeypatch.delenv("CPQ_HTTP_TIMEOUT", raising=False)
    return cfg


def test_load_unified_profile_yaml(config_dir: Path) -> None:
    (config_dir / "acme.yaml").write_text(PROFILE_YAML, encoding="utf-8")
    profile = load_profile("acme")
    assert profile.profile_file_kind == "yaml"
    assert profile.catalog_source == "profile_yaml"
    assert profile.customer_name == "Yaml Corp"
    assert profile.base_url == "https://yaml-dev.example.com"
    assert profile.username == "yaml_user"
    assert profile.commerce_process_var_names == ["yaml_process"]
    assert profile.commerce_process_aliases["yaml commerce"] == "yaml_process"
    assert profile.custom_data_table_names == ["YamlTable"]
    assert profile.metric_descriptions["QUOTES"] == "From profile YAML"
    assert profile.product_family_aliases["laptop family"] == "laptop"
    assert profile.product_line_aliases["hp line"] == "hp"
    assert profile.product_model_aliases["elite 840"] == "elite840"


def test_yaml_preferred_over_env(config_dir: Path) -> None:
    (config_dir / "acme.yaml").write_text(PROFILE_YAML, encoding="utf-8")
    (config_dir / "acme.env").write_text(LEGACY_ENV, encoding="utf-8")
    profile = load_profile("acme")
    assert profile.profile_file_kind == "yaml"
    assert profile.customer_name == "Yaml Corp"
    assert profile.username == "yaml_user"


def test_legacy_env_still_loads(config_dir: Path) -> None:
    (config_dir / "legacy.env").write_text(LEGACY_ENV, encoding="utf-8")
    profile = load_profile("legacy")
    assert profile.profile_file_kind == "env"
    assert profile.customer_name == "Legacy Corp"
    assert profile.commerce_process_var_name == "legacy_process"


def test_update_profile_yaml_writable_keys(config_dir: Path) -> None:
    path = config_dir / "acme.yaml"
    path.write_text(PROFILE_YAML, encoding="utf-8")
    update_profile_env_key("acme", "AUTO_SAVE_REFINED_PROMPT", "true")
    update_profile_env_key("acme", "LOCAL_DATA_POLICY", "prefer")
    update_profile_env_key("acme", "POST_RESPONSE_EXPORT", "always_excel")
    text = path.read_text(encoding="utf-8")
    assert "auto_save_refined_prompt: true" in text
    assert "local_data_policy: prefer" in text
    assert "post_response_export: always_excel" in text
    assert "yaml_pass" in text
    profile = load_profile("acme")
    assert profile.auto_save_refined_prompt is True
    assert profile.local_data_policy == "prefer"
    assert profile.post_response_export == "always_excel"


def test_host_override_read_only_on_yaml(config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (config_dir / "acme.yaml").write_text(PROFILE_YAML, encoding="utf-8")
    monkeypatch.setenv("CPQ_READ_ONLY", "false")
    profile = load_profile("acme")
    assert profile.read_only is False


def test_multi_data_tables_yaml_skips_disabled(config_dir: Path) -> None:
    yaml_text = """\
version: 1
customer_name: Multi Tables
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://multi-dev.example.com
    credentials:
      - username: u1
        password: p1
data_tables:
  - name: TableA
    alias: table a
    enabled: true
  - name: TableB
    alias: table b
    enabled: true
  - name: TableOff
    alias: table off
    enabled: false
"""
    (config_dir / "multi.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("multi")
    assert profile.custom_data_table_names == ["TableA", "TableB"]
    assert profile.custom_data_table_name == "TableA"
    assert profile.custom_data_table_aliases["table a"] == "TableA"
    assert profile.custom_data_table_aliases["table b"] == "TableB"
    assert "table off" not in profile.custom_data_table_aliases
    assert resolve_custom_data_table_alias(profile, "Table B") == "TableB"
    assert resolve_custom_data_table_alias(profile, "table off") is None


def test_disabled_environment_rejected(config_dir: Path) -> None:
    yaml_text = """\
version: 1
customer_name: Env Guard
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://guard-dev.example.com
    enabled: true
    credentials:
      - username: u1
        password: p1
  test:
    url: https://guard-test.example.com
    enabled: false
    credentials:
      - username: u2
        password: p2
"""
    (config_dir / "guard.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("guard", environment="dev")
    assert profile.environment == "dev"
    assert profile.base_url == "https://guard-dev.example.com"
    with pytest.raises(ValueError, match="environment 'test' is disabled"):
        load_profile("guard", environment="test")


def test_disabled_default_environment_rejected(config_dir: Path) -> None:
    yaml_text = """\
version: 1
customer_name: Bad Default
default_environment: prod
rest_api_version: v18
environments:
  prod:
    url: https://bad-prod.example.com
    enabled: false
    credentials:
      - username: u1
        password: p1
"""
    (config_dir / "baddefault.yaml").write_text(yaml_text, encoding="utf-8")
    with pytest.raises(ValueError, match="environment 'prod' is disabled"):
        load_profile("baddefault")


FUSION_YAML = """\
version: 1
customer_name: Fusion Corp
mode: fusion
default_environment: dev
rest_api_version: v19
environments:
  dev:
    url: https://fusion-dev.example.com
    oauth_token_url: https://idcs.example.com/oauth2/v1/token
    oauth_client_id: fusion-client
    oauth_client_secret: fusion-secret
    oauth_scope: urn:opc:resource:fusion:demo:cpq/
"""


def test_missing_mode_defaults_to_cpq(config_dir: Path) -> None:
    (config_dir / "acme.yaml").write_text(PROFILE_YAML, encoding="utf-8")
    profile = load_profile("acme")
    assert profile.mode == "cpq"
    assert profile.rest_base == "https://yaml-dev.example.com/rest/v18"


def test_standalone_mode_alias_defaults_to_cpq(config_dir: Path) -> None:
    yaml_text = PROFILE_YAML.replace(
        "customer_name: Yaml Corp\n",
        "customer_name: Yaml Corp\nmode: standalone\n",
        1,
    )
    (config_dir / "standalone.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("standalone")
    assert profile.mode == "cpq"
    assert profile.rest_base == "https://yaml-dev.example.com/rest/v18"
    assert "/cpq/rest/" not in profile.rest_base


def test_fusion_mode_loads_oauth_and_rest_base(config_dir: Path) -> None:
    (config_dir / "fusion.yaml").write_text(FUSION_YAML, encoding="utf-8")
    profile = load_profile("fusion")
    assert profile.mode == "fusion"
    assert profile.oauth_client_id == "fusion-client"
    assert profile.oauth_client_secret == "fusion-secret"
    assert profile.oauth_scope == "urn:opc:resource:fusion:demo:cpq/"
    assert profile.rest_base == "https://fusion-dev.example.com/cpq/rest/v19"
    assert profile.sanitize_secret == "fusion-secret"
    assert profile.credentials == []


def test_fusion_mode_missing_oauth_rejected(config_dir: Path) -> None:
    yaml_text = """\
version: 1
customer_name: Broken Fusion
mode: fusion
default_environment: dev
rest_api_version: v19
environments:
  dev:
    url: https://fusion-dev.example.com
"""
    (config_dir / "broken.yaml").write_text(yaml_text, encoding="utf-8")
    with pytest.raises(ValueError, match="mode=fusion requires"):
        load_profile("broken")


def test_profile_yaml_format_version_float(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.profile_yaml import (
        PROFILE_YAML_FORMAT_VERSION,
        CustomerProfileDocument,
        load_profile_document,
    )

    assert PROFILE_YAML_FORMAT_VERSION == 1.02
    assert CustomerProfileDocument.model_fields["version"].default == 1.02

    yaml_text = """\
version: 1.02
customer_name: Versioned
mode: cpq
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://ver-dev.example.com
    credentials:
      - username: u1
        password: p1
"""
    path = config_dir / "versioned.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    doc = load_profile_document(path)
    assert doc.version == 1.02
    assert doc.mode == "cpq"

    # Older integer / 1.01 versions still load (backward compatible).
    old = yaml_text.replace("version: 1.02", "version: 1", 1)
    path.write_text(old, encoding="utf-8")
    doc_old = load_profile_document(path)
    assert doc_old.version == 1.0

    mid = yaml_text.replace("version: 1.02", "version: 1.01", 1)
    path.write_text(mid, encoding="utf-8")
    assert load_profile_document(path).version == 1.01


def test_load_profile_accepts_format_version_float(config_dir: Path) -> None:
    """Regression: float format version must not break ProfileCatalog (int)."""
    yaml_text = """\
version: 1.02
customer_name: Format Ok
mode: cpq
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://ok-dev.example.com
    credentials:
      - username: u1
        password: p1
commerce_processes:
  - var_name: oraclecpqo
    alias: base
    enabled: true
"""
    (config_dir / "ok.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("ok")
    assert profile.customer_id == "ok"
    assert profile.mode == "cpq"
    assert profile.commerce_process_var_names == ["oraclecpqo"]


def test_fusion_skips_credentials_cpq_skips_oauth(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.profile_yaml import load_profile_document

    fusion = """\
version: 1.02
customer_name: Fusion Skip Creds
mode: fusion
default_environment: dev
rest_api_version: v19
environments:
  dev:
    url: https://fusion-dev.example.com
    oauth_token_url: https://idcs.example.com/oauth2/v1/token
    oauth_client_id: cid
    oauth_client_secret: csecret
    oauth_scope: urn:opc:resource:fusion:demo:cpq/
"""
    path = config_dir / "fskip.yaml"
    path.write_text(fusion, encoding="utf-8")
    doc = load_profile_document(path)
    assert doc.mode == "fusion"
    assert doc.environments["dev"].credentials == []
    profile = load_profile("fskip")
    assert profile.mode == "fusion"
    assert profile.credentials == []

    cpq = """\
version: 1.02
customer_name: Cpq Skip Oauth
mode: cpq
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://cpq-dev.example.com
    credentials:
      - username: u1
        password: p1
"""
    path = config_dir / "cskip.yaml"
    path.write_text(cpq, encoding="utf-8")
    doc = load_profile_document(path)
    assert doc.mode == "cpq"
    assert doc.environments["dev"].oauth_client_id is None
    assert load_profile("cskip").mode == "cpq"


def test_cpq_enabled_env_missing_credentials_rejected(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.profile_yaml import load_profile_document

    yaml_text = """\
version: 1.02
customer_name: Broken Cpq
mode: cpq
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://cpq-dev.example.com
    enabled: true
"""
    path = config_dir / "broken_cpq.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    with pytest.raises(ValueError, match="mode=cpq requires"):
        load_profile_document(path)
