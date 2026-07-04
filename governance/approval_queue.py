"""Local demo human approval queue for Phase 6."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_APPROVAL_PATH = REPO_ROOT / "storage" / "approvals" / "approval_queue.jsonl"

APPROVAL_STATUSES = ["pending", "approved", "rejected", "overridden"]


class ApprovalQueue:
    """Append-only approval queue with in-memory updates via rewrite."""

    def __init__(self, store_path: Path | None = None):
        self.store_path = store_path or DEFAULT_APPROVAL_PATH

    def _load_all(self) -> list[dict[str, Any]]:
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
        return entries

    def _rewrite(self, entries: list[dict[str, Any]]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, ensure_ascii=True) + "\n")

    def request(
        self,
        *,
        run_id: str,
        requested_by_agent: str,
        skill_id: str,
        risk_tier: str,
        reason: str,
        accountability_owner: str,
    ) -> dict[str, Any]:
        entry = {
            "approval_id": str(uuid4()),
            "run_id": run_id,
            "requested_by_agent": requested_by_agent,
            "skill_id": skill_id,
            "risk_tier": risk_tier,
            "reason": reason,
            "status": "pending",
            "justification": "",
            "accountability_owner": accountability_owner,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with self.store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
        return entry

    def resolve(
        self,
        *,
        approval_id: str,
        status: str,
        justification: str = "",
    ) -> dict[str, Any] | None:
        if status not in APPROVAL_STATUSES or status == "pending":
            raise ValueError(f"Invalid approval resolution status: {status}")
        entries = self._load_all()
        updated: dict[str, Any] | None = None
        for entry in entries:
            if entry.get("approval_id") == approval_id:
                entry["status"] = status
                entry["justification"] = justification
                entry["resolved_at"] = datetime.now(timezone.utc).isoformat()
                updated = entry
                break
        if updated is None:
            return None
        self._rewrite(entries)
        return updated

    def get(self, approval_id: str) -> dict[str, Any] | None:
        for entry in self._load_all():
            if entry.get("approval_id") == approval_id:
                return entry
        return None

    def list_entries(self, *, run_id: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        entries = self._load_all()
        if run_id:
            entries = [entry for entry in entries if entry.get("run_id") == run_id]
        if limit is not None:
            return entries[-limit:]
        return entries

    def is_approved(self, approval_id: str) -> bool:
        entry = self.get(approval_id)
        return bool(entry and entry.get("status") in {"approved", "overridden"})

    def pending_for_skill(self, run_id: str, skill_id: str) -> dict[str, Any] | None:
        for entry in reversed(self._load_all()):
            if (
                entry.get("run_id") == run_id
                and entry.get("skill_id") == skill_id
                and entry.get("status") == "pending"
            ):
                return entry
        return None
