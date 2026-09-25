"""Load and resolve Oracle CPQ customer profiles from `.config/<customer>.yaml` or `.env`."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, Field, field_validator

from oracle_cpq_mcp.core.catalog import CatalogProductFamily

EnvironmentName = Literal["dev", "test", "prod"]
LocalDataPolicy = Literal["ask", "prefer", "never"]
PostResponseExportPolicy = Literal["ask", "never", "always_excel"]
CatalogSource = Literal["none", "env", "catalog_yaml", "profile_yaml"]
ProfileFileKind = Literal["yaml", "env"]


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
    customer_knowledge_file: str | None = None
    commerce_process_aliases: dict[str, str] = Field(default_factory=dict)
    custom_data_table_aliases: dict[str, str] = Field(default_factory=dict)
    read_only: bool = True
    refined_prompt: bool = True
    auto_save_refined_prompt: bool = False
    debug_mode: bool = True
    local_data_policy: LocalDataPolicy = "ask"
    post_response_export: PostResponseExportPolicy = "ask"
    http_timeout: float = 60.0
    # METRICS_<NAME> → description; keys are NAME suffixes (e.g. QUOTES).
    metric_descriptions: dict[str, str] = Field(default_factory=dict)
    # Product family tree + aliases (from profile YAML, .catalog.yaml, or flat keys).
    product_families: list[CatalogProductFamily] = Field(default_factory=list)
    product_family_aliases: dict[str, str] = Field(default_factory=dict)
    product_line_aliases: dict[str, str] = Field(default_factory=dict)
    product_model_aliases: dict[str, str] = Field(default_factory=dict)
    catalog_source: CatalogSource = "none"
    profile_file_kind: ProfileFileKind = "env"

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


def profile_env_path(customer_id: str) -> Path:
    """Return `.config/<customer_id>.env` path (may not exist)."""
    return config_dir() / f"{customer_id}.env"


def profile_yaml_path(customer_id: str) -> Path:
    """Return `.config/<customer_id>.yaml` path (may not exist)."""
    return config_dir() / f"{customer_id}.yaml"


def resolve_profile_path(customer_id: str) -> Path:
    """Prefer `.config/<id>.yaml` when present; otherwise require `.env`."""
    yaml_path = profile_yaml_path(customer_id)
    if yaml_path.is_file():
        return yaml_path
    env_path = profile_env_path(customer_id)
    if env_path.is_file():
        return env_path
    raise FileNotFoundError(
        f"Customer profile not found: {yaml_path} (or {env_path}). "
        f"Copy .config/.profile.yaml.example to .config/{customer_id}.yaml "
        f"or use a legacy .config/{customer_id}.env"
    )


def profile_path(customer_id: str) -> Path:
    """Resolved active profile file (``.yaml`` preferred, else ``.env``)."""
    return resolve_profile_path(customer_id)


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


def _resolve_debug_mode(raw: dict[str, str | None]) -> bool:
    if os.environ.get("CPQ_DEBUG_MODE") is not None:
        return parse_bool_env(os.environ.get("CPQ_DEBUG_MODE"), default=True)
    return parse_bool_env(raw.get("DEBUG_MODE"), default=True)


def _resolve_http_timeout(raw: dict[str, str | None]) -> float:
    """Host ``CPQ_HTTP_TIMEOUT`` wins over profile ``HTTP_TIMEOUT`` (seconds)."""
    raw_value = os.environ.get("CPQ_HTTP_TIMEOUT")
    if raw_value is None or not str(raw_value).strip():
        raw_value = raw.get("HTTP_TIMEOUT")
    if raw_value is None or not str(raw_value).strip():
        return 60.0
    try:
        value = float(str(raw_value).strip())
    except ValueError as exc:
        raise ValueError(
            f"Invalid HTTP_TIMEOUT/CPQ_HTTP_TIMEOUT={raw_value!r}; use seconds as a number"
        ) from exc
    if value < 5.0 or value > 3600.0:
        raise ValueError(
            f"HTTP_TIMEOUT/CPQ_HTTP_TIMEOUT={value} out of range; use 5–3600 seconds"
        )
    return value


def _resolve_local_data_policy(raw: dict[str, str | None]) -> LocalDataPolicy:
    from oracle_cpq_mcp.core.local_data import parse_local_data_policy

    if os.environ.get("CPQ_LOCAL_DATA_POLICY") is not None:
        return parse_local_data_policy(os.environ.get("CPQ_LOCAL_DATA_POLICY"), default="ask")
    return parse_local_data_policy(raw.get("LOCAL_DATA_POLICY"), default="ask")


def _resolve_post_response_export(raw: dict[str, str | None]) -> PostResponseExportPolicy:
    def _parse(value: str | None, *, default: PostResponseExportPolicy = "ask") -> PostResponseExportPolicy:
        if value is None or not str(value).strip():
            return default
        normalized = str(value).strip().lower()
        if normalized in ("ask", "never", "always_excel"):
            return normalized  # type: ignore[return-value]
        raise ValueError(
            f"Invalid POST_RESPONSE_EXPORT={value!r}; use ask, never, or always_excel"
        )

    if os.environ.get("CPQ_POST_RESPONSE_EXPORT") is not None:
        return _parse(os.environ.get("CPQ_POST_RESPONSE_EXPORT"), default="ask")
    return _parse(raw.get("POST_RESPONSE_EXPORT"), default="ask")


# Keys the MCP tools are allowed to rewrite in the active profile .env.
PROFILE_ENV_WRITABLE_KEYS = frozenset(
    {"AUTO_SAVE_REFINED_PROMPT", "LOCAL_DATA_POLICY", "POST_RESPONSE_EXPORT"}
)


def update_profile_env_key(
    customer_id: str,
    key: str,
    value: str,
    *,
    path: Path | None = None,
) -> Path:
    """Replace or append a single allowlisted key in the active profile file.

    Supports both `.yaml` (snake_case fields) and legacy `.env`. Never used for
    credentials.
    """
    if key not in PROFILE_ENV_WRITABLE_KEYS:
        raise ValueError(
            f"Refusing to write env key {key!r}; allowlist is "
            f"{sorted(PROFILE_ENV_WRITABLE_KEYS)}"
        )
    target = path or profile_path(customer_id)
    if not target.is_file():
        raise FileNotFoundError(f"Customer profile not found: {target}")

    if target.suffix.lower() in (".yaml", ".yml"):
        from oracle_cpq_mcp.core.profile_yaml import update_profile_yaml_key

        return update_profile_yaml_key(target, key, value)

    text = target.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    replaced = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue
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


def _max_numbered_index(raw: dict[str, str | None], *base_keys: str) -> int:
    """Highest `_N` suffix present for any of the base keys (0 = primary only / none)."""
    max_index = 0
    for base_key in base_keys:
        if base_key in raw:
            max_index = max(max_index, 0)
        index = 1
        while f"{base_key}_{index}" in raw:
            max_index = max(max_index, index)
            index += 1
    return max_index


def _slot_value(raw: dict[str, str | None], base_key: str, index: int) -> str | None:
    key = base_key if index == 0 else f"{base_key}_{index}"
    return (raw.get(key) or "").strip() or None


def pair_aliases_from_raw(
    raw: dict[str, str | None],
    *,
    name_key: str,
    alias_key: str,
    enabled_key: str | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Return (non-empty names in slot order, alias→name map) index-aligned.

    When ``enabled_key`` is set (e.g. ``COMMERCE_PROCESS_ENABLED``), slots with
    ``ENABLED[_N]=false`` are omitted from names and aliases (default true if unset).
    """
    index_keys = (name_key, alias_key) + ((enabled_key,) if enabled_key else ())
    max_index = _max_numbered_index(raw, *index_keys)
    # If neither name nor alias key exists, empty
    if max_index == 0 and name_key not in raw and alias_key not in raw:
        # Still allow primary if only present via empty check
        if _slot_value(raw, name_key, 0) is None and _slot_value(raw, alias_key, 0) is None:
            return [], {}

    names: list[str] = []
    aliases: dict[str, str] = {}
    # Iterate 0..max_index inclusive when any primary/numbered key exists
    last = max_index
    if name_key in raw or alias_key in raw or last > 0:
        for index in range(0, last + 1):
            name = _slot_value(raw, name_key, index)
            alias = _slot_value(raw, alias_key, index)
            if not name:
                continue
            if enabled_key is not None:
                enabled_raw = _slot_value(raw, enabled_key, index)
                if not parse_bool_env(enabled_raw, default=True):
                    continue
            names.append(name)
            if alias:
                aliases[normalize_alias_key(alias)] = name
    return names, aliases


