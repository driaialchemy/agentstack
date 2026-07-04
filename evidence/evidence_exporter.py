"""Export evidence reports as Markdown and JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_evidence_bundle(
    *,
    run_id: str,
    reports: dict[str, Any],
    output_dir: Path,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for name, payload in reports.items():
        json_path = output_dir / f"{run_id}_{name}.json"
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        paths[f"{name}_json"] = str(json_path)

        md_path = output_dir / f"{run_id}_{name}.md"
        md_path.write_text(_to_markdown(name, payload), encoding="utf-8")
        paths[f"{name}_markdown"] = str(md_path)
    return paths


def _to_markdown(name: str, payload: dict[str, Any]) -> str:
    lines = [f"# {name.replace('_', ' ').title()}", ""]
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            lines.append(f"## {key}")
            lines.append("```json")
            lines.append(json.dumps(value, indent=2))
            lines.append("```")
        else:
            lines.append(f"- **{key}**: {value}")
        lines.append("")
    return "\n".join(lines)
