"""Central tool risk classification and policy registry."""

from __future__ import annotations

from dataclasses import dataclass

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG, ToolSpec, RiskLevel


@dataclass(frozen=True)
class ToolPolicy:
    """Server-side policy for one MCP tool."""

    name: str
    risk: RiskLevel
    confirmation_required: bool
    max_calls_per_minute: int
    idempotent: bool = False


def _risk_for_spec(spec: ToolSpec) -> RiskLevel:
    return spec.risk


def _rate_limit_for_risk(risk: RiskLevel) -> int:
    return {
        "READ_ONLY": 120,
        "LOW_RISK_WRITE": 20,
        "HIGH_RISK_WRITE": 10,
        "DESTRUCTIVE": 5,
        "PRIVILEGED": 5,
    }[risk]


def build_tool_policies() -> dict[str, ToolPolicy]:
    """Build TOOL_POLICIES from TOOL_CATALOG (single source of truth)."""
    policies: dict[str, ToolPolicy] = {}
    for name, spec in TOOL_CATALOG.items():
        risk = _risk_for_spec(spec)
        policies[name] = ToolPolicy(
            name=name,
            risk=risk,
            confirmation_required=spec.operation == "write",
            max_calls_per_minute=_rate_limit_for_risk(risk),
            idempotent=spec.operation == "write",
        )
    return policies


TOOL_POLICIES: dict[str, ToolPolicy] = build_tool_policies()


def get_tool_policy(tool_name: str) -> ToolPolicy | None:
    return TOOL_POLICIES.get(tool_name)
