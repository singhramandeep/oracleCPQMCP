"""Default MCP icons per tool domain (data-URI SVGs)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from oracle_cpq_mcp.registry.tool_registry import DomainName


@dataclass(frozen=True)
class IconSpec:
    """Serializable icon metadata mapped to mcp.types.Icon at registration."""

    src: str
    mime_type: str | None = "image/svg+xml"
    sizes: tuple[str, ...] | None = ("48x48",)


def _svg_data_uri(body: str, *, fill: str) -> str:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" '
        'width="48" height="48">'
        f'<rect width="48" height="48" rx="8" fill="{fill}"/>'
        f"{body}"
        "</svg>"
    )
    return "data:image/svg+xml," + quote(svg, safe="")


def _icon(fill: str, path: str) -> IconSpec:
    return IconSpec(src=_svg_data_uri(path, fill=fill))


# Simple monochrome glyphs on colored tiles (domain differentiation).
_DOMAIN_ICON_SPECS: dict[str, IconSpec] = {
    "users": _icon(
        "#2563eb",
        '<circle cx="24" cy="18" r="8" fill="#fff"/>'
        '<path d="M8 40c0-8 7-12 16-12s16 4 16 12" fill="#fff"/>',
    ),
    "groups": _icon(
        "#7c3aed",
        '<circle cx="16" cy="18" r="6" fill="#fff"/>'
        '<circle cx="32" cy="18" r="6" fill="#fff"/>'
        '<path d="M4 40c0-6 5-10 12-10m16 0c7 0 12 4 12 10" '
        'stroke="#fff" stroke-width="3" fill="none"/>',
    ),
    "datatables": _icon(
        "#059669",
        '<rect x="10" y="12" width="28" height="24" rx="2" fill="none" '
        'stroke="#fff" stroke-width="3"/>'
        '<path d="M10 20h28M10 28h28M22 12v24" stroke="#fff" stroke-width="3"/>',
    ),
    "bml": _icon(
        "#db2777",
        '<path d="M14 34V14h6l4 12 4-12h6v20h-5V22l-4 12h-2l-4-12v12h-5z" fill="#fff"/>',
    ),
    "commerce": _icon(
        "#ea580c",
        '<path d="M12 14h28l-3 18H16L12 14zm6 26a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm16 0'
        'a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" fill="#fff"/>',
    ),
    "performance": _icon(
        "#0891b2",
        '<path d="M10 34V22h6v12H10zm11 0V14h6v20h-6zm11 0V26h6v8h-6z" fill="#fff"/>',
    ),
    "parts": _icon(
        "#4f46e5",
        '<path d="M24 10l12 7v14l-12 7-12-7V17l12-7z" fill="none" '
        'stroke="#fff" stroke-width="3"/>',
    ),
    "tasks": _icon(
        "#ca8a04",
        '<rect x="12" y="10" width="24" height="28" rx="2" fill="none" '
        'stroke="#fff" stroke-width="3"/>'
        '<path d="M18 22l4 4 8-8" stroke="#fff" stroke-width="3" fill="none"/>',
    ),
    "configuration": _icon(
        "#64748b",
        '<circle cx="24" cy="24" r="8" fill="none" stroke="#fff" stroke-width="3"/>'
        '<path d="M24 8v6M24 34v6M8 24h6M34 24h6M12 12l4 4M32 32l4 4M36 12l-4 4M16 32l-4 4" '
        'stroke="#fff" stroke-width="3"/>',
    ),
    "meta": _icon(
        "#0f766e",
        '<circle cx="24" cy="24" r="14" fill="none" stroke="#fff" stroke-width="3"/>'
        '<path d="M18 24h12M24 18v12" stroke="#fff" stroke-width="3"/>',
    ),
}


def domain_default_icons(domain: DomainName | str) -> tuple[IconSpec, ...]:
    """Return the default icon tuple for a catalog domain."""
    icon = _DOMAIN_ICON_SPECS.get(str(domain)) or _DOMAIN_ICON_SPECS["meta"]
    return (icon,)


def resolve_tool_icons(
    domain: DomainName | str,
    icons: tuple[IconSpec, ...] | None,
) -> tuple[IconSpec, ...]:
    """Use explicit icons when provided; otherwise domain defaults."""
    if icons:
        return icons
    return domain_default_icons(domain)
