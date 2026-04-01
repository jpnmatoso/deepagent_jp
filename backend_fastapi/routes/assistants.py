from fastapi import APIRouter, HTTPException, Query, Body
from typing import Any
from models import Assistant

router = APIRouter(prefix="", tags=["assistants"])

AVAILABLE_ASSISTANTS: dict[str, dict[str, Any]] = {
    "planning": {
        "assistant_id": "planning",
        "graph_id": "planning",
        "name": "Planning Agent",
        "description": "Strategic planning agent with project and task management",
        "config": {},
        "metadata": {"created_by": "system"},
    },
    "research": {
        "assistant_id": "research",
        "graph_id": "research",
        "name": "Research Agent",
        "description": "Deep research agent with sub-agent delegation",
        "config": {},
        "metadata": {"created_by": "system"},
    },
    "simple": {
        "assistant_id": "simple",
        "graph_id": "simple",
        "name": "Simple Agent",
        "description": "Simple agent with basic arithmetic tools",
        "config": {},
        "metadata": {"created_by": "system"},
    },
}


@router.get("/assistants")
async def list_assistants(
    limit: int = Query(100),
) -> list[dict[str, Any]]:
    return list(AVAILABLE_ASSISTANTS.values())[:limit]


@router.post("/assistants/search")
async def search_assistants(
    body: dict[str, Any] | None = Body(None),
    limit: int = Query(100),
    graph_id: str | None = Query(None),
    graphId: str | None = Query(None),
) -> list[dict[str, Any]]:
    assistants = list(AVAILABLE_ASSISTANTS.values())

    target_graph = graph_id or graphId
    if body:
        target_graph = body.get("graph_id") or body.get("graphId") or target_graph
        body_limit = body.get("limit")
        if body_limit:
            limit = int(body_limit)

    if target_graph:
        assistants = [a for a in assistants if a.get("graph_id") == target_graph]

    return assistants[:limit]


@router.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str) -> dict[str, Any]:
    assistant = AVAILABLE_ASSISTANTS.get(assistant_id)
    if not assistant:
        raise HTTPException(
            status_code=404, detail=f"Assistant {assistant_id} not found"
        )
    return assistant
