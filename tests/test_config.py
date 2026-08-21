"""Unit tests for customer profile loading."""



from __future__ import annotations



from pathlib import Path



import pytest



from oracle_cpq_mcp.core.config import CPQProfile, load_profile





FIXTURE_ENV = """\

CUSTOMER_NAME=Test Corp

DEV_URL=https://dev.example.com

TEST_URL=https://test.example.com

PROD_URL=https://prod.example.com

DEV_USERNAME=dev_user

DEV_PASSWORD=dev_pass

TEST_USERNAME=test_user

TEST_PASSWORD=test_pass

PROD_USERNAME=prod_user

PROD_PASSWORD=prod_pass

DEFAULT_ENVIRONMENT=dev

REST_API_VERSION=v18

COMPANY_LOGIN_NAME=_host

CUSTOM_DATA_TABLE_NAME=ModelMaster

COMMERCE_PROCESS_VAR_NAME=oraclecpqo_bmClone_2

"""



MULTI_VALUE_ENV = """\

CUSTOMER_NAME=Multi Corp

DEV_URL=https://dev.example.com

DEV_USERNAME=dev_user

DEV_PASSWORD=dev_pass

DEV_USERNAME_1=dev_user_2

DEV_PASSWORD_1=dev_pass_2

DEFAULT_ENVIRONMENT=dev

REST_API_VERSION=v18

CUSTOM_DATA_TABLE_NAME=TableA

CUSTOM_DATA_TABLE_NAME_1=TableB

COMMERCE_PROCESS_VAR_NAME=process_a

COMMERCE_PROCESS_VAR_NAME_1=process_b

"""





@pytest.fixture()

def config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:

    cfg = tmp_path / ".config"

    cfg.mkdir()

    (cfg / "acme.env").write_text(FIXTURE_ENV, encoding="utf-8")

    (cfg / "multi.env").write_text(MULTI_VALUE_ENV, encoding="utf-8")

    monkeypatch.setenv("CPQ_CONFIG_DIR", str(cfg))

    monkeypatch.delenv("CPQ_ENVIRONMENT", raising=False)

    monkeypatch.delenv("CPQ_CUSTOMER_PROFILE", raising=False)

    monkeypatch.delenv("CPQ_CREDENTIAL_INDEX", raising=False)
    monkeypatch.delenv("CPQ_READ_ONLY", raising=False)
    monkeypatch.delenv("CPQ_REFINED_PROMPT", raising=False)
    monkeypatch.delenv("CPQ_AUTO_SAVE_REFINED_PROMPT", raising=False)

    return cfg





def test_load_profile_dev_defaults(config_dir: Path) -> None:

    profile = load_profile("acme")

    assert isinstance(profile, CPQProfile)

    assert profile.customer_name == "Test Corp"

    assert profile.base_url == "https://dev.example.com"

    assert profile.username == "dev_user"

    assert profile.password == "dev_pass"

    assert profile.rest_version == "v18"

    assert profile.company_login_name == "_host"

    assert profile.custom_data_table_name == "ModelMaster"

    assert profile.custom_data_table_names == ["ModelMaster"]

    assert profile.commerce_process_var_name == "oraclecpqo_bmClone_2"

    assert profile.commerce_process_var_names == ["oraclecpqo_bmClone_2"]

    assert len(profile.credentials) == 1

    assert profile.credential_index == 0
    assert profile.read_only is True
    assert profile.refined_prompt is True
    assert profile.auto_save_refined_prompt is False
    assert profile.rest_base == "https://dev.example.com/rest/v18"





def test_load_profile_test_override(config_dir: Path) -> None:

    profile = load_profile("acme", "test")

    assert profile.environment == "test"

    assert profile.base_url == "https://test.example.com"

    assert profile.username == "test_user"





def test_load_profile_multiple_credentials(config_dir: Path) -> None:

    profile = load_profile("multi")

    assert len(profile.credentials) == 2

    assert profile.credentials[0].username == "dev_user"

    assert profile.credentials[1].username == "dev_user_2"

    assert profile.username == "dev_user"





