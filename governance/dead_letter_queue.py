"""Dead-letter queue for unrecoverable governed failures."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from governance.failure_taxonomy import recommended_action

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEAD_LETTER_PATH = REPO_ROOT / "storage" / "dead_letter" / "dead_letter.jsonl"


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class DeadLetterQueue:
    """Append-only dead-letter queue."""

    def __init__(self, store_path: Path | None = None):
        self.store_path = store_path or DEFAULT_DEAD_LETTER_PATH

    def append(
        self,
        *,
        run_id: str,
        task_id: str,
        agent_id: str,
        skill_id: str,
        failure_class: str,
        reason: str,
        accountability_owner: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        body = payload or {}
        entry = {
            "dead_letter_id": str(uuid4()),
            "run_id": run_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "skill_id": skill_id,
            "failure_class": failure_class,
            "failed_payload_hash": _hash_payload(body),
            "reason": reason,
            "recommended_action": recommended_action(failure_class),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "accountability_owner": accountability_owner,
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
