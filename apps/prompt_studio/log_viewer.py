"""Parse and summarize DEBUG_MODE API logs under ``logs/`` for Prompt Studio."""

from __future__ import annotations

import re
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.core.debug_api_log import debug_log_dir

MAX_READ_BYTES = 8 * 1024 * 1024  # 8 MiB

_BLOCK_SPLIT = re.compile(
    r"^==========\s*(.+?)\s*==========\s*$",
    re.MULTILINE,
)
_METHOD_PATH = re.compile(r"^([A-Z]+)\s+(\S+)\s*$")
_STATUS_LINE = re.compile(
    r"^Status:\s*(\S+)(?:\s+\((\d+(?:\.\d+)?)\s*ms\))?\s*$",
    re.IGNORECASE,
)


@dataclass
class LogEntry:
    """One parsed HTTP request block from a debug log."""

    index: int
    timestamp: str | None
    method: str
    path: str
    url: str
    status: int | str | None
    duration_ms: float | None
    curl: str
    parameters: list[str] = field(default_factory=list)
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def logs_dir() -> Path:
    """Directory containing ``{profile}-{env}.log`` files."""
    return debug_log_dir()


def split_profile_env(stem: str) -> tuple[str, str]:
    """Split ``test-dev`` / ``my-company-prod`` into (profile, environment)."""
    if "-" not in stem:
        return stem, ""
    profile, env = stem.rsplit("-", 1)
    return profile, env


def list_log_files(directory: Path | None = None) -> list[dict[str, Any]]:
    """List ``*.log`` files in the logs directory (newest mtime first)."""
    root = directory or logs_dir()
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        try:
            st = path.stat()
        except OSError:
            continue
        profile, environment = split_profile_env(path.stem)
        rows.append(
            {
                "name": path.name,
                "profile": profile,
                "environment": environment,
                "size_bytes": st.st_size,
                "mtime_iso": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z"),
            }
        )
    return rows


def resolve_log_path(name: str, directory: Path | None = None) -> Path:
    """Resolve a log filename under *directory*; reject path escapes."""
    root = (directory or logs_dir()).resolve()
    if not name or name != Path(name).name:
        raise ValueError("Invalid log file name")
    if not name.endswith(".log"):
        raise ValueError("Only .log files are allowed")
    if ".." in name or "/" in name or "\\" in name:
        raise ValueError("Invalid log file name")
    target = (root / name).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Log path escapes logs directory") from exc
    if not target.is_file():
        raise FileNotFoundError(f"Log file not found: {name}")
    return target


def _parse_status(raw: str) -> int | str:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return raw


def parse_log_text(text: str) -> list[LogEntry]:
    """Parse debug-log text into structured entries."""
    matches = list(_BLOCK_SPLIT.finditer(text))
    if not matches:
        return []

    entries: list[LogEntry] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        raw = text[start:end].rstrip() + "\n"
        timestamp = match.group(1).strip() or None
        body = text[match.end() : end]

        method = ""
        path = ""
        url = ""
        status: int | str | None = None
        duration_ms: float | None = None
        curl_lines: list[str] = []
        param_lines: list[str] = []
        section: str | None = None

        for line in body.splitlines():
            if section == "curl":
                if line.strip() == "" or line.startswith("Parameters:"):
                    section = "params" if line.startswith("Parameters:") else None
                    continue
                curl_lines.append(line)
                continue
            if section == "params":
                if line.startswith("=========="):
                    break
                if line.strip():
                    param_lines.append(line.rstrip())
                continue

            mp = _METHOD_PATH.match(line.strip())
            if mp and not method:
                method = mp.group(1)
                path = mp.group(2)
                continue
            if line.startswith("URL:"):
                url = line[4:].strip()
                continue
            sm = _STATUS_LINE.match(line.strip())
            if sm:
                status = _parse_status(sm.group(1))
                if sm.group(2) is not None:
                    duration_ms = float(sm.group(2))
                continue
            if line.startswith("CURL:"):
                section = "curl"
                continue
            if line.startswith("Parameters:"):
                section = "params"
                continue

        entries.append(
            LogEntry(
                index=i,
                timestamp=timestamp,
                method=method,
                path=path,
                url=url,
                status=status,
                duration_ms=duration_ms,
                curl="\n".join(curl_lines).strip(),
                parameters=param_lines,
                raw=raw,
            )
        )
    return entries


def parse_log_file(path: Path, *, max_bytes: int = MAX_READ_BYTES) -> tuple[list[LogEntry], bool]:
    """Read and parse a log file. Returns (entries, truncated)."""
    size = path.stat().st_size
    truncated = size > max_bytes
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        if truncated:
            handle.seek(max(0, size - max_bytes))
            # Drop partial first line after seek into the middle of a file.
            handle.readline()
            text = handle.read()
        else:
            text = handle.read()
    return parse_log_text(text), truncated


def status_class(status: int | str | None) -> str:
    """Bucket label: 2xx / 3xx / 4xx / 5xx / error / other."""
    if status is None:
        return "other"
    if isinstance(status, str):
        lower = status.lower()
        if lower in ("error", "timeout", "exception"):
            return "error"
        try:
            status = int(status)
        except ValueError:
            return "other"
    if 200 <= status < 300:
        return "2xx"
    if 300 <= status < 400:
        return "3xx"
    if 400 <= status < 500:
        return "4xx"
    if 500 <= status < 600:
        return "5xx"
    return "other"


