import sys
from pathlib import Path

AGENT_DIR = Path(__file__).parent.parent
SRC_DIR = AGENT_DIR.parent

if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend
from dotenv import load_dotenv

load_dotenv(AGENT_DIR / ".env")

from planning_agent.prompts import PLANNING_WORKFLOW_INSTRUCTIONS
from planning_agent.tools import (
    tavily_search,
    think_tool,
    projects_manager,
    tasks_manager,
    documents_manager,
)

INSTRUCTIONS = PLANNING_WORKFLOW_INSTRUCTIONS + "\n\n" + "=" * 80 + "\n\n"

model = init_chat_model(
    "stepfun/step-3.5-flash", model_provider="openai", temperature=0.0
)

backend = lambda rt: CompositeBackend(
    default=FilesystemBackend(root_dir=str(AGENT_DIR), virtual_mode=True),
    routes={
        "/skills/": FilesystemBackend(
            root_dir=str(AGENT_DIR / "skills"), virtual_mode=True
        ),
    },
)

graph = create_deep_agent(
    model=model,
    tools=[
        tavily_search,
        think_tool,
        projects_manager,
        tasks_manager,
        documents_manager,
    ],
    backend=backend,
    skills=["/skills/"],
    system_prompt=INSTRUCTIONS,
)