def normalize_alias_key(text: str) -> str:
    """Normalize alias text for case-insensitive, whitespace-collapsed lookup."""
    return " ".join(text.strip().lower().split())


def resolve_alias(aliases: dict[str, str], text: str) -> str | None:
    """Resolve a user phrase to a variable name, or None if unknown."""
    if not text or not aliases:
        return None
    return aliases.get(normalize_alias_key(text))


def resolve_commerce_process_alias(profile: CPQProfile, text: str) -> str | None:
    """Resolve a commerce-process alias phrase using the profile map."""
    return resolve_alias(profile.commerce_process_aliases, text)


def resolve_custom_data_table_alias(profile: CPQProfile, text: str) -> str | None:
    """Resolve a data-table alias phrase using the profile map."""
    return resolve_alias(profile.custom_data_table_aliases, text)


def resolve_product_family_alias(profile: CPQProfile, text: str) -> str | None:
    """Resolve a product-family alias phrase using the profile map."""
    return resolve_alias(profile.product_family_aliases, text)


def resolve_product_line_alias(profile: CPQProfile, text: str) -> str | None:
    """Resolve a product-line alias phrase using the profile map."""
    return resolve_alias(profile.product_line_aliases, text)


def resolve_product_model_alias(profile: CPQProfile, text: str) -> str | None:
    """Resolve a product-model alias phrase using the profile map."""
    return resolve_alias(profile.product_model_aliases, text)


