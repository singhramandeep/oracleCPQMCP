"""Authentication stub for stdio transport; OAuth-ready for future HTTP deployment."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AuthProvider(Protocol):
    """Future OAuth/MCP token validation interface."""

    def authenticate(self) -> bool:
        """Return True when the MCP client is authenticated."""
        ...


class StdioTrustedHostAuth:
    """Stdio mode: the host process (Cursor) is the trust boundary."""

    def authenticate(self) -> bool:
        return True
