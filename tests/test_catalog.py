"""Unit tests for profile catalog YAML + flat product-family parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from oracle_cpq_mcp.core.catalog import (
    catalog_from_flat_env,
    dump_catalog_yaml,
    load_catalog,
    parse_flat_product_families,
)
from oracle_cpq_mcp.core.config import (
    load_profile,
    resolve_product_family_alias,
    resolve_product_line_alias,
    resolve_product_model_alias,
)

FIXTURE_ENV = """\
CUSTOMER_NAME=Test Corp
DEV_URL=https://dev.example.com
DEV_USERNAME=dev_user
DEV_PASSWORD=dev_pass
DEFAULT_ENVIRONMENT=dev
REST_API_VERSION=v18
CUSTOM_DATA_TABLE_NAME=ModelMaster
COMMERCE_PROCESS_VAR_NAME=oraclecpqo_bmClone_2
"""

CATALOG_YAML = """\
version: 1
commerce_processes:
  - var_name: yaml_process
    alias: YAML Commerce
    enabled: true
  - var_name: disabled_proc
    alias: Disabled
    enabled: false
data_tables:
  - name: YamlTable
    alias: yaml table
metrics:
  QUOTES: From YAML
product_families:
  - var_name: laptop
    name: Laptop
    alias: Laptop Family
    enabled: true
    lines:
      - var_name: hp
        name: HP
        alias: HP Line
        enabled: true
        models:
          - var_name: elite840
            name: EliteBook 840
            alias: Elite 840
            enabled: true
          - var_name: off_model
            alias: Off Model
            enabled: false
"""


@pytest.fixture()
def config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cfg = tmp_path / ".config"
    cfg.mkdir()
    (cfg / "acme.env").write_text(FIXTURE_ENV, encoding="utf-8")
    monkeypatch.setenv("CPQ_CONFIG_DIR", str(cfg))
    monkeypatch.delenv("CPQ_ENVIRONMENT", raising=False)
    monkeypatch.delenv("CPQ_CUSTOMER_PROFILE", raising=False)
    return cfg


def test_yaml_catalog_wins_over_flat_env(config_dir: Path) -> None:
    (config_dir / "acme.catalog.yaml").write_text(CATALOG_YAML, encoding="utf-8")
    profile = load_profile("acme")
    assert profile.catalog_source == "catalog_yaml"
    assert profile.commerce_process_var_names == ["yaml_process"]
    assert profile.commerce_process_aliases["yaml commerce"] == "yaml_process"
    assert "disabled" not in profile.commerce_process_aliases
    assert profile.custom_data_table_names == ["YamlTable"]
    assert profile.custom_data_table_aliases["yaml table"] == "YamlTable"
    assert profile.metric_descriptions["QUOTES"] == "From YAML"
    assert len(profile.product_families) == 1
    assert profile.product_families[0].var_name == "laptop"
    assert len(profile.product_families[0].lines[0].models) == 1
    assert resolve_product_family_alias(profile, "Laptop Family") == "laptop"
    assert resolve_product_line_alias(profile, "HP Line") == "hp"
    assert resolve_product_model_alias(profile, "Elite 840") == "elite840"
    assert resolve_product_model_alias(profile, "Off Model") is None


def test_flat_product_families_when_no_yaml(config_dir: Path) -> None:
    env = config_dir / "flatfam.env"
    env.write_text(
        FIXTURE_ENV
        + "PRODUCT_FAMILY_VAR_NAME_1=laptop\n"
        + "PRODUCT_FAMILY_1_NAME=Laptop\n"
        + "PRODUCT_FAMILY_1_ALIAS=Laptop Family\n"
        + "PRODUCT_FAMILY_ENABLED_1=true\n"
        + "PRODUCT_LINE_VAR_NAME_1_1=hp\n"
        + "PRODUCT_LINE_NAME_1_1=HP\n"
        + "PRODUCT_LINE_ALIAS_1_1=HP Line\n"
        + "PRODUCT_LINE_ENABLED_1_1=true\n"
        + "MODEL_VAR_NAME_1_1_1=elite840\n"
        + "MODEL_NAME_1_1_1=EliteBook\n"
        + "MODEL_ALIAS_1_1_1=Elite 840\n"
        + "MODEL_ENABLED_1_1_1=true\n"
        + "PRODUCT_FAMILY_VAR_NAME_2=offFam\n"
        + "PRODUCT_FAMILY_2_ALIAS=Off Family\n"
        + "PRODUCT_FAMILY_ENABLED_2=false\n",
        encoding="utf-8",
    )
    profile = load_profile("flatfam")
    assert profile.catalog_source == "env"
    assert [f.var_name for f in profile.product_families] == ["laptop"]
    assert resolve_product_family_alias(profile, "Laptop Family") == "laptop"
    assert resolve_product_family_alias(profile, "Off Family") is None
    assert resolve_product_line_alias(profile, "hp line") == "hp"
    assert resolve_product_model_alias(profile, "elite 840") == "elite840"


def test_no_catalog_source_without_families(config_dir: Path) -> None:
    profile = load_profile("acme")
    assert profile.catalog_source == "none"
    assert profile.product_families == []
    assert profile.commerce_process_var_name == "oraclecpqo_bmClone_2"


def test_parse_flat_and_dump_roundtrip() -> None:
    raw = {
        "COMMERCE_PROCESS_VAR_NAME": "p1",
        "COMMERCE_PROCESS_ALIAS": "Process One",
        "COMMERCE_PROCESS_ENABLED": "true",
        "CUSTOM_DATA_TABLE_NAME": "T1",
        "CUSTOM_DATA_TABLE_ALIAS": "table one",
        "METRICS_QUOTES": "Quotes",
        "PRODUCT_FAMILY_VAR_NAME_1": "fam",
        "PRODUCT_FAMILY_1_ALIAS": "Fam Alias",
        "PRODUCT_FAMILY_ENABLED_1": "true",
        "PRODUCT_LINE_VAR_NAME_1_1": "line",
        "PRODUCT_LINE_ALIAS_1_1": "Line Alias",
        "MODEL_VAR_NAME_1_1_1": "mod",
        "MODEL_ALIAS_1_1_1": "Mod Alias",
    }
    catalog = catalog_from_flat_env(raw)
    assert len(catalog.commerce_processes) == 1
    assert catalog.metrics["QUOTES"] == "Quotes"
    families = parse_flat_product_families(raw)
    assert families[0].lines[0].models[0].var_name == "mod"
    text = dump_catalog_yaml(catalog)
    assert "commerce_processes:" in text
    assert "product_families:" in text


def test_load_catalog_missing(config_dir: Path) -> None:
    assert load_catalog("missing") is None
