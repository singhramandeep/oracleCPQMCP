"""Profile catalog models and loaders (YAML sidecar + flat-env fallbacks)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

try:
    import yaml
except ImportError:  # pragma: no cover - dependency declared in pyproject
    yaml = None  # type: ignore[assignment]


def _normalize_alias_key(text: str) -> str:
    """Local copy to avoid circular import with config.py."""
    return " ".join(text.strip().lower().split())


def _parse_bool_env(value: str | None, *, default: bool) -> bool:
    from oracle_cpq_mcp.core.config import parse_bool_env

    return parse_bool_env(value, default=default)


class CatalogModelNode(BaseModel):
    """One product model under a product line."""

    var_name: str
    name: str | None = None
    alias: str | None = None
    enabled: bool = True

    @field_validator("var_name")
    @classmethod
    def strip_var_name(cls, value: str) -> str:
        return value.strip()


class CatalogProductLine(BaseModel):
    """One product line under a product family."""

    var_name: str
    name: str | None = None
    alias: str | None = None
    enabled: bool = True
    models: list[CatalogModelNode] = Field(default_factory=list)

    @field_validator("var_name")
    @classmethod
    def strip_var_name(cls, value: str) -> str:
        return value.strip()


class CatalogProductFamily(BaseModel):
    """One product family with nested lines and models."""

    var_name: str
    name: str | None = None
    alias: str | None = None
    enabled: bool = True
    lines: list[CatalogProductLine] = Field(default_factory=list)

    @field_validator("var_name")
    @classmethod
    def strip_var_name(cls, value: str) -> str:
        return value.strip()


class CatalogCommerceProcess(BaseModel):
    """Commerce process entry in the profile catalog."""

    var_name: str
    alias: str | None = None
    enabled: bool = True

    @field_validator("var_name")
    @classmethod
    def strip_var_name(cls, value: str) -> str:
        return value.strip()


class CatalogDataTable(BaseModel):
    """Custom data table entry in the profile catalog."""

    name: str
    alias: str | None = None
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class ProfileCatalog(BaseModel):
    """Structured catalog loaded from `.config/<id>.catalog.yaml`."""

    version: int = 1
    commerce_processes: list[CatalogCommerceProcess] = Field(default_factory=list)
    data_tables: list[CatalogDataTable] = Field(default_factory=list)
    metrics: dict[str, str] = Field(default_factory=dict)
    product_families: list[CatalogProductFamily] = Field(default_factory=list)

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


def catalog_path(customer_id: str, *, config_directory: Path | None = None) -> Path:
    """Return `.config/<customer_id>.catalog.yaml` path (may not exist)."""
    from oracle_cpq_mcp.core.config import config_dir

    base = config_directory if config_directory is not None else config_dir()
    return base / f"{customer_id}.catalog.yaml"


def load_catalog_file(path: Path) -> ProfileCatalog:
    """Parse and validate a catalog YAML file."""
    if yaml is None:
        raise ImportError(
            "PyYAML is required to load profile catalogs. "
            "Install with: pip install 'PyYAML>=6.0.0'"
        )
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return ProfileCatalog()
    if not isinstance(data, dict):
        raise ValueError(f"Catalog root must be a mapping: {path}")
    return ProfileCatalog.model_validate(data)


def load_catalog(
    customer_id: str,
    *,
    config_directory: Path | None = None,
) -> ProfileCatalog | None:
    """Load `.config/<id>.catalog.yaml` when present; otherwise return None."""
    path = catalog_path(customer_id, config_directory=config_directory)
    if not path.is_file():
        return None
    return load_catalog_file(path)


def dump_catalog_yaml(catalog: ProfileCatalog) -> str:
    """Serialize a catalog to YAML text (for migrate script / examples)."""
    if yaml is None:
        raise ImportError(
            "PyYAML is required to write profile catalogs. "
            "Install with: pip install 'PyYAML>=6.0.0'"
        )
    payload = catalog.model_dump(mode="python", exclude_none=False)
    return yaml.safe_dump(
        payload,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


def commerce_from_catalog(
    catalog: ProfileCatalog,
) -> tuple[list[str], dict[str, str]]:
    """Return (var_names, alias→var_name) for enabled commerce processes."""
    names: list[str] = []
    aliases: dict[str, str] = {}
    for process in catalog.commerce_processes:
        if not process.enabled or not process.var_name:
            continue
        names.append(process.var_name)
        if process.alias and process.alias.strip():
            aliases[_normalize_alias_key(process.alias)] = process.var_name
    return names, aliases


def data_tables_from_catalog(
    catalog: ProfileCatalog,
) -> tuple[list[str], dict[str, str]]:
    """Return (table_names, alias→name) for enabled catalog data tables."""
    names: list[str] = []
    aliases: dict[str, str] = {}
    for table in catalog.data_tables:
        if not table.enabled or not table.name:
            continue
        names.append(table.name)
        if table.alias and table.alias.strip():
            aliases[_normalize_alias_key(table.alias)] = table.name
    return names, aliases


def product_family_aliases_from_tree(
    families: list[CatalogProductFamily],
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Build family/line/model alias maps from an enabled tree."""
    family_aliases: dict[str, str] = {}
    line_aliases: dict[str, str] = {}
    model_aliases: dict[str, str] = {}
    for family in families:
        if not family.enabled or not family.var_name:
            continue
        if family.alias and family.alias.strip():
            family_aliases[_normalize_alias_key(family.alias)] = family.var_name
        for line in family.lines:
            if not line.enabled or not line.var_name:
                continue
            if line.alias and line.alias.strip():
                line_aliases[_normalize_alias_key(line.alias)] = line.var_name
            for model in line.models:
                if not model.enabled or not model.var_name:
                    continue
                if model.alias and model.alias.strip():
                    model_aliases[_normalize_alias_key(model.alias)] = model.var_name
    return family_aliases, line_aliases, model_aliases