def _resolve_customer_knowledge_file(raw: dict[str, str | None]) -> str | None:
    value = (raw.get("CUSTOMER_KNOWLEDGE_FILE") or "").strip()
    return value or None


def _collect_metric_descriptions(raw: dict[str, str | None]) -> dict[str, str]:
    """Parse METRICS_* keys into {NAME: description} (last duplicate wins)."""
    prefix = "METRICS_"
    descriptions: dict[str, str] = {}
    for key, value in raw.items():
        if not key or not key.startswith(prefix):
            continue
        name = key[len(prefix) :].strip().upper()
        if not name:
            continue
        text = (value or "").strip()
        if text:
            descriptions[name] = text
    return descriptions


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


def _coerce_http_timeout(value: float | None) -> float:
    """Host ``CPQ_HTTP_TIMEOUT`` wins; otherwise use profile value or 60s."""
    raw_value = os.environ.get("CPQ_HTTP_TIMEOUT")
    if raw_value is not None and str(raw_value).strip():
        try:
            timeout = float(str(raw_value).strip())
        except ValueError as exc:
            raise ValueError(
                f"Invalid CPQ_HTTP_TIMEOUT={raw_value!r}; use seconds as a number"
            ) from exc
    elif value is None:
        return 60.0
    else:
        timeout = float(value)
    if timeout < 5.0 or timeout > 3600.0:
        raise ValueError(
            f"HTTP_TIMEOUT/CPQ_HTTP_TIMEOUT={timeout} out of range; use 5–3600 seconds"
        )
    return timeout


def _host_bool_override(env_name: str, file_value: bool, *, default: bool) -> bool:
    if os.environ.get(env_name) is not None:
        return parse_bool_env(os.environ.get(env_name), default=default)
    return file_value


