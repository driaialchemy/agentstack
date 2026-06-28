"""Synthetic data sources for agentstack Phase 1."""

from data_sources.synthetic_data import get_structured_records, summarize_structured_data
from data_sources.synthetic_documents import get_documents, summarize_documents

__all__ = [
    "get_structured_records",
    "summarize_structured_data",
    "get_documents",
    "summarize_documents",
]
