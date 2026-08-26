"""Load shared and customer knowledge markdown for MCP instructions."""

from __future__ import annotations

import logging
from pathlib import Path

from oracle_cpq_mcp.core.config import find_project_root

logger = logging.getLogger(__name__)

BASE_KNOWLEDGE_FILENAME = "CPQBaseKnowledge.md"


def knowledge_dir(project_root: Path | None = None) -> Path:
    """Return the repo `knowledge/` directory."""
    root = project_root or find_project_root()
    return root / "knowledge"


def load_base_knowledge(project_root: Path | None = None) -> str:
    """Load shared CPQBaseKnowledge.md; return empty string if missing."""
    path = knowledge_dir(project_root) / BASE_KNOWLEDGE_FILENAME
    if not path.is_file():
        logger.warning("Shared knowledge file not found: %s", path)
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_customer_knowledge(
    customer_knowledge_file: str | None,
    *,
    project_root: Path | None = None,
) -> str:
    """Load knowledge/{CUSTOMER_KNOWLEDGE_FILE}; warn and return '' if missing."""
    if not customer_knowledge_file:
        return ""
    raw = customer_knowledge_file.strip()
    name = Path(raw).name
    if name != raw:
        logger.warning(
            "Ignoring unsafe CUSTOMER_KNOWLEDGE_FILE value (filename only): %s",
            customer_knowledge_file,
        )
        return ""

    path = knowledge_dir(project_root) / name
    if not path.is_file():
        logger.warning("Customer knowledge file not found (skipping): %s", path)
        return ""
    return path.read_text(encoding="utf-8").strip()