def _load_profile_from_yaml(
    customer_id: str,
    path: Path,
    environment: EnvironmentName | None,
    credential_index: int | None,
) -> CPQProfile:
    from oracle_cpq_mcp.core.local_data import parse_local_data_policy
    from oracle_cpq_mcp.core.profile_yaml import (
        commerce_from_catalog,
        data_tables_from_catalog,
        enabled_product_families,
        load_profile_document,
        product_family_aliases_from_tree,
    )

    document = load_profile_document(path)
    active_env: EnvironmentName = (
        environment
        or os.environ.get("CPQ_ENVIRONMENT")  # type: ignore[assignment]
        or document.default_environment
    )
    if active_env not in ("dev", "test", "prod"):
        raise ValueError(f"Invalid environment '{active_env}'. Use dev, test, or prod.")

    env_block = document.environments.get(active_env)
    if env_block is None or not env_block.url:
        raise ValueError(
            f"Profile '{customer_id}' is missing environments.{active_env}.url "
            f"in {path}"
        )
    if not env_block.enabled:
        raise ValueError(
            f"Profile '{customer_id}' environment '{active_env}' is disabled "
            f"(environments.{active_env}.enabled=false in {path}). "
            "Pick another environment or set enabled: true."
        )
    if not env_block.credentials:
        raise ValueError(
            f"Profile '{customer_id}' is missing environments.{active_env}.credentials "
            f"in {path}"
        )

    credentials = [
        CredentialSet(username=item.username, password=item.password)
        for item in env_block.credentials
    ]
    resolved_index = _resolve_credential_index(credential_index, len(credentials))

    catalog = document.as_catalog()
    commerce_names, commerce_aliases = commerce_from_catalog(catalog)
    table_names, table_aliases = data_tables_from_catalog(catalog)
    product_families = enabled_product_families(catalog.product_families)
    family_aliases, line_aliases, model_aliases = product_family_aliases_from_tree(
        product_families
    )

    read_only = _host_bool_override("CPQ_READ_ONLY", document.read_only, default=True)
    refined_prompt = _host_bool_override(
        "CPQ_REFINED_PROMPT", document.refined_prompt, default=True
    )
    auto_save = _host_bool_override(
        "CPQ_AUTO_SAVE_REFINED_PROMPT",
        document.auto_save_refined_prompt,
        default=False,
    )
    debug_mode = _host_bool_override(
        "CPQ_DEBUG_MODE", document.debug_mode, default=True
    )

    if os.environ.get("CPQ_LOCAL_DATA_POLICY") is not None:
        local_policy = parse_local_data_policy(
            os.environ.get("CPQ_LOCAL_DATA_POLICY"), default="ask"
        )
    else:
        local_policy = parse_local_data_policy(
            document.local_data_policy, default="ask"
        )

    if os.environ.get("CPQ_POST_RESPONSE_EXPORT") is not None:
        export_policy = _resolve_post_response_export(
            {"POST_RESPONSE_EXPORT": os.environ.get("CPQ_POST_RESPONSE_EXPORT")}
        )
    else:
        export_policy = _resolve_post_response_export(
            {"POST_RESPONSE_EXPORT": document.post_response_export}
        )

    return CPQProfile(
        customer_name=document.customer_name or customer_id,
        customer_id=customer_id,
        environment=active_env,
        base_url=env_block.url,
        rest_version=document.rest_api_version or "v18",
        company_login_name=document.company_login_name or "_host",
        credentials=credentials,
        credential_index=resolved_index,
        custom_data_table_names=table_names,
        commerce_process_var_names=commerce_names,
        customer_knowledge_file=document.customer_knowledge_file,
        commerce_process_aliases=commerce_aliases,
        custom_data_table_aliases=table_aliases,
        read_only=read_only,
        refined_prompt=refined_prompt,
        auto_save_refined_prompt=auto_save,
        debug_mode=debug_mode,
        local_data_policy=local_policy,
        post_response_export=export_policy,
        http_timeout=_coerce_http_timeout(document.http_timeout),
        metric_descriptions=dict(document.metrics),
        product_families=product_families,
        product_family_aliases=family_aliases,
        product_line_aliases=line_aliases,
        product_model_aliases=model_aliases,
        catalog_source="profile_yaml",
        profile_file_kind="yaml",
    )


