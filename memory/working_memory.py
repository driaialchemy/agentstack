"""Working memory — current workflow/task context only."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKING_DIR = REPO_ROOT / "storage" / "memory" / "working"


class WorkingMemory:
    """File-backed working memory keyed by run_id."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or DEFAULT_WORKING_DIR

    def write(self, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "run_id": run_id,
            "payload": payload,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        path = self.base_dir / f"{run_id}.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record

    def read(self, run_id: str) -> dict[str, Any] | None:
        path = self.base_dir / f"{run_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_all(self) -> list[dict[str, Any]]:
        if not self.base_dir.exists():
            return []
        records: list[dict[str, Any]] = []
        for path in sorted(self.base_dir.glob("*.json")):
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        return records
