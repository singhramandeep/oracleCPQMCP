"""Full customer profile YAML (secrets + flags + catalog in one file)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from oracle_cpq_mcp.core.catalog import (
    CatalogCommerceProcess,
    CatalogDataTable,
    CatalogProductFamily,
    ProfileCatalog,
    catalog_from_flat_env,
    commerce_from_catalog,
    data_tables_from_catalog,
    enabled_product_families,
    product_family_aliases_from_tree,
)

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

EnvironmentName = Literal["dev", "test", "prod"]
ProfileMode = Literal["standalone", "fusion"]
AuthMode = Literal["basic", "bearer"]
HostedMode = Literal["standalone", "fusion"]

# Current profile YAML format version (bump when template gains fields).
PROFILE_YAML_FORMAT_VERSION = 1.06

# Allowlisted env-style keys → YAML field names for in-place updates.
PROFILE_YAML_WRITABLE_FIELDS: dict[str, str] = {
    "AUTO_SAVE_REFINED_PROMPT": "auto_save_refined_prompt",
    "LOCAL_DATA_POLICY": "local_data_policy",
    "POST_RESPONSE_EXPORT": "post_response_export",
    "CUSTOMER_KNOWLEDGE_FILE": "customer_knowledge_file",
}

# Canonical Fusion CX module names (case-insensitive match on load).
FUSION_MODULE_ALLOWLIST: tuple[str, ...] = (
    "Sales",
    "PRM",
    "Service",
    "Field Service",
    "Subscription",
    "Incentive Compensation",
)
# YAML display name → catalog cx_module / domain slug.
FUSION_MODULE_SLUGS: dict[str, str] = {
    "Sales": "sales",
    "PRM": "prm",
    "Service": "service",
    "Field Service": "field_service",
    "Subscription": "subscription",
    "Incentive Compensation": "incentive_compensation",
}
_FUSION_MODULE_BY_KEY: dict[str, str] = {
    name.casefold(): name for name in FUSION_MODULE_ALLOWLIST
}


class ProfileCredential(BaseModel):
    """One Basic Auth pair inside a profile YAML environment block."""

    username: str
    password: str = Field(repr=False)

    @field_validator("username", "password")
    @classmethod
    def strip_required(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("username and password must be non-empty")
        return text


def normalize_auth_mode(value: Any) -> AuthMode:
    """Default auth is basic; bearer aliases: oauth, token."""
    if value is None or (isinstance(value, str) and not str(value).strip()):
        return "basic"
    text = str(value).strip().lower()
    if text == "basic":
        return "basic"
    if text in ("bearer", "oauth", "token"):
        return "bearer"
    raise ValueError("auth must be 'basic' or 'bearer'")


def normalize_hosted_mode(value: Any) -> HostedMode:
    """CPQ REST prefix: standalone → /rest; fusion → /cpq/rest."""
    return normalize_cpq_mode(value)


def _strip_optional_oauth(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


class ProductConnection(BaseModel):
    """One product connection (CPQ or CX Fusion) inside an environment."""

    enabled: bool = True
    url: str | None = None
    auth: AuthMode = "basic"
    hosted: HostedMode = "standalone"
    credentials: list[ProfileCredential] = Field(default_factory=list)
    oauth_token_url: str | None = None
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = Field(default=None, repr=False)
    oauth_scope: str | None = None
    modules: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def migrate_flat_username_password(cls, data: Any) -> Any:
        """Lift flat username/password into credentials when credentials omitted."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        flat_user = out.pop("username", None)
        flat_pass = out.pop("password", None)
        creds = out.get("credentials")
        has_creds = isinstance(creds, list) and len(creds) > 0
        if flat_user is not None or flat_pass is not None:
            if has_creds:
                raise ValueError(
                    "Use either credentials: [{username, password}] or flat "
                    "username/password — not both"
                )
            user_text = str(flat_user or "").strip()
            pass_text = str(flat_pass or "").strip()
            if user_text or pass_text:
                out["credentials"] = [
                    {"username": user_text, "password": pass_text}
                ]
        return out

    @field_validator("url", mode="before")
    @classmethod
    def strip_url(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip().rstrip("/")
        return text or None

    @field_validator("auth", mode="before")
    @classmethod
    def normalize_auth_field(cls, value: Any) -> str:
        return normalize_auth_mode(value)

    @field_validator("hosted", mode="before")
    @classmethod
    def normalize_hosted_field(cls, value: Any) -> str:
        return normalize_hosted_mode(value)

    @field_validator(
        "oauth_token_url",
        "oauth_client_id",
        "oauth_client_secret",
        "oauth_scope",
        mode="before",
    )
    @classmethod
    def strip_optional_oauth(cls, value: Any) -> str | None:
        return _strip_optional_oauth(value)

    @field_validator("modules", mode="before")
    @classmethod
    def normalize_modules_field(cls, value: Any) -> list[str]:
        return normalize_fusion_modules(value)


class ProfileEnvironment(BaseModel):
    """One env (dev/test/prod) with optional CPQ and/or CX Fusion connections."""

    enabled: bool = True
    cpq: ProductConnection | None = None
    cx: ProductConnection | None = None

    @property
    def url(self) -> str:
        """Legacy: CPQ URL, else CX URL."""
        if self.cpq and self.cpq.url:
            return self.cpq.url
        if self.cx and self.cx.url:
            return self.cx.url
        return ""

    @property
    def credentials(self) -> list[ProfileCredential]:
        if self.cpq:
            return self.cpq.credentials
        return []

    @property
    def oauth_token_url(self) -> str | None:
        return self.cpq.oauth_token_url if self.cpq else None

    @property
    def oauth_client_id(self) -> str | None:
        return self.cpq.oauth_client_id if self.cpq else None

    @property
    def oauth_client_secret(self) -> str | None:
        return self.cpq.oauth_client_secret if self.cpq else None

    @property
    def oauth_scope(self) -> str | None:
        return self.cpq.oauth_scope if self.cpq else None


def normalize_cpq_mode(value: Any) -> ProfileMode:
    """Normalize CPQ Mode: blank/cpq → standalone; standalone|fusion unchanged."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return "standalone"
    text = str(value).strip().lower()
    if text in ("cpq", "standalone"):
        return "standalone"
    if text == "fusion":
        return "fusion"
    raise ValueError(
        "cpq_mode must be 'standalone' or 'fusion' "
        "(legacy 'cpq' and 'mode' alias map to standalone / fusion)"
    )


def _coerce_bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off", ""):
        return False
    raise ValueError(f"boolean field must be true/false, got {value!r}")


def normalize_fusion_modules(value: Any) -> list[str]:
    """Coerce blank / CSV string / list → sorted unique allowlisted module names."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_parts = [part.strip() for part in value.split(",")]
        tokens = [part for part in raw_parts if part]
    elif isinstance(value, (list, tuple)):
        tokens = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if not text:
                continue
            # Allow nested CSV inside list items.
            if "," in text:
                tokens.extend(p.strip() for p in text.split(",") if p.strip())
            else:
                tokens.append(text)
    else:
        raise ValueError(
            "fusion_modules must be a comma-separated string or a YAML list "
            f"(got {type(value).__name__})"
        )

    resolved: list[str] = []
    unknown: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        canonical = _FUSION_MODULE_BY_KEY.get(token.casefold())
        if canonical is None:
            unknown.append(token)
            continue
        if canonical not in seen:
            seen.add(canonical)
            resolved.append(canonical)
    if unknown:
        allowed = ", ".join(FUSION_MODULE_ALLOWLIST)
        bad = ", ".join(repr(u) for u in unknown)
        raise ValueError(
            f"Unknown fusion_modules value(s): {bad}. Allowed: {allowed}"
        )
    # Stable canonical order (allowlist order), not input order.
    order = {name: index for index, name in enumerate(FUSION_MODULE_ALLOWLIST)}
    return sorted(resolved, key=lambda name: order[name])


_LEGACY_ENV_KEYS = (
    "url",
    "credentials",
    "oauth_token_url",
    "oauth_client_id",
    "oauth_client_secret",
    "oauth_scope",
)


def _migrate_legacy_environment(
    env_block: Any, *, hosted: HostedMode, top_modules: list[str]
) -> Any:
    """Lift flat env url/credentials/oauth_* into ``cpq`` when nested blocks are absent."""
    if not isinstance(env_block, dict):
        return env_block
    out = dict(env_block)
    if "cpq" not in out and any(key in out for key in _LEGACY_ENV_KEYS):
        oauth_present = any(
            str(out.get(key) or "").strip()
            for key in (
                "oauth_token_url",
                "oauth_client_id",
                "oauth_client_secret",
                "oauth_scope",
            )
        )
        auth: AuthMode = "bearer" if hosted == "fusion" and oauth_present else "basic"
        out["cpq"] = {
            "enabled": True,
            "url": out.pop("url", None),
            "auth": auth,
            "hosted": hosted,
            "credentials": out.pop("credentials", []) or [],
            "oauth_token_url": out.pop("oauth_token_url", None),
            "oauth_client_id": out.pop("oauth_client_id", None),
            "oauth_client_secret": out.pop("oauth_client_secret", None),
            "oauth_scope": out.pop("oauth_scope", None),
        }
    cx_block = out.get("cx")
    if isinstance(cx_block, dict) and top_modules and not cx_block.get("modules"):
        cx = dict(cx_block)
        cx["modules"] = top_modules
        out["cx"] = cx
    return out


def _validate_product_connection(
    conn: ProductConnection, *, prefix: str, require_modules: bool
) -> None:
    if not conn.url:
        raise ValueError(f"{prefix}.url is required when enabled")
    if conn.auth == "bearer":
        missing = [
            field
            for field, val in (
                ("oauth_token_url", conn.oauth_token_url),
                ("oauth_client_id", conn.oauth_client_id),
                ("oauth_client_secret", conn.oauth_client_secret),
                ("oauth_scope", conn.oauth_scope),
            )
            if not val
        ]
        if missing:
            raise ValueError(
                f"{prefix}.auth: bearer requires {prefix}."
                + ", ".join(missing)
                + " (credentials may be omitted)"
            )
    elif not conn.credentials:
        raise ValueError(
            f"{prefix}.auth: basic requires {prefix}.credentials "
            "(oauth_* fields may be omitted)"
        )
    if require_modules and not conn.modules:
        allowed = ", ".join(FUSION_MODULE_ALLOWLIST)
        raise ValueError(
            f"{prefix}.modules must list at least one CX module when cx is enabled. "
            f"Allowed: {allowed}"
        )


class CustomerProfileDocument(BaseModel):
    """Complete `.config/<id>.yaml` document (secrets, flags, catalog)."""

    version: float = PROFILE_YAML_FORMAT_VERSION
    customer_name: str | None = None
    cpq_mode: ProfileMode = "standalone"
    fusion_enabled: bool = False
    fusion_modules: list[str] = Field(default_factory=list)
    frugal_mode: bool = False
    default_environment: EnvironmentName = "dev"
    rest_api_version: str = "v18"
    company_login_name: str = "_host"
    read_only: bool = True
    debug_mode: bool = True
    refined_prompt: bool = True
    auto_save_refined_prompt: bool = False
    include_refined_prompt_in_documents: bool = True
    local_data_policy: str = "prefer"
    post_response_export: str = "always_excel"
    http_timeout: float | None = None
    customer_knowledge_file: str | None = None
    environments: dict[str, ProfileEnvironment] = Field(default_factory=dict)
    commerce_processes: list[CatalogCommerceProcess] = Field(default_factory=list)
    data_tables: list[CatalogDataTable] = Field(default_factory=list)
    metrics: dict[str, str] = Field(default_factory=dict)
    product_families: list[CatalogProductFamily] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def alias_mode_and_migrate_fusion_enabled(cls, data: Any) -> Any:
        """Map legacy ``mode`` → ``cpq_mode``; nest legacy env url/auth under ``cpq``."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        has_fusion_enabled_key = "fusion_enabled" in out
        if "cpq_mode" not in out and "mode" in out:
            out["cpq_mode"] = out.pop("mode")
        elif "mode" in out and "cpq_mode" in out:
            out.pop("mode", None)
        if "cpq_mode" in out:
            out["cpq_mode"] = normalize_cpq_mode(out.get("cpq_mode"))
        else:
            out["cpq_mode"] = "standalone"
        if has_fusion_enabled_key:
            out["fusion_enabled"] = _coerce_bool(
                out.get("fusion_enabled"), default=False
            )
        elif out["cpq_mode"] == "fusion":
            # Legacy mode/cpq_mode: fusion without fusion_enabled → active Fusion.
            out["fusion_enabled"] = True
        else:
            out["fusion_enabled"] = False

        hosted: HostedMode = (
            "fusion" if out["cpq_mode"] == "fusion" and out["fusion_enabled"] else "standalone"
        )
        top_modules = normalize_fusion_modules(out.get("fusion_modules"))
        environments = out.get("environments")
        if isinstance(environments, dict):
            migrated: dict[str, Any] = {}
            for env_name, env_block in environments.items():
                migrated[env_name] = _migrate_legacy_environment(
                    env_block, hosted=hosted, top_modules=top_modules
                )
            out["environments"] = migrated
        return out

    @field_validator("cpq_mode", mode="before")
    @classmethod
    def normalize_cpq_mode_field(cls, value: Any) -> str:
        return normalize_cpq_mode(value)

    @field_validator("fusion_modules", mode="before")
    @classmethod
    def normalize_fusion_modules_field(cls, value: Any) -> list[str]:
        return normalize_fusion_modules(value)

    @field_validator("metrics", mode="before")
    @classmethod
    def normalize_metric_keys(cls, value: Any) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError("metrics must be a mapping of NAME → description")
        out: dict[str, str] = {}
        for key, text in value.items():
            name = str(key).strip().upper()
            description = str(text or "").strip()
            if name and description:
                out[name] = description
        return out

    @property
    def uses_fusion(self) -> bool:
        return self.cpq_mode == "fusion" and self.fusion_enabled

    @model_validator(mode="after")
    def validate_connections_and_sync_cpq_flags(self) -> CustomerProfileDocument:
        """Validate cpq/cx auth; derive top-level cpq_mode from nested CPQ hosted."""
        hosted_fusion = False
        for env_name, block in self.environments.items():
            if not block.enabled:
                continue
            cpq_on = block.cpq is not None and block.cpq.enabled
            cx_on = block.cx is not None and block.cx.enabled
            if not cpq_on and not cx_on:
                raise ValueError(
                    f"environments.{env_name} must enable cpq and/or cx "
                    "(set cpq.enabled or cx.enabled true)"
                )
            if cpq_on:
                assert block.cpq is not None
                _validate_product_connection(
                    block.cpq, prefix=f"environments.{env_name}.cpq", require_modules=False
                )
                if block.cpq.hosted == "fusion":
                    hosted_fusion = True
            if cx_on:
                assert block.cx is not None
                _validate_product_connection(
                    block.cx, prefix=f"environments.{env_name}.cx", require_modules=True
                )
        object.__setattr__(self, "cpq_mode", "fusion" if hosted_fusion else "standalone")
        object.__setattr__(self, "fusion_enabled", hosted_fusion)
        return self

    def as_catalog(self) -> ProfileCatalog:
        # ProfileCatalog.version is the catalog schema (int), not the profile
        # YAML format version (float, e.g. 1.02).
        return ProfileCatalog(
            version=1,
            commerce_processes=self.commerce_processes,
            data_tables=self.data_tables,
            metrics=self.metrics,
            product_families=self.product_families,
        )


def profile_yaml_path(customer_id: str, *, config_directory: Path | None = None) -> Path:
    """Return `.config/<customer_id>.yaml` path (may not exist)."""
    from oracle_cpq_mcp.core.config import config_dir

    base = config_directory if config_directory is not None else config_dir()
    return base / f"{customer_id}.yaml"


def load_profile_document(path: Path) -> CustomerProfileDocument:
    """Parse and validate a full profile YAML file."""
    if yaml is None:
        raise ImportError(
            "PyYAML is required to load profile YAML. "
            "Install with: pip install 'PyYAML>=6.0.0'"
        )
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        raise ValueError(f"Profile YAML is empty: {path}")
    if not isinstance(data, dict):
        raise ValueError(f"Profile YAML root must be a mapping: {path}")
    return CustomerProfileDocument.model_validate(data)


def dump_profile_yaml(document: CustomerProfileDocument) -> str:
    """Serialize a full profile document to YAML text."""
    if yaml is None:
        raise ImportError(
            "PyYAML is required to write profile YAML. "
            "Install with: pip install 'PyYAML>=6.0.0'"
        )
    payload = document.model_dump(mode="python", exclude_none=True)
    return yaml.safe_dump(
        payload,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


def update_profile_yaml_key(path: Path, env_key: str, value: str) -> Path:
    """Update an allowlisted flag on a profile YAML file (preserves other keys)."""
    if env_key not in PROFILE_YAML_WRITABLE_FIELDS:
        raise ValueError(
            f"Refusing to write profile YAML key for {env_key!r}; allowlist is "
            f"{sorted(PROFILE_YAML_WRITABLE_FIELDS)}"
        )
    if yaml is None:
        raise ImportError(
            "PyYAML is required to update profile YAML. "
            "Install with: pip install 'PyYAML>=6.0.0'"
        )
    if not path.is_file():
        raise FileNotFoundError(f"Customer profile not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"Profile YAML root must be a mapping: {path}")

    field = PROFILE_YAML_WRITABLE_FIELDS[env_key]
    # Keep boolean-looking strings as bools for read_only-style consistency where useful.
    if env_key == "AUTO_SAVE_REFINED_PROMPT":
        normalized = value.strip().lower()
        data[field] = normalized in ("1", "true", "yes", "on")
    else:
        data[field] = value.strip()

    path.write_text(
        yaml.safe_dump(
            data,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def _credential_pairs_from_raw(
    raw: dict[str, str | None], prefix: str
) -> list[ProfileCredential]:
    from oracle_cpq_mcp.core.config import _collect_credential_suffixes

    credentials: list[ProfileCredential] = []
    for suffix in _collect_credential_suffixes(raw, prefix):
        username = (raw.get(f"{prefix}_USERNAME{suffix}") or "").strip()
        password = (raw.get(f"{prefix}_PASSWORD{suffix}") or "").strip()
        if not username and not password:
            continue
        if not username or not password:
            continue
        credentials.append(ProfileCredential(username=username, password=password))
    return credentials


def profile_document_from_flat_env(raw: dict[str, str | None]) -> CustomerProfileDocument:
    """Build a full profile YAML document from a legacy flat `.env` map."""
    from oracle_cpq_mcp.core.config import parse_bool_env

    catalog = catalog_from_flat_env(raw)
    environments: dict[str, ProfileEnvironment] = {}
    for env_name in ("dev", "test", "prod"):
        prefix = env_name.upper()
        url = (raw.get(f"{prefix}_URL") or "").strip()
        creds = _credential_pairs_from_raw(raw, prefix)
        if not url and not creds:
            continue
        if not url:
            continue
        environments[env_name] = ProfileEnvironment(
            enabled=True,
            cpq=ProductConnection(
                enabled=True,
                url=url,
                auth="basic",
                hosted="standalone",
                credentials=creds,
            ),
        )

    default_env = (raw.get("DEFAULT_ENVIRONMENT") or "dev").strip().lower()
    if default_env not in ("dev", "test", "prod"):
        default_env = "dev"

    knowledge = (raw.get("CUSTOMER_KNOWLEDGE_FILE") or "").strip() or None
    http_raw = (raw.get("HTTP_TIMEOUT") or "").strip()
    http_timeout: float | None = None
    if http_raw:
        http_timeout = float(http_raw)

    return CustomerProfileDocument(
        version=PROFILE_YAML_FORMAT_VERSION,
        customer_name=(raw.get("CUSTOMER_NAME") or "").strip() or None,
        default_environment=default_env,  # type: ignore[arg-type]
        rest_api_version=(raw.get("REST_API_VERSION") or "v18").strip() or "v18",
        company_login_name=(raw.get("COMPANY_LOGIN_NAME") or "_host").strip() or "_host",
        read_only=parse_bool_env(raw.get("READ_ONLY"), default=True),
        debug_mode=parse_bool_env(raw.get("DEBUG_MODE"), default=True),
        refined_prompt=parse_bool_env(raw.get("REFINED_PROMPT"), default=True),
        auto_save_refined_prompt=parse_bool_env(
            raw.get("AUTO_SAVE_REFINED_PROMPT"), default=False
        ),
        include_refined_prompt_in_documents=parse_bool_env(
            raw.get("INCLUDE_REFINED_PROMPT_IN_DOCUMENTS"), default=True
        ),
        local_data_policy=(raw.get("LOCAL_DATA_POLICY") or "prefer").strip()
        or "prefer",
        post_response_export=(raw.get("POST_RESPONSE_EXPORT") or "always_excel").strip()
        or "always_excel",
        http_timeout=http_timeout,
        customer_knowledge_file=knowledge,
        environments=environments,
        commerce_processes=catalog.commerce_processes,
        data_tables=catalog.data_tables,
        metrics=catalog.metrics,
        product_families=catalog.product_families,
    )