def enabled_product_families(
    families: list[CatalogProductFamily],
) -> list[CatalogProductFamily]:
    """Return families/lines/models with disabled nodes pruned."""
    out: list[CatalogProductFamily] = []
    for family in families:
        if not family.enabled or not family.var_name:
            continue
        lines: list[CatalogProductLine] = []
        for line in family.lines:
            if not line.enabled or not line.var_name:
                continue
            models = [
                model
                for model in line.models
                if model.enabled and model.var_name
            ]
            lines.append(line.model_copy(update={"models": models}))
        out.append(family.model_copy(update={"lines": lines}))
    return out


_FAMILY_VAR_RE = re.compile(r"^PRODUCT_FAMILY_VAR_NAME_(\d+)$")
_FAMILY_NAME_RE = re.compile(r"^PRODUCT_FAMILY_(\d+)_NAME$")
_FAMILY_ALIAS_RE = re.compile(r"^PRODUCT_FAMILY_(\d+)_ALIAS$")
_FAMILY_ENABLED_RE = re.compile(r"^PRODUCT_FAMILY_ENABLED_(\d+)$")
_LINE_VAR_RE = re.compile(r"^PRODUCT_LINE_VAR_NAME_(\d+)_(\d+)$")
_LINE_NAME_RE = re.compile(r"^PRODUCT_LINE_NAME_(\d+)_(\d+)$")
_LINE_ALIAS_RE = re.compile(r"^PRODUCT_LINE_ALIAS_(\d+)_(\d+)$")
_LINE_ENABLED_RE = re.compile(r"^PRODUCT_LINE_ENABLED_(\d+)_(\d+)$")
_MODEL_VAR_RE = re.compile(r"^MODEL_VAR_NAME_(\d+)_(\d+)_(\d+)$")
_MODEL_NAME_RE = re.compile(r"^MODEL_NAME_(\d+)_(\d+)_(\d+)$")
_MODEL_ALIAS_RE = re.compile(r"^MODEL_ALIAS_(\d+)_(\d+)_(\d+)$")
_MODEL_ENABLED_RE = re.compile(r"^MODEL_ENABLED_(\d+)_(\d+)_(\d+)$")


def _slot(raw: dict[str, str | None], key: str) -> str | None:
    return (raw.get(key) or "").strip() or None


def _collect_family_indices(raw: dict[str, str | None]) -> list[int]:
    indices: set[int] = set()
    for key in raw:
        for pattern in (
            _FAMILY_VAR_RE,
            _FAMILY_NAME_RE,
            _FAMILY_ALIAS_RE,
            _FAMILY_ENABLED_RE,
        ):
            match = pattern.match(key)
            if match:
                indices.add(int(match.group(1)))
                break
    return sorted(indices)


def _collect_line_indices(raw: dict[str, str | None], family_index: int) -> list[int]:
    indices: set[int] = set()
    for key in raw:
        for pattern in (_LINE_VAR_RE, _LINE_NAME_RE, _LINE_ALIAS_RE, _LINE_ENABLED_RE):
            match = pattern.match(key)
            if match and int(match.group(1)) == family_index:
                indices.add(int(match.group(2)))
                break
    return sorted(indices)


def _collect_model_indices(
    raw: dict[str, str | None], family_index: int, line_index: int
) -> list[int]:
    indices: set[int] = set()
    for key in raw:
        for pattern in (
            _MODEL_VAR_RE,
            _MODEL_NAME_RE,
            _MODEL_ALIAS_RE,
            _MODEL_ENABLED_RE,
        ):
            match = pattern.match(key)
            if (
                match
                and int(match.group(1)) == family_index
                and int(match.group(2)) == line_index
            ):
                indices.add(int(match.group(3)))
                break
    return sorted(indices)


