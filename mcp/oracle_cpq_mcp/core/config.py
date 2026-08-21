"""Load and resolve Oracle CPQ customer profiles from `.config/<customer>.env`."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, Field, field_validator

EnvironmentName = Literal["dev", "test", "prod"]
LocalDataPolicy = Literal["ask", "prefer", "never"]


class CredentialSet(BaseModel):
    """One Basic Auth credential pair for an environment."""

    username: str
    password: str = Field(repr=False)


class CPQProfile(BaseModel):
    """Resolved CPQ connection settings for one customer profile + environment."""

    customer_name: str
    customer_id: str
    environment: EnvironmentName
    base_url: str
    rest_version: str
    company_login_name: str = "_host"
    credentials: list[CredentialSet]
    credential_index: int = 0
    custom_data_table_names: list[str] = Field(default_factory=list)
    commerce_process_var_names: list[str] = Field(default_factory=list)
    read_only: bool = True
    refined_prompt: bool = True
    auto_save_refined_prompt: bool = False
    local_data_policy: LocalDataPolicy = "ask"

    @field_validator("base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def username(self) -> str:
        return self.credentials[self.credential_index].username

    @property
    def password(self) -> str:
        return self.credentials[self.credential_index].password

    @property
    def custom_data_table_name(self) -> str | None:
        return self.custom_data_table_names[0] if self.custom_data_table_names else None

    @property
    def commerce_process_var_name(self) -> str | None:
        return self.commerce_process_var_names[0] if self.commerce_process_var_names else None

    @property
    def rest_base(self) -> str:
        return f"{self.base_url}/rest/{self.rest_version}"


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from *start* (or cwd) to locate the repo root containing `.config`."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".config").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate project root with a `.config` directory. "
        "Set CPQ_CONFIG_DIR to the repo root."
    )


def config_dir() -> Path:
    if env_dir := os.environ.get("CPQ_CONFIG_DIR"):
        path = Path(env_dir).resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"CPQ_CONFIG_DIR does not exist: {path}")
        return path
    return find_project_root() / ".config"


def profile_path(customer_id: str) -> Path:
    path = config_dir() / f"{customer_id}.env"
    if not path.is_file():
        raise FileNotFoundError(
            f"Customer profile not found: {path}. "
            f"Copy .config/.env.example to .config/{customer_id}.env"
        )
    return path


def _env_prefix(environment: EnvironmentName) -> str:
    return environment.upper()


def parse_bool_env(value: str | None, *, default: bool) -> bool:
    """Parse common truthy/falsey strings from profile env values."""
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in ("1", "true", "yes", "on"):
        return True
    if normalized in ("0", "false", "no", "off"):
        return False
    raise ValueError(
        f"Invalid boolean env value '{value}'. Use true/false, yes/no, 1/0, or on/off."
    )


def connection_mode_message(read_only: bool) -> str:
    """Human-readable connection mode for logs and smoke output."""
    if read_only:
        return (
            "Connected in READ-ONLY mode — create/update/patch/delete operations are blocked."
        )
    return (
        "Connected in DML-ENABLED mode — write operations (create/update/deploy) "
        "are permitted when confirmed."
    )


def _resolve_read_only(raw: dict[str, str | None]) -> bool:
    if os.environ.get("CPQ_READ_ONLY") is not None:
        return parse_bool_env(os.environ.get("CPQ_READ_ONLY"), default=True)
    return parse_bool_env(raw.get("READ_ONLY"), default=True)


def _resolve_refined_prompt(raw: dict[str, str | None]) -> bool:
    if os.environ.get("CPQ_REFINED_PROMPT") is not None:
        return parse_bool_env(os.environ.get("CPQ_REFINED_PROMPT"), default=True)
    return parse_bool_env(raw.get("REFINED_PROMPT"), default=True)


def _resolve_auto_save_refined_prompt(raw: dict[str, str | None]) -> bool:
    if os.environ.get("CPQ_AUTO_SAVE_REFINED_PROMPT") is not None:
        return parse_bool_env(
            os.environ.get("CPQ_AUTO_SAVE_REFINED_PROMPT"), default=False
        )
    return parse_bool_env(raw.get("AUTO_SAVE_REFINED_PROMPT"), default=False)


def _resolve_local_data_policy(raw: dict[str, str | None]) -> LocalDataPolicy:
    from oracle_cpq_mcp.core.local_data import parse_local_data_policy

    if os.environ.get("CPQ_LOCAL_DATA_POLICY") is not None:
        return parse_local_data_policy(os.environ.get("CPQ_LOCAL_DATA_POLICY"), default="ask")
    return parse_local_data_policy(raw.get("LOCAL_DATA_POLICY"), default="ask")


# Keys the MCP tools are allowed to rewrite in the active profile .env.
PROFILE_ENV_WRITABLE_KEYS = frozenset(
    {"AUTO_SAVE_REFINED_PROMPT", "LOCAL_DATA_POLICY"}
)


def update_profile_env_key(
    customer_id: str,
    key: str,
    value: str,
    *,
    path: Path | None = None,
) -> Path:
    """Replace or append a single allowlisted key in the profile .env file.

    Preserves comments and all other keys. Never used for credentials.
    """
    if key not in PROFILE_ENV_WRITABLE_KEYS:
        raise ValueError(
            f"Refusing to write env key {key!r}; allowlist is "
            f"{sorted(PROFILE_ENV_WRITABLE_KEYS)}"
        )
    target = path or profile_path(customer_id)
    if not target.is_file():
        raise FileNotFoundError(f"Customer profile not found: {target}")

    text = target.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith(("\n", "\r")):
        # Normalize so we can append cleanly later
        pass

    key_prefix = f"{key}="
    replaced = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue
        # Compare key part (ignore leading whitespace)
        left = line.split("=", 1)[0].strip()
        if left == key:
            eol = "\n"
            if line.endswith("\r\n"):
                eol = "\r\n"
            elif line.endswith("\n"):
                eol = "\n"
            elif line.endswith("\r"):
                eol = "\r"
            else:
                eol = "\n"
            new_lines.append(f"{key}={value}{eol}")
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        needs_nl = bool(new_lines) and not new_lines[-1].endswith(("\n", "\r"))
        if needs_nl:
            new_lines[-1] = new_lines[-1] + "\n"
        new_lines.append(f"{key}={value}\n")

    target.write_text("".join(new_lines), encoding="utf-8")
    return target


def _collect_numbered_values(raw: dict[str, str | None], base_key: str) -> list[str]:
    """Return [base_key, base_key_1, base_key_2, ...] values in order; skip empty."""
    values: list[str] = []
    primary = raw.get(base_key)
    if primary:
        values.append(primary)
    index = 1
    while f"{base_key}_{index}" in raw:
        value = raw.get(f"{base_key}_{index}")
        if value:
            values.append(value)
        index += 1
    return values


def _collect_credential_suffixes(raw: dict[str, str | None], prefix: str) -> list[str]:
    suffixes = [""]
    index = 1
    while f"{prefix}_USERNAME_{index}" in raw:
        suffixes.append(f"_{index}")
        index += 1
    return suffixes


def _load_credentials(raw: dict[str, str | None], prefix: str) -> list[CredentialSet]:
    credentials: list[CredentialSet] = []
    for suffix in _collect_credential_suffixes(raw, prefix):
        username_key = f"{prefix}_USERNAME{suffix}"
        password_key = f"{prefix}_PASSWORD{suffix}"
        username = raw.get(username_key) or ""
        password = raw.get(password_key) or ""
        if not username and not password:
            continue
        if not username or not password:
            missing_key = password_key if username else username_key
            raise ValueError(
                f"Profile missing paired credential: both {username_key} and "
                f"{password_key} are required (missing {missing_key})"
            )
        credentials.append(CredentialSet(username=username, password=password))
    return credentials


def _resolve_credential_index(
    credential_index: int | None,
    credential_count: int,
) -> int:
    if credential_index is None:
        env_value = os.environ.get("CPQ_CREDENTIAL_INDEX")
        credential_index = int(env_value) if env_value is not None else 0
    if credential_index < 0 or credential_index >= credential_count:
        raise ValueError(
            f"CPQ_CREDENTIAL_INDEX {credential_index} is out of range "
            f"(profile has {credential_count} credential set(s), "
            f"indices 0–{credential_count - 1})"
        )
    return credential_index


def load_profile(
    customer_id: str | None = None,
    environment: EnvironmentName | None = None,
    credential_index: int | None = None,
) -> CPQProfile:
    """Load `.config/<customer_id>.env` and resolve the active environment."""
    customer_id = customer_id or os.environ.get("CPQ_CUSTOMER_PROFILE", "mycompany")
    raw = dotenv_values(profile_path(customer_id))

    active_env: EnvironmentName = (
        environment
        or os.environ.get("CPQ_ENVIRONMENT", raw.get("DEFAULT_ENVIRONMENT", "dev"))  # type: ignore[assignment]
    )  # type: ignore[assignment]
    if active_env not in ("dev", "test", "prod"):
        raise ValueError(f"Invalid environment '{active_env}'. Use dev, test, or prod.")

    prefix = _env_prefix(active_env)
    base_url = raw.get(f"{prefix}_URL") or ""
    credentials = _load_credentials(raw, prefix)

    missing = [name for name, value in [(f"{prefix}_URL", base_url)] if not value]
    if not credentials:
        missing.append(f"{prefix}_USERNAME")
        missing.append(f"{prefix}_PASSWORD")
    if missing:
        raise ValueError(
            f"Profile '{customer_id}' is missing required keys for '{active_env}': "
            + ", ".join(missing)
        )

    resolved_index = _resolve_credential_index(credential_index, len(credentials))

    return CPQProfile(
        customer_name=raw.get("CUSTOMER_NAME") or customer_id,
        customer_id=customer_id,
        environment=active_env,
        base_url=base_url,
        rest_version=raw.get("REST_API_VERSION") or "v18",
        company_login_name=raw.get("COMPANY_LOGIN_NAME") or "_host",
        credentials=credentials,
        credential_index=resolved_index,
        custom_data_table_names=_collect_numbered_values(raw, "CUSTOM_DATA_TABLE_NAME"),
        commerce_process_var_names=_collect_numbered_values(raw, "COMMERCE_PROCESS_VAR_NAME"),
        read_only=_resolve_read_only(raw),
        refined_prompt=_resolve_refined_prompt(raw),
        auto_save_refined_prompt=_resolve_auto_save_refined_prompt(raw),
        local_data_policy=_resolve_local_data_policy(raw),
    )