def test_load_profile_credential_index(config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:

    profile = load_profile("multi", credential_index=1)

    assert profile.credential_index == 1

    assert profile.username == "dev_user_2"

    assert profile.password == "dev_pass_2"



    monkeypatch.setenv("CPQ_CREDENTIAL_INDEX", "1")

    profile_env = load_profile("multi")

    assert profile_env.username == "dev_user_2"





def test_load_profile_credential_index_out_of_range(config_dir: Path) -> None:

    with pytest.raises(ValueError, match="CPQ_CREDENTIAL_INDEX"):

        load_profile("multi", credential_index=5)





def test_load_profile_multiple_tables_and_commerce(config_dir: Path) -> None:

    profile = load_profile("multi")

    assert profile.custom_data_table_names == ["TableA", "TableB"]

    assert profile.commerce_process_var_names == ["process_a", "process_b"]





def test_missing_paired_password_raises(config_dir: Path) -> None:

    broken = config_dir / "broken.env"

    broken.write_text(

        "CUSTOMER_NAME=X\nDEFAULT_ENVIRONMENT=dev\n"

        "DEV_URL=https://dev.example.com\n"

        "DEV_USERNAME=user1\n"

        "DEV_USERNAME_1=user2\n",

        encoding="utf-8",

    )

    with pytest.raises(ValueError, match="paired credential"):

        load_profile("broken")





def test_missing_profile_raises(config_dir: Path) -> None:

    with pytest.raises(FileNotFoundError, match="Customer profile not found"):

        load_profile("missing")





def test_missing_env_keys_raises(config_dir: Path) -> None:

    incomplete = config_dir / "incomplete.env"

    incomplete.write_text("CUSTOMER_NAME=X\nDEFAULT_ENVIRONMENT=prod\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required keys"):

        load_profile("incomplete")


def test_load_profile_read_only_false(config_dir: Path) -> None:
    env = config_dir / "writable.env"
    env.write_text(
        FIXTURE_ENV.replace("COMMERCE_PROCESS_VAR_NAME=oraclecpqo_bmClone_2", "")
        + "READ_ONLY=false\nCOMMERCE_PROCESS_VAR_NAME=oraclecpqo_bmClone_2\n",
        encoding="utf-8",
    )
    profile = load_profile("writable")
    assert profile.read_only is False


def test_load_profile_refined_prompt_false(config_dir: Path) -> None:
    env = config_dir / "no_refined.env"
    env.write_text(
        FIXTURE_ENV + "REFINED_PROMPT=false\n",
        encoding="utf-8",
    )
    profile = load_profile("no_refined")
    assert profile.refined_prompt is False


def test_load_profile_refined_prompt_env_override(
    config_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = config_dir / "refined_file.env"
    env.write_text(FIXTURE_ENV + "REFINED_PROMPT=true\n", encoding="utf-8")
    monkeypatch.setenv("CPQ_REFINED_PROMPT", "false")
    profile = load_profile("refined_file")
    assert profile.refined_prompt is False


def test_load_profile_auto_save_refined_prompt_defaults_false(config_dir: Path) -> None:
    profile = load_profile("acme")
    assert profile.auto_save_refined_prompt is False


def test_load_profile_auto_save_refined_prompt_true(config_dir: Path) -> None:
    env = config_dir / "auto_save.env"
    env.write_text(FIXTURE_ENV + "AUTO_SAVE_REFINED_PROMPT=true\n", encoding="utf-8")
    profile = load_profile("auto_save")
    assert profile.auto_save_refined_prompt is True


def test_load_profile_auto_save_env_override(
    config_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = config_dir / "auto_save_file.env"
    env.write_text(FIXTURE_ENV + "AUTO_SAVE_REFINED_PROMPT=false\n", encoding="utf-8")
    monkeypatch.setenv("CPQ_AUTO_SAVE_REFINED_PROMPT", "true")
    profile = load_profile("auto_save_file")
    assert profile.auto_save_refined_prompt is True


def test_update_profile_env_key_replaces_and_preserves(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.config import update_profile_env_key

    path = config_dir / "acme.env"
    original = path.read_text(encoding="utf-8")
    assert "DEV_PASSWORD=dev_pass" in original

    update_profile_env_key("acme", "AUTO_SAVE_REFINED_PROMPT", "true")
    text = path.read_text(encoding="utf-8")
    assert "AUTO_SAVE_REFINED_PROMPT=true" in text
    assert "DEV_PASSWORD=dev_pass" in text
    assert "CUSTOMER_NAME=Test Corp" in text

    update_profile_env_key("acme", "AUTO_SAVE_REFINED_PROMPT", "false")
    text2 = path.read_text(encoding="utf-8")
    assert text2.count("AUTO_SAVE_REFINED_PROMPT=") == 1
    assert "AUTO_SAVE_REFINED_PROMPT=false" in text2

    update_profile_env_key("acme", "LOCAL_DATA_POLICY", "prefer")
    text3 = path.read_text(encoding="utf-8")
    assert "LOCAL_DATA_POLICY=prefer" in text3
    assert "DEV_PASSWORD=dev_pass" in text3


def test_update_profile_env_key_rejects_non_allowlisted(config_dir: Path) -> None:
    from oracle_cpq_mcp.core.config import update_profile_env_key

    with pytest.raises(ValueError, match="allowlist"):
        update_profile_env_key("acme", "DEV_PASSWORD", "hacked")


def test_connection_mode_message_read_only() -> None:
    from oracle_cpq_mcp.core.config import connection_mode_message

    assert "read-only" in connection_mode_message(True).lower()
    assert "dml" in connection_mode_message(False).lower()