def parse_flat_product_families(
    raw: dict[str, str | None],
) -> list[CatalogProductFamily]:
    """Parse legacy PRODUCT_FAMILY_* / PRODUCT_LINE_* / MODEL_* flat env keys."""
    families: list[CatalogProductFamily] = []
    for family_index in _collect_family_indices(raw):
        var_name = _slot(raw, f"PRODUCT_FAMILY_VAR_NAME_{family_index}")
        if not var_name:
            continue
        enabled = _parse_bool_env(
            _slot(raw, f"PRODUCT_FAMILY_ENABLED_{family_index}"), default=True
        )
        lines: list[CatalogProductLine] = []
        for line_index in _collect_line_indices(raw, family_index):
            line_var = _slot(raw, f"PRODUCT_LINE_VAR_NAME_{family_index}_{line_index}")
            if not line_var:
                continue
            line_enabled = _parse_bool_env(
                _slot(raw, f"PRODUCT_LINE_ENABLED_{family_index}_{line_index}"),
                default=True,
            )
            models: list[CatalogModelNode] = []
            for model_index in _collect_model_indices(raw, family_index, line_index):
                model_var = _slot(
                    raw,
                    f"MODEL_VAR_NAME_{family_index}_{line_index}_{model_index}",
                )
                if not model_var:
                    continue
                model_enabled = _parse_bool_env(
                    _slot(
                        raw,
                        f"MODEL_ENABLED_{family_index}_{line_index}_{model_index}",
                    ),
                    default=True,
                )
                models.append(
                    CatalogModelNode(
                        var_name=model_var,
                        name=_slot(
                            raw,
                            f"MODEL_NAME_{family_index}_{line_index}_{model_index}",
                        ),
                        alias=_slot(
                            raw,
                            f"MODEL_ALIAS_{family_index}_{line_index}_{model_index}",
                        ),
                        enabled=model_enabled,
                    )
                )
            lines.append(
                CatalogProductLine(
                    var_name=line_var,
                    name=_slot(raw, f"PRODUCT_LINE_NAME_{family_index}_{line_index}"),
                    alias=_slot(raw, f"PRODUCT_LINE_ALIAS_{family_index}_{line_index}"),
                    enabled=line_enabled,
                    models=models,
                )
            )
        families.append(
            CatalogProductFamily(
                var_name=var_name,
                name=_slot(raw, f"PRODUCT_FAMILY_{family_index}_NAME"),
                alias=_slot(raw, f"PRODUCT_FAMILY_{family_index}_ALIAS"),
                enabled=enabled,
                lines=lines,
            )
        )
    return families


def catalog_from_flat_env(raw: dict[str, str | None]) -> ProfileCatalog:
    """Build a ProfileCatalog from flat profile env keys (migration helper)."""
    from oracle_cpq_mcp.core.config import _collect_metric_descriptions

    return ProfileCatalog(
        version=1,
        commerce_processes=_commerce_slots_including_disabled(raw),
        data_tables=_data_table_slots(raw),
        metrics=_collect_metric_descriptions(raw),
        product_families=parse_flat_product_families(raw),
    )


def _commerce_slots_including_disabled(
    raw: dict[str, str | None],
) -> list[CatalogCommerceProcess]:
    from oracle_cpq_mcp.core.config import _max_numbered_index, _slot_value

    max_index = _max_numbered_index(
        raw,
        "COMMERCE_PROCESS_VAR_NAME",
        "COMMERCE_PROCESS_ALIAS",
        "COMMERCE_PROCESS_ENABLED",
    )
    if (
        max_index == 0
        and "COMMERCE_PROCESS_VAR_NAME" not in raw
        and "COMMERCE_PROCESS_ALIAS" not in raw
    ):
        return []
    processes: list[CatalogCommerceProcess] = []
    last = max_index
    if (
        "COMMERCE_PROCESS_VAR_NAME" in raw
        or "COMMERCE_PROCESS_ALIAS" in raw
        or last > 0
    ):
        for index in range(0, last + 1):
            name = _slot_value(raw, "COMMERCE_PROCESS_VAR_NAME", index)
            if not name:
                continue
            alias = _slot_value(raw, "COMMERCE_PROCESS_ALIAS", index)
            enabled = _parse_bool_env(
                _slot_value(raw, "COMMERCE_PROCESS_ENABLED", index), default=True
            )
            processes.append(
                CatalogCommerceProcess(var_name=name, alias=alias, enabled=enabled)
            )
    return processes


def _data_table_slots(raw: dict[str, str | None]) -> list[CatalogDataTable]:
    from oracle_cpq_mcp.core.config import _max_numbered_index, _slot_value

    max_index = _max_numbered_index(
        raw, "CUSTOM_DATA_TABLE_NAME", "CUSTOM_DATA_TABLE_ALIAS"
    )
    if (
        max_index == 0
        and "CUSTOM_DATA_TABLE_NAME" not in raw
        and "CUSTOM_DATA_TABLE_ALIAS" not in raw
    ):
        return []
    tables: list[CatalogDataTable] = []
    last = max_index
    if "CUSTOM_DATA_TABLE_NAME" in raw or "CUSTOM_DATA_TABLE_ALIAS" in raw or last > 0:
        for index in range(0, last + 1):
            name = _slot_value(raw, "CUSTOM_DATA_TABLE_NAME", index)
            if not name:
                continue
            alias = _slot_value(raw, "CUSTOM_DATA_TABLE_ALIAS", index)
            tables.append(CatalogDataTable(name=name, alias=alias))
    return tables
