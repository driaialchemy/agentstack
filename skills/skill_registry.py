"""Load and validate the Phase 2 skill registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent / "registry.yaml"

REQUIRED_SKILL_FIELDS = [
    "skill_id",
    "display_name",
    "description",
    "allowed_data_sources",
    "allowed_workflow_types",
    "risk_level",
    "requires_approval",
    "max_records_or_documents",
    "enabled",
]


class SkillRegistryError(Exception):
    """Raised when the skill registry cannot be loaded or validated."""


def _validate_skill(skill: Any, index: int) -> dict[str, Any]:
    if not isinstance(skill, dict):
        raise SkillRegistryError(f"Skill entry at index {index} must be a mapping.")

    missing = [field for field in REQUIRED_SKILL_FIELDS if field not in skill]
    if missing:
        raise SkillRegistryError(
            f"Skill entry at index {index} is missing required fields: {', '.join(missing)}"
        )

    skill_id = skill["skill_id"]
    if not isinstance(skill_id, str) or not skill_id.strip():
        raise SkillRegistryError(f"Skill entry at index {index} has an invalid skill_id.")

    for list_field in ("allowed_data_sources", "allowed_workflow_types"):
        value = skill[list_field]
        if not isinstance(value, list) or not value:
            raise SkillRegistryError(
                f"Skill '{skill_id}' must define a non-empty {list_field} list."
            )

    if not isinstance(skill["max_records_or_documents"], int) or skill["max_records_or_documents"] < 1:
        raise SkillRegistryError(
            f"Skill '{skill_id}' must define max_records_or_documents as a positive integer."
        )

    risk = str(skill.get("risk_level", "low")).lower()
    cost_defaults = {
        "low": {"estimated_cost": 0.5, "cost_category": "compute", "cost_budget_impact": "low"},
        "medium": {"estimated_cost": 2.0, "cost_category": "compute", "cost_budget_impact": "medium"},
        "high": {"estimated_cost": 5.0, "cost_category": "governance", "cost_budget_impact": "high"},
    }
    defaults = cost_defaults.get(risk, cost_defaults["low"])
    for field, default_value in defaults.items():
        skill.setdefault(field, default_value)

    return skill


def load_skill_registry(registry_path: Path | None = None) -> list[dict[str, Any]]:
    """Load and validate all skills from registry.yaml."""
    target_path = registry_path or DEFAULT_REGISTRY_PATH

    if not target_path.exists():
        raise SkillRegistryError(f"Skill registry not found: {target_path}")

    try:
        raw_text = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SkillRegistryError(f"Unable to read skill registry: {exc}") from exc

    try:
        parsed = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise SkillRegistryError(f"Skill registry YAML is malformed: {exc}") from exc

    if not isinstance(parsed, dict) or "skills" not in parsed:
        raise SkillRegistryError("Skill registry must contain a top-level 'skills' list.")

    skills = parsed["skills"]
    if not isinstance(skills, list) or not skills:
        raise SkillRegistryError("Skill registry 'skills' list must not be empty.")

    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, skill in enumerate(skills):
        validated_skill = _validate_skill(skill, index)
        skill_id = validated_skill["skill_id"]
        if skill_id in seen_ids:
            raise SkillRegistryError(f"Duplicate skill_id found in registry: {skill_id}")
        seen_ids.add(skill_id)
        validated.append(validated_skill)

    return validated


def get_all_skills(registry_path: Path | None = None) -> list[dict[str, Any]]:
    """Return all registered skills."""
    return load_skill_registry(registry_path)


def get_enabled_skills(registry_path: Path | None = None) -> list[dict[str, Any]]:
    """Return only skills where enabled is true."""
    return [skill for skill in get_all_skills(registry_path) if skill.get("enabled") is True]


def get_skill_by_id(
    skill_id: str,
    registry_path: Path | None = None,
) -> dict[str, Any] | None:
    """Return one skill by skill_id, or None if not registered."""
    for skill in get_all_skills(registry_path):
        if skill["skill_id"] == skill_id:
            return skill
    return None
