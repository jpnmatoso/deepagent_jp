import sys
from datetime import datetime
from pathlib import Path

AGENT_DIR = Path(__file__).parent.parent
SRC_DIR = AGENT_DIR.parent

if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from dotenv import load_dotenv

load_dotenv(AGENT_DIR / ".env")

from research_agent.prompts import (
    RESEARCHER_INSTRUCTIONS,
    RESEARCH_WORKFLOW_INSTRUCTIONS,
    SUBAGENT_DELEGATION_INSTRUCTIONS,
)
from research_agent.tools import save_markdown_report
from tools import tavily_search, think_tool

max_concurrent_research_units = 3
max_researcher_iterations = 3

current_date = datetime.now().strftime("%Y-%m-%d")

INSTRUCTIONS = (
    RESEARCH_WORKFLOW_INSTRUCTIONS
    + "\n\n"
    + "=" * 80
    + "\n\n"
    + SUBAGENT_DELEGATION_INSTRUCTIONS.format(
        max_concurrent_research_units=max_concurrent_research_units,
        max_researcher_iterations=max_researcher_iterations,
    )
)

research_sub_agent = {
    "name": "research-agent",
    "description": "Delegate research to the sub-agent researcher. Only give this researcher one topic at a time.",
    "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
    "tools": [tavily_search, think_tool, save_markdown_report],
}

model = init_chat_model(
    "stepfun/step-3.5-flash:free", model_provider="openai", temperature=0.0
)

graph = create_deep_agent(
    model=model,
    tools=[tavily_search, think_tool, save_markdown_report],
    system_prompt=INSTRUCTIONS,
    subagents=[research_sub_agent],
)
