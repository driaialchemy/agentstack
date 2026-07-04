"""Session memory — current app session/run state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SESSION_DIR = REPO_ROOT / "storage" / "memory" / "session"


class SessionStore:
    """File-backed session memory keyed by run_id."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or DEFAULT_SESSION_DIR

    def write(self, run_id: str, state: dict[str, Any]) -> dict[str, Any]:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "run_id": run_id,
            "state": state,
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
