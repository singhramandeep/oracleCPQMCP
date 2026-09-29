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
ProfileMode = Literal["cpq", "fusion"]

# Current profile YAML format version (bump when template gains fields).
PROFILE_YAML_FORMAT_VERSION = 1.02

# Allowlisted env-style keys → YAML field names for in-place updates.
PROFILE_YAML_WRITABLE_FIELDS: dict[str, str] = {
    "AUTO_SAVE_REFINED_PROMPT": "auto_save_refined_prompt",
    "LOCAL_DATA_POLICY": "local_data_policy",
    "POST_RESPONSE_EXPORT": "post_response_export",
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


class ProfileEnvironment(BaseModel):
    """URL + auth material for one CPQ / Fusion environment."""

    url: str
    credentials: list[ProfileCredential] = Field(default_factory=list)
    enabled: bool = True
    oauth_token_url: str | None = None
    oauth_client_id: str | None = None
    oauth_client_secret: str | None = Field(default=None, repr=False)
    oauth_scope: str | None = None

    @field_validator("url")
    @classmethod
    def strip_url(cls, value: str) -> str:
        return value.strip().rstrip("/")

    @field_validator(
        "oauth_token_url",
        "oauth_client_id",
        "oauth_client_secret",
        "oauth_scope",
        mode="before",
    )
    @classmethod
    def strip_optional_oauth(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class CustomerProfileDocument(BaseModel):
    """Complete `.config/<id>.yaml` document (secrets, flags, catalog)."""

    version: float = PROFILE_YAML_FORMAT_VERSION
    customer_name: str | None = None
    mode: ProfileMode = "cpq"
    default_environment: EnvironmentName = "dev"
    rest_api_version: str = "v18"
    company_login_name: str = "_host"
    read_only: bool = True
    debug_mode: bool = True
    refined_prompt: bool = True
    auto_save_refined_prompt: bool = False
    local_data_policy: str = "prefer"
    post_response_export: str = "always_excel"
    http_timeout: float | None = None
    customer_knowledge_file: str | None = None
    environments: dict[str, ProfileEnvironment] = Field(default_factory=dict)
    commerce_processes: list[CatalogCommerceProcess] = Field(default_factory=list)
    data_tables: list[CatalogDataTable] = Field(default_factory=list)
    metrics: dict[str, str] = Field(default_factory=dict)
    product_families: list[CatalogProductFamily] = Field(default_factory=list)

    @field_validator("mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: Any) -> str:
        """Normalize connection mode.

        Missing/blank and ``standalone`` map to ``cpq`` (Basic Auth + ``/rest/{version}``).
        ``fusion`` keeps Bearer + ``/cpq/rest/{version}``.
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return "cpq"
        text = str(value).strip().lower()
        if text in ("cpq", "standalone"):
            return "cpq"
        if text == "fusion":
            return "fusion"
        raise ValueError(
            "mode must be 'cpq', 'standalone' (alias for cpq), or 'fusion'"
        )

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

    @model_validator(mode="after")
    def validate_mode_auth_fields(self) -> CustomerProfileDocument:
        """Require auth fields on every enabled env based on mode.

        mode=fusion → oauth_* required (credentials may be omitted).
        mode=cpq → credentials required (oauth_* may be omitted).
        """
        for env_name, block in self.environments.items():
            if not block.enabled:
                continue
            if self.mode == "fusion":
                missing = [
                    field
                    for field, val in (
                        ("oauth_token_url", block.oauth_token_url),
                        ("oauth_client_id", block.oauth_client_id),
                        ("oauth_client_secret", block.oauth_client_secret),
                        ("oauth_scope", block.oauth_scope),
                    )
                    if not val
                ]
                if missing:
                    raise ValueError(
                        f"mode=fusion requires environments.{env_name}."
                        + ", ".join(missing)
                        + " (credentials may be omitted)"
                    )
            else:
                if not block.credentials:
                    raise ValueError(
                        f"mode=cpq requires environments.{env_name}.credentials "
                        "(oauth_* fields may be omitted)"
                    )
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
        environments[env_name] = ProfileEnvironment(url=url, credentials=creds)

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
