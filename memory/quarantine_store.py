"""Quarantine memory — failed, suspect, or unverified outputs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUARANTINE_PATH = REPO_ROOT / "storage" / "quarantine" / "quarantine.jsonl"


class QuarantineStore:
    """Append-only quarantine store."""

    def __init__(self, store_path: Path | None = None):
        self.store_path = store_path or DEFAULT_QUARANTINE_PATH

    def add(
        self,
        *,
        run_id: str,
        payload: dict[str, Any],
        reason: str,
        failure_class: str | None = None,
        accountability_owner: str = "",
    ) -> dict[str, Any]:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "quarantine_id": str(uuid4()),
            "run_id": run_id,
            "reason": reason,
            "failure_class": failure_class,
            "payload": payload,
            "accountability_owner": accountability_owner,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self.store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
        return entry

    def list_entries(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.store_path.exists():
            return []
        entries: list[dict[str, Any]] = []
        with self.store_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        if limit is not None:
            return entries[-limit:]
        return entries
