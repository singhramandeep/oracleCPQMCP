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
    monkeypatch.delenv("CPQ_INCLUDE_REFINED_PROMPT_IN_DOCUMENTS", raising=False)
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
    assert profile.include_refined_prompt_in_documents is True


def test_yaml_include_refined_prompt_in_documents_false(
    config_dir: Path,
) -> None:
    yaml_text = PROFILE_YAML.replace(
        "auto_save_refined_prompt: false",
        "auto_save_refined_prompt: false\ninclude_refined_prompt_in_documents: false",
        1,
    )
    (config_dir / "acme.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("acme")
    assert profile.include_refined_prompt_in_documents is False


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
cpq_mode: fusion
fusion_enabled: true
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


def test_missing_cpq_mode_defaults_to_standalone(config_dir: Path) -> None:
    (config_dir / "acme.yaml").write_text(PROFILE_YAML, encoding="utf-8")
    profile = load_profile("acme")
    assert profile.cpq_mode == "standalone"
    assert profile.fusion_enabled is False
    assert profile.uses_fusion is False
    assert profile.rest_base == "https://yaml-dev.example.com/rest/v18"


def test_standalone_cpq_mode_and_legacy_cpq_alias(config_dir: Path) -> None:
    yaml_text = PROFILE_YAML.replace(
        "customer_name: Yaml Corp\n",
        "customer_name: Yaml Corp\ncpq_mode: standalone\nfusion_enabled: false\n",
        1,
    )
    (config_dir / "standalone.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("standalone")
    assert profile.cpq_mode == "standalone"
    assert profile.fusion_enabled is False
    assert profile.rest_base == "https://yaml-dev.example.com/rest/v18"
    assert "/cpq/rest/" not in profile.rest_base

    legacy = PROFILE_YAML.replace(
        "customer_name: Yaml Corp\n",
        "customer_name: Yaml Corp\nmode: cpq\n",
        1,
    )
    (config_dir / "legacy_cpq.yaml").write_text(legacy, encoding="utf-8")
    legacy_profile = load_profile("legacy_cpq")
    assert legacy_profile.cpq_mode == "standalone"
    assert legacy_profile.fusion_enabled is False


def test_fusion_mode_loads_oauth_and_rest_base(config_dir: Path) -> None:
    (config_dir / "fusion.yaml").write_text(FUSION_YAML, encoding="utf-8")
    profile = load_profile("fusion")
    assert profile.cpq_mode == "fusion"
    assert profile.fusion_enabled is True
    assert profile.uses_fusion is True
    assert profile.oauth_client_id == "fusion-client"
    assert profile.oauth_client_secret == "fusion-secret"
    assert profile.oauth_scope == "urn:opc:resource:fusion:demo:cpq/"
    assert profile.rest_base == "https://fusion-dev.example.com/cpq/rest/v19"
    assert profile.sanitize_secret == "fusion-secret"
    assert profile.credentials == []


def test_legacy_mode_fusion_without_fusion_enabled_migrates(config_dir: Path) -> None:
    """Legacy mode: fusion with fusion_enabled omitted → fusion active."""
    yaml_text = """\
version: 1
customer_name: Legacy Fusion
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
    (config_dir / "legacy_fusion.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("legacy_fusion")
    assert profile.cpq_mode == "fusion"
    assert profile.fusion_enabled is True
    assert profile.uses_fusion is True


def test_fusion_gate_legacy_mismatched_flags_still_load_as_hosted(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.profile_yaml import load_profile_document

    fusion_off = """\
version: 1.03
customer_name: Fusion Off
cpq_mode: fusion
fusion_enabled: false
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
    path = config_dir / "fusion_off.yaml"
    path.write_text(fusion_off, encoding="utf-8")
    with pytest.raises(ValueError, match="credentials"):
        load_profile_document(path)

    stand_on = """\
version: 1.03
customer_name: Standalone Fusion Flag
cpq_mode: standalone
fusion_enabled: true
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://cpq-dev.example.com
    credentials:
      - username: u1
        password: p1
"""
    path = config_dir / "stand_on.yaml"
    path.write_text(stand_on, encoding="utf-8")
    doc = load_profile_document(path)
    assert doc.cpq_mode == "standalone"
    assert doc.fusion_enabled is False
    assert load_profile("stand_on").cpq_auth == "basic"


def test_fusion_mode_missing_oauth_rejected(config_dir: Path) -> None:
    yaml_text = """\
version: 1
customer_name: Broken Fusion
cpq_mode: fusion
fusion_enabled: true
default_environment: dev
rest_api_version: v19
environments:
  dev:
    url: https://fusion-dev.example.com
"""
    (config_dir / "broken.yaml").write_text(yaml_text, encoding="utf-8")
    with pytest.raises(ValueError, match="credentials"):
        load_profile("broken")


def test_profile_yaml_format_version_float(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.profile_yaml import (
        PROFILE_YAML_FORMAT_VERSION,
        CustomerProfileDocument,
        load_profile_document,
    )

    assert PROFILE_YAML_FORMAT_VERSION == 1.06
    assert CustomerProfileDocument.model_fields["version"].default == 1.06

    yaml_text = """\
version: 1.06
customer_name: Versioned
cpq_mode: standalone
fusion_enabled: false
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
    assert doc.version == 1.06
    assert doc.cpq_mode == "standalone"
    assert doc.fusion_enabled is False
    assert doc.frugal_mode is False
    assert doc.fusion_modules == []

    # Older integer / 1.01 versions still load (backward compatible).
    old = yaml_text.replace("version: 1.06", "version: 1", 1)
    path.write_text(old, encoding="utf-8")
    doc_old = load_profile_document(path)
    assert doc_old.version == 1.0

    mid = yaml_text.replace("version: 1.06", "version: 1.01", 1)
    path.write_text(mid, encoding="utf-8")
    assert load_profile_document(path).version == 1.01


def test_load_profile_accepts_format_version_float(config_dir: Path) -> None:
    """Regression: float format version must not break ProfileCatalog (int)."""
    yaml_text = """\
version: 1.03
customer_name: Format Ok
cpq_mode: standalone
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
    assert profile.cpq_mode == "standalone"
    assert profile.commerce_process_var_names == ["oraclecpqo"]


def test_fusion_skips_credentials_cpq_skips_oauth(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.profile_yaml import load_profile_document

    fusion = """\
version: 1.03
customer_name: Fusion Skip Creds
cpq_mode: fusion
fusion_enabled: true
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
    assert doc.cpq_mode == "fusion"
    assert doc.fusion_enabled is True
    assert doc.environments["dev"].credentials == []
    profile = load_profile("fskip")
    assert profile.uses_fusion is True
    assert profile.credentials == []

    cpq = """\
version: 1.03
customer_name: Cpq Skip Oauth
cpq_mode: standalone
fusion_enabled: false
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
    assert doc.cpq_mode == "standalone"
    assert doc.environments["dev"].oauth_client_id is None
    assert load_profile("cskip").cpq_mode == "standalone"


def test_cpq_enabled_env_missing_credentials_rejected(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.profile_yaml import load_profile_document

    yaml_text = """\
version: 1.03
customer_name: Broken Cpq
cpq_mode: standalone
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://cpq-dev.example.com
    enabled: true
"""
    path = config_dir / "broken_cpq.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    with pytest.raises(ValueError, match="credentials"):
        load_profile_document(path)


def test_frugal_mode_forces_refined_off_and_export_never(config_dir: Path) -> None:
    yaml_text = """\
version: 1.04
customer_name: Frugal Corp
cpq_mode: standalone
frugal_mode: true
refined_prompt: true
auto_save_refined_prompt: true
post_response_export: always_excel
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://frugal-dev.example.com
    credentials:
      - username: u1
        password: p1
"""
    (config_dir / "frugal.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("frugal")
    assert profile.frugal_mode is True
    assert profile.refined_prompt is False
    assert profile.auto_save_refined_prompt is False
    assert profile.post_response_export == "never"


def test_normalize_fusion_modules_csv_list_blank_and_invalid() -> None:
    from oracle_cpq_mcp.core.profile_yaml import normalize_fusion_modules

    assert normalize_fusion_modules(None) == []
    assert normalize_fusion_modules("") == []
    assert normalize_fusion_modules("  ") == []
    assert normalize_fusion_modules("Sales, Service") == ["Sales", "Service"]
    assert normalize_fusion_modules("service, sales, PRM") == [
        "Sales",
        "PRM",
        "Service",
    ]
    assert normalize_fusion_modules(
        ["Field Service", "Incentive Compensation", "Subscription"]
    ) == ["Field Service", "Subscription", "Incentive Compensation"]
    assert normalize_fusion_modules(["Sales", "Sales", "sales"]) == ["Sales"]
    with pytest.raises(ValueError, match="Unknown fusion_modules"):
        normalize_fusion_modules("Sales, NotAModule")


def test_fusion_module_slugs_match_allowlist() -> None:
    from oracle_cpq_mcp.core.profile_yaml import (
        FUSION_MODULE_ALLOWLIST,
        FUSION_MODULE_SLUGS,
    )

    assert set(FUSION_MODULE_SLUGS) == set(FUSION_MODULE_ALLOWLIST)
    assert FUSION_MODULE_SLUGS["Sales"] == "sales"
    assert FUSION_MODULE_SLUGS["PRM"] == "prm"
    assert FUSION_MODULE_SLUGS["Field Service"] == "field_service"
    assert FUSION_MODULE_SLUGS["Incentive Compensation"] == "incentive_compensation"
    assert len(FUSION_MODULE_SLUGS) == len(set(FUSION_MODULE_SLUGS.values()))


def test_fusion_modules_load_profile_csv_and_list(config_dir: Path) -> None:
    csv_yaml = """\
version: 1.05
customer_name: Modules CSV
cpq_mode: fusion
fusion_enabled: true
fusion_modules: Sales, Service
default_environment: dev
rest_api_version: v19
environments:
  dev:
    url: https://mod-csv.example.com
    oauth_token_url: https://idcs.example.com/oauth2/v1/token
    oauth_client_id: cid
    oauth_client_secret: csecret
    oauth_scope: urn:opc:resource:fusion:x:cpq/
"""
    (config_dir / "modcsv.yaml").write_text(csv_yaml, encoding="utf-8")
    profile = load_profile("modcsv")
    assert profile.fusion_modules == ["Sales", "Service"]

    list_yaml = """\
version: 1.05
customer_name: Modules List
cpq_mode: fusion
fusion_enabled: true
fusion_modules:
  - PRM
  - Field Service
default_environment: dev
rest_api_version: v19
environments:
  dev:
    url: https://mod-list.example.com
    oauth_token_url: https://idcs.example.com/oauth2/v1/token
    oauth_client_id: cid
    oauth_client_secret: csecret
    oauth_scope: urn:opc:resource:fusion:x:cpq/
"""
    (config_dir / "modlist.yaml").write_text(list_yaml, encoding="utf-8")
    assert load_profile("modlist").fusion_modules == ["PRM", "Field Service"]


def test_legacy_mode_alias_still_loads_with_empty_fusion_modules(
    config_dir: Path,
) -> None:
    yaml_text = """\
version: 1.02
customer_name: Legacy Mode
mode: fusion
default_environment: dev
rest_api_version: v19
environments:
  dev:
    url: https://legacy-mode.example.com
    oauth_token_url: https://idcs.example.com/oauth2/v1/token
    oauth_client_id: cid
    oauth_client_secret: csecret
    oauth_scope: urn:opc:resource:fusion:x:cpq/
"""
    (config_dir / "legacymode.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("legacymode")
    assert profile.cpq_mode == "fusion"
    assert profile.fusion_enabled is True
    assert profile.fusion_modules == []


def test_nested_cpq_and_cx_blocks(config_dir: Path) -> None:
    yaml_text = """\
version: 1.06
customer_name: Dual Corp
default_environment: dev
rest_api_version: v19
environments:
  dev:
    enabled: true
    cpq:
      enabled: true
      hosted: fusion
      url: https://dual-cpq.example.com
      auth: bearer
      oauth_token_url: https://idcs.example.com/oauth2/v1/token
      oauth_client_id: cid
      oauth_client_secret: csecret
      oauth_scope: urn:opc:resource:fusion:dual:cpq/
    cx:
      enabled: true
      url: https://dual-cx.example.com
      auth: basic
      modules:
        - Sales
        - Service
      credentials:
        - username: cx_user
          password: cx_pass
"""
    (config_dir / "dual.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("dual")
    assert profile.cpq_enabled is True
    assert profile.cpq_auth == "bearer"
    assert profile.uses_fusion is True
    assert profile.uses_cpq_bearer is True
    assert profile.rest_base == "https://dual-cpq.example.com/cpq/rest/v19"
    assert profile.cx_enabled is True
    assert profile.cx_url == "https://dual-cx.example.com"
    assert profile.cx_modules == ["Sales", "Service"]
    assert profile.fusion_modules == ["Sales", "Service"]
    assert profile.cx_credentials[0].username == "cx_user"


def test_cx_only_profile(config_dir: Path) -> None:
    yaml_text = """\
version: 1.06
customer_name: Cx Only
default_environment: dev
rest_api_version: v19
environments:
  dev:
    enabled: true
    cx:
      enabled: true
      url: https://cx-only.example.com
      auth: basic
      modules: [Sales]
      credentials:
        - username: cx_user
          password: cx_pass
"""
    (config_dir / "cxonly.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("cxonly")
    assert profile.cpq_enabled is False
    assert profile.cx_enabled is True
    assert profile.cx_modules == ["Sales"]
    with pytest.raises(RuntimeError, match="does not have CPQ enabled"):
        _ = profile.rest_base


def test_cx_enabled_requires_modules(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.profile_yaml import load_profile_document

    yaml_text = """\
version: 1.06
customer_name: Cx No Modules
default_environment: dev
environments:
  dev:
    enabled: true
    cx:
      enabled: true
      url: https://cx.example.com
      auth: basic
      credentials:
        - username: u1
          password: p1
"""
    path = config_dir / "cxnomod.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    with pytest.raises(ValueError, match="modules"):
        load_profile_document(path)


def test_cpq_bearer_missing_oauth_rejected(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.profile_yaml import load_profile_document

    yaml_text = """\
version: 1.06
customer_name: Bearer Gap
default_environment: dev
environments:
  dev:
    enabled: true
    cpq:
      enabled: true
      url: https://cpq.example.com
      auth: bearer
"""
    path = config_dir / "bearergap.yaml"
    path.write_text(yaml_text, encoding="utf-8")
    with pytest.raises(ValueError, match="auth: bearer"):
        load_profile_document(path)


def test_flat_cx_username_password_migrates_to_credentials(config_dir: Path) -> None:
    yaml_text = """\
version: 1.06
customer_name: Flat Cx Creds
default_environment: dev
rest_api_version: v19
environments:
  dev:
    enabled: true
    cx:
      enabled: true
      url: https://cx.example.com
      auth: basic
      modules: [Sales, PRM]
      username: cx_user@example.com
      password: cx_secret
"""
    (config_dir / "flatcx.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("flatcx")
    assert profile.cx_enabled is True
    assert profile.cx_modules == ["Sales", "PRM"]
    assert profile.cx_credentials[0].username == "cx_user@example.com"
    assert profile.cx_credentials[0].password == "cx_secret"


def test_hosted_fusion_basic_auth_uses_cpq_rest_prefix(config_dir: Path) -> None:
    yaml_text = """\
version: 1.06
customer_name: Fusion Basic
default_environment: dev
rest_api_version: v19
environments:
  dev:
    enabled: true
    cpq:
      enabled: true
      hosted: fusion
      url: https://fa.example.com
      auth: basic
      credentials:
        - username: u1
          password: p1
"""
    (config_dir / "fusbasic.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("fusbasic")
    assert profile.uses_fusion is True
    assert profile.uses_cpq_bearer is False
    assert profile.cpq_auth == "basic"
    assert profile.rest_base == "https://fa.example.com/cpq/rest/v19"
