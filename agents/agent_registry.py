"""Load and validate the Phase 3 agent registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent / "registry.yaml"

REQUIRED_AGENT_FIELDS = [
    "agent_id",
    "agent_name",
    "description",
    "allowed_skills",
    "enabled",
]


class AgentRegistryError(Exception):
    """Raised when the agent registry cannot be loaded or validated."""


def _validate_agent(agent: Any, index: int) -> dict[str, Any]:
    if not isinstance(agent, dict):
        raise AgentRegistryError(f"Agent entry at index {index} must be a mapping.")

    missing = [field for field in REQUIRED_AGENT_FIELDS if field not in agent]
    if missing:
        raise AgentRegistryError(
            f"Agent entry at index {index} is missing required fields: {', '.join(missing)}"
        )

    agent_id = agent["agent_id"]
    if not isinstance(agent_id, str) or not agent_id.strip():
        raise AgentRegistryError(f"Agent entry at index {index} has an invalid agent_id.")

    allowed_skills = agent["allowed_skills"]
    if not isinstance(allowed_skills, list) or not allowed_skills:
        raise AgentRegistryError(
            f"Agent '{agent_id}' must define a non-empty allowed_skills list."
        )

    return agent


def load_agent_registry(registry_path: Path | None = None) -> list[dict[str, Any]]:
    """Load and validate all agents from registry.yaml."""
    target_path = registry_path or DEFAULT_REGISTRY_PATH

    if not target_path.exists():
        raise AgentRegistryError(f"Agent registry not found: {target_path}")

    try:
        raw_text = target_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentRegistryError(f"Unable to read agent registry: {exc}") from exc

    try:
        parsed = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise AgentRegistryError(f"Agent registry YAML is malformed: {exc}") from exc

    if not isinstance(parsed, dict) or "agents" not in parsed:
        raise AgentRegistryError("Agent registry must contain a top-level 'agents' list.")

    agents = parsed["agents"]
    if not isinstance(agents, list) or not agents:
        raise AgentRegistryError("Agent registry 'agents' list must not be empty.")

    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, agent in enumerate(agents):
        validated_agent = _validate_agent(agent, index)
        agent_id = validated_agent["agent_id"]
        if agent_id in seen_ids:
            raise AgentRegistryError(f"Duplicate agent_id found in registry: {agent_id}")
        seen_ids.add(agent_id)
        validated.append(validated_agent)

    return validated


def get_all_agents(registry_path: Path | None = None) -> list[dict[str, Any]]:
    """Return all registered agents."""
    return load_agent_registry(registry_path)


def get_enabled_agents(registry_path: Path | None = None) -> list[dict[str, Any]]:
    """Return only agents where enabled is true."""
    return [agent for agent in get_all_agents(registry_path) if agent.get("enabled") is True]


def get_agent_by_id(
    agent_id: str,
    registry_path: Path | None = None,
) -> dict[str, Any] | None:
    """Return one agent by agent_id, or None if not registered."""
    for agent in get_all_agents(registry_path):
        if agent["agent_id"] == agent_id:
            return agent
    return None
