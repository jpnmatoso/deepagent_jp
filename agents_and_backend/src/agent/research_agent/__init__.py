"""Research Agent Module."""

from .prompts import (
    RESEARCHER_INSTRUCTIONS,
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from .tools import tavily_search, think_tool, save_markdown_report

__all__ = [
    "tavily_search",
    "think_tool",
    "save_markdown_report",
    "RESEARCHER_INSTRUCTIONS",
    "RESEARCH_WORKFLOW_INSTRUCTIONS",
    "SUBAGENT_DELEGATION_INSTRUCTIONS",
]
