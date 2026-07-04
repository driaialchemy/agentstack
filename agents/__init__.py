"""Phase 3 governed agents for agentstack."""

from agents.agent_registry import (
    AgentRegistryError,
    get_agent_by_id,
    get_all_agents,
    get_enabled_agents,
    load_agent_registry,
)
from agents.analysis_agent import AnalysisAgent
from agents.intake_agent import IntakeAgent
from agents.report_agent import ReportAgent
from agents.verification_agent import VerificationAgent

AGENT_CLASSES = {
    "intake_agent": IntakeAgent,
    "analysis_agent": AnalysisAgent,
    "verification_agent": VerificationAgent,
    "report_agent": ReportAgent,
}

__all__ = [
    "AGENT_CLASSES",
    "AgentRegistryError",
    "AnalysisAgent",
    "IntakeAgent",
    "ReportAgent",
    "VerificationAgent",
    "get_agent_by_id",
    "get_all_agents",
    "get_enabled_agents",
    "load_agent_registry",
]