def _load_profile_from_env(
    customer_id: str,
    path: Path,
    environment: EnvironmentName | None,
    credential_index: int | None,
) -> CPQProfile:
    raw = dotenv_values(path)

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

    commerce_names, commerce_aliases = pair_aliases_from_raw(
        raw,
        name_key="COMMERCE_PROCESS_VAR_NAME",
        alias_key="COMMERCE_PROCESS_ALIAS",
        enabled_key="COMMERCE_PROCESS_ENABLED",
    )
    table_names, table_aliases = pair_aliases_from_raw(
        raw, name_key="CUSTOM_DATA_TABLE_NAME", alias_key="CUSTOM_DATA_TABLE_ALIAS"
    )
    metric_descriptions = _collect_metric_descriptions(raw)

    from oracle_cpq_mcp.core.catalog import (
        commerce_from_catalog,
        data_tables_from_catalog,
        enabled_product_families,
        load_catalog,
        parse_flat_product_families,
        product_family_aliases_from_tree,
    )

    catalog = load_catalog(customer_id)
    catalog_source: CatalogSource = "none"
    product_families: list[CatalogProductFamily] = []

    if catalog is not None:
        catalog_source = "catalog_yaml"
        commerce_names, commerce_aliases = commerce_from_catalog(catalog)
        table_names, table_aliases = data_tables_from_catalog(catalog)
        if catalog.metrics:
            metric_descriptions = dict(catalog.metrics)
        product_families = enabled_product_families(catalog.product_families)
    else:
        flat_families = parse_flat_product_families(raw)
        if flat_families:
            catalog_source = "env"
            product_families = enabled_product_families(flat_families)

    family_aliases, line_aliases, model_aliases = product_family_aliases_from_tree(
        product_families
    )

    return CPQProfile(
        customer_name=raw.get("CUSTOMER_NAME") or customer_id,
        customer_id=customer_id,
        environment=active_env,
        base_url=base_url,
        rest_version=raw.get("REST_API_VERSION") or "v18",
        company_login_name=raw.get("COMPANY_LOGIN_NAME") or "_host",
        credentials=credentials,
        credential_index=resolved_index,
        custom_data_table_names=table_names,
        commerce_process_var_names=commerce_names,
        customer_knowledge_file=_resolve_customer_knowledge_file(raw),
        commerce_process_aliases=commerce_aliases,
        custom_data_table_aliases=table_aliases,
        read_only=_resolve_read_only(raw),
        refined_prompt=_resolve_refined_prompt(raw),
        auto_save_refined_prompt=_resolve_auto_save_refined_prompt(raw),
        debug_mode=_resolve_debug_mode(raw),
        local_data_policy=_resolve_local_data_policy(raw),
        post_response_export=_resolve_post_response_export(raw),
        http_timeout=_resolve_http_timeout(raw),
        metric_descriptions=metric_descriptions,
        product_families=product_families,
        product_family_aliases=family_aliases,
        product_line_aliases=line_aliases,
        product_model_aliases=model_aliases,
        catalog_source=catalog_source,
        profile_file_kind="env",
    )


def load_profile(
    customer_id: str | None = None,
    environment: EnvironmentName | None = None,
    credential_index: int | None = None,
) -> CPQProfile:
    """Load `.config/<id>.yaml` when present, else legacy `.env` (+ optional catalog)."""
    customer_id = customer_id or os.environ.get("CPQ_CUSTOMER_PROFILE", "mycompany")
    path = resolve_profile_path(customer_id)
    if path.suffix.lower() in (".yaml", ".yml"):
        return _load_profile_from_yaml(
            customer_id, path, environment, credential_index
        )
    return _load_profile_from_env(customer_id, path, environment, credential_index)