def _status_matches(entry: LogEntry, status_filter: str) -> bool:
    key = status_filter.strip().lower()
    if not key:
        return True
    if key == "error":
        sc = status_class(entry.status)
        return sc in ("4xx", "5xx", "error")
    if key.endswith("xx") and len(key) == 3:
        return status_class(entry.status) == key
    if isinstance(entry.status, int):
        try:
            return entry.status == int(key)
        except ValueError:
            return False
    return str(entry.status).lower() == key


def filter_entries(
    entries: list[LogEntry],
    *,
    q: str | None = None,
    method: str | None = None,
    status: str | None = None,
    path_contains: str | None = None,
    min_ms: float | None = None,
    max_ms: float | None = None,
) -> list[LogEntry]:
    """Apply query filters to parsed entries."""
    out: list[LogEntry] = []
    q_norm = (q or "").strip().lower()
    method_norm = (method or "").strip().upper()
    path_norm = (path_contains or "").strip().lower()

    for entry in entries:
        if method_norm and entry.method.upper() != method_norm:
            continue
        if status and not _status_matches(entry, status):
            continue
        if path_norm and path_norm not in (entry.path or "").lower():
            continue
        if min_ms is not None:
            if entry.duration_ms is None or entry.duration_ms < min_ms:
                continue
        if max_ms is not None:
            if entry.duration_ms is None or entry.duration_ms > max_ms:
                continue
        if q_norm:
            hay = " ".join(
                [
                    entry.method,
                    entry.path,
                    entry.url,
                    str(entry.status or ""),
                    entry.curl,
                    " ".join(entry.parameters),
                    entry.raw,
                ]
            ).lower()
            if q_norm not in hay:
                continue
        out.append(entry)
    return out


def latency_histogram(entries: list[LogEntry]) -> list[dict[str, Any]]:
    """Fixed latency buckets for charts."""
    buckets = [
        ("lt_200", "<200ms", 0, 200),
        ("200_500", "200–500ms", 200, 500),
        ("500_1000", "500ms–1s", 500, 1000),
        ("1000_3000", "1–3s", 1000, 3000),
        ("gte_3000", ">3s", 3000, None),
    ]
    counts = {key: 0 for key, _, _, _ in buckets}
    for entry in entries:
        ms = entry.duration_ms
        if ms is None:
            continue
        for key, _, lo, hi in buckets:
            if hi is None:
                if ms >= lo:
                    counts[key] += 1
                    break
            elif lo <= ms < hi:
                counts[key] += 1
                break
    return [
        {"key": key, "label": label, "count": counts[key]}
        for key, label, _, _ in buckets
    ]


def summarize_entries(entries: list[LogEntry]) -> dict[str, Any]:
    """Aggregate counts and latency percentiles for the filtered set."""
    status_buckets = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "error": 0, "other": 0}
    method_counts: dict[str, int] = {}
    durations: list[float] = []
    error_count = 0

    for entry in entries:
        sc = status_class(entry.status)
        status_buckets[sc] = status_buckets.get(sc, 0) + 1
        if sc in ("4xx", "5xx", "error"):
            error_count += 1
        m = entry.method or "?"
        method_counts[m] = method_counts.get(m, 0) + 1
        if entry.duration_ms is not None:
            durations.append(entry.duration_ms)

    p50: float | None = None
    p95: float | None = None
    if durations:
        sorted_d = sorted(durations)
        p50 = float(statistics.median(sorted_d))
        # Nearest-rank style p95
        idx = min(len(sorted_d) - 1, max(0, int(round(0.95 * (len(sorted_d) - 1)))))
        p95 = float(sorted_d[idx])

    return {
        "count": len(entries),
        "error_count": error_count,
        "p50_ms": p50,
        "p95_ms": p95,
        "status_buckets": status_buckets,
        "method_counts": method_counts,
        "latency_histogram": latency_histogram(entries),
    }


def load_log_payload(
    name: str,
    *,
    directory: Path | None = None,
    q: str | None = None,
    method: str | None = None,
    status: str | None = None,
    path_contains: str | None = None,
    min_ms: float | None = None,
    max_ms: float | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    """Resolve, parse, filter, and paginate a log file for the API."""
    path = resolve_log_path(name, directory)
    entries, truncated = parse_log_file(path)
    filtered = filter_entries(
        entries,
        q=q,
        method=method,
        status=status,
        path_contains=path_contains,
        min_ms=min_ms,
        max_ms=max_ms,
    )
    # Newest first for the timeline
    filtered_rev = list(reversed(filtered))
    summary = summarize_entries(filtered_rev)
    limit = max(1, min(limit, 1000))
    offset = max(0, offset)
    page = filtered_rev[offset : offset + limit]
    profile, environment = split_profile_env(path.stem)
    return {
        "name": path.name,
        "profile": profile,
        "environment": environment,
        "truncated": truncated,
        "total_parsed": len(entries),
        "total_matched": len(filtered_rev),
        "offset": offset,
        "limit": limit,
        "summary": summary,
        "entries": [e.to_dict() for e in page],
    }
