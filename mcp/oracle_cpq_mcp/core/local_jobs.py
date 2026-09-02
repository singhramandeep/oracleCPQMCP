"""In-process background jobs for long CPQ fetches (BML site export, etc.)."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.local_data import profile_env_root, safe_segment

logger = logging.getLogger(__name__)

JobStatus = str  # queued | running | succeeded | failed

_LOCK = threading.Lock()
_THREADS: dict[str, threading.Thread] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def jobs_dir(profile: CPQProfile) -> Path:
    """``data/{profile}/{env}/jobs``."""
    path = profile_env_root(profile) / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _job_path(profile: CPQProfile, job_id: str) -> Path:
    safe_id = safe_segment(job_id, fallback="job")
    return jobs_dir(profile) / f"{safe_id}.json"


def write_job(profile: CPQProfile, record: dict[str, Any]) -> Path:
    job_id = str(record["job_id"])
    path = _job_path(profile, job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def read_job(profile: CPQProfile, job_id: str) -> dict[str, Any] | None:
    path = _job_path(profile, job_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def create_job(
    profile: CPQProfile,
    *,
    kind: str,
    message: str,
) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    record = {
        "job_id": job_id,
        "kind": kind,
        "status": "queued",
        "message": message,
        "profile": profile.customer_id,
        "environment": profile.environment,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "result": None,
        "error": None,
    }
    write_job(profile, record)
    return record


def update_job(profile: CPQProfile, job_id: str, **fields: Any) -> dict[str, Any] | None:
    record = read_job(profile, job_id)
    if record is None:
        return None
    record.update(fields)
    record["updated_at"] = _utc_now()
    write_job(profile, record)
    return record


def start_background_job(
    profile: CPQProfile,
    *,
    kind: str,
    message: str,
    worker: Callable[[str], None],
) -> dict[str, Any]:
    """Create a job record and run *worker(job_id)* on a daemon thread."""
    record = create_job(profile, kind=kind, message=message)
    job_id = record["job_id"]

    def _run() -> None:
        try:
            update_job(profile, job_id, status="running", message=f"{message} (running)")
            worker(job_id)
        except Exception as exc:  # noqa: BLE001 — surface to job record
            logger.exception("Local job %s failed", job_id)
            update_job(
                profile,
                job_id,
                status="failed",
                message="Job failed",
                error=str(exc),
            )
        finally:
            with _LOCK:
                _THREADS.pop(job_id, None)

    thread = threading.Thread(
        target=_run,
        name=f"cpq-job-{job_id[:8]}",
        daemon=True,
    )
    with _LOCK:
        _THREADS[job_id] = thread
    thread.start()
    return record
