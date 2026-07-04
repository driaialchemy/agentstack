"""Checkpoint manager for governed workflow recovery."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHECKPOINT_DIR = REPO_ROOT / "storage" / "checkpoints"

CHECKPOINT_STATUSES = ["created", "updated", "failed", "resumed", "rolled_back"]


class CheckpointManager:
    """Create, list, resume, and roll back workflow checkpoints."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or DEFAULT_CHECKPOINT_DIR

    def create(
        self,
        *,
        run_id: str,
        workflow_type: str,
        data_source: str,
        accountability_owner: str,
        current_step: str,
        completed_steps: list[str],
        failed_steps: list[str],
        agent_context: dict[str, Any],
        output_refs: dict[str, Any],
        status: str = "created",
    ) -> dict[str, Any]:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_id = str(uuid4())
        record = {
            "checkpoint_id": checkpoint_id,
            "run_id": run_id,
            "workflow_type": workflow_type,
            "data_source": data_source,
            "accountability_owner": accountability_owner,
            "current_step": current_step,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "agent_context": agent_context,
            "output_refs": output_refs,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
        }
        path = self.base_dir / f"{checkpoint_id}.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record

    def load(self, checkpoint_id: str) -> dict[str, Any] | None:
        path = self.base_dir / f"{checkpoint_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def update_status(self, checkpoint_id: str, status: str) -> dict[str, Any] | None:
        record = self.load(checkpoint_id)
        if record is None:
            return None
        record["status"] = status
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        path = self.base_dir / f"{checkpoint_id}.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record

    def list_for_run(self, run_id: str) -> list[dict[str, Any]]:
        if not self.base_dir.exists():
            return []
        records: list[dict[str, Any]] = []
        for path in self.base_dir.glob("*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if record.get("run_id") == run_id:
                records.append(record)
        records.sort(key=lambda item: item.get("created_at", ""))
        return records

    def list_all(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.base_dir.exists():
            return []
        records: list[dict[str, Any]] = []
        for path in sorted(self.base_dir.glob("*.json")):
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        if limit is not None:
            return records[-limit:]
        return records

    def latest_for_run(self, run_id: str) -> dict[str, Any] | None:
        checkpoints = self.list_for_run(run_id)
        return checkpoints[-1] if checkpoints else None
