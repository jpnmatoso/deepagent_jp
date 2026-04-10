from fastapi import APIRouter, HTTPException, Query, Body
from typing import Any
from uuid import uuid4
from models import Thread, ThreadCreate, ThreadUpdate
from storage import storage

router = APIRouter(prefix="/threads", tags=["threads"])


def _ensure_message_id(msg: dict) -> dict:
    if not msg.get("id"):
        msg["id"] = str(uuid4())
    return msg


def _normalize_message_type(msg_type: str) -> str:
    type_map = {
        "AIMessageChunk": "ai",
        "HumanMessage": "human",
        "SystemMessage": "system",
        "ToolMessage": "tool",
        "ai": "ai",
        "human": "human",
        "system": "system",
        "tool": "tool",
    }
    return type_map.get(msg_type, msg_type.lower() if msg_type else "ai")


def _consolidate_messages(messages: list) -> list[dict[str, Any]]:
    result = []
    for msg in messages:
        if not isinstance(msg, dict):
            result.append(msg)
            continue

        msg = _ensure_message_id(msg)
        msg_type = msg.get("type", "")

        if msg_type == "AIMessageChunk":
            if result and result[-1].get("id") == msg.get("id"):
                prev = result[-1]
                prev["content"] = (prev.get("content") or "") + (
                    msg.get("content") or ""
                )
                prev["type"] = "ai"
                if msg.get("response_metadata"):
                    prev["response_metadata"].update(msg["response_metadata"])
                if msg.get("tool_calls"):
                    prev["tool_calls"] = msg["tool_calls"]
                if msg.get("usage_metadata"):
                    prev["usage_metadata"] = msg["usage_metadata"]
            else:
                consolidated = {
                    "content": msg.get("content", ""),
                    "additional_kwargs": msg.get("additional_kwargs", {}),
                    "response_metadata": msg.get("response_metadata", {}),
                    "type": "ai",
                    "name": msg.get("name"),
                    "id": msg["id"],
                    "tool_calls": msg.get("tool_calls", []),
                    "invalid_tool_calls": msg.get("invalid_tool_calls", []),
                    "usage_metadata": msg.get("usage_metadata"),
                }
                result.append(consolidated)
        else:
            msg["type"] = _normalize_message_type(msg_type)
            result.append(msg)
    return result


@router.post("")
async def create_thread(data: ThreadCreate | None = None) -> dict[str, Any]:
    thread = await storage.create_thread(data)
    return {
        "thread_id": thread.thread_id,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
        "metadata": thread.metadata,
        "status": thread.status,
        "values": thread.values.model_dump(),
    }


@router.get("")
async def list_threads(
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    status: str | None = Query(None),
) -> list[dict[str, Any]]:
    threads = await storage.list_threads(
        limit=limit,
        offset=offset,
        status=status,
        metadata_filter=None,
    )
    return [
        {
            "thread_id": t.thread_id,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            "metadata": t.metadata,
            "status": t.status,
            "config": t.config,
            "values": t.values.model_dump()
            if hasattr(t.values, "model_dump")
            else t.values,
        }
        for t in threads
    ]


@router.post("/search")
async def search_threads(
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    status: str | None = Query(None),
) -> list[dict[str, Any]]:
    threads = await storage.list_threads(
        limit=limit,
        offset=offset,
        status=status,
        metadata_filter=None,
    )
    return [
        {
            "thread_id": t.thread_id,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            "metadata": t.metadata,
            "status": t.status,
            "config": t.config,
            "values": t.values.model_dump()
            if hasattr(t.values, "model_dump")
            else t.values,
        }
        for t in threads
    ]


@router.patch("/{thread_id}")
async def update_thread(thread_id: str, data: ThreadUpdate) -> dict[str, Any]:
    thread = await storage.update_thread(thread_id, data.metadata)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    return {
        "thread_id": thread.thread_id,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
        "metadata": thread.metadata,
        "status": thread.status,
    }


@router.get("/{thread_id}")
async def get_thread(thread_id: str) -> dict[str, Any]:
    thread = await storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    return {
        "thread_id": thread.thread_id,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
        "metadata": thread.metadata,
        "status": thread.status,
        "config": thread.config,
        "values": thread.values.model_dump()
        if hasattr(thread.values, "model_dump")
        else thread.values,
    }


@router.delete("/{thread_id}", status_code=204)
async def delete_thread(thread_id: str) -> None:
    deleted = await storage.delete_thread(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")


@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str) -> dict[str, Any]:
    thread = await storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    from datetime import datetime
    from uuid import uuid4

    checkpoint_id = str(uuid4())

    thread_id_clean = thread_id.replace("-", "")[:8]

    history = await storage.get_history(thread_id, limit=1, offset=0)

    messages_list = []
    if history and "values" in history[0] and "messages" in history[0]["values"]:
        messages_list = history[0]["values"]["messages"]
    elif hasattr(thread.values, "messages"):
        for msg in thread.values.messages:
            if isinstance(msg, dict):
                messages_list.append(
                    {
                        "content": msg.get("content", ""),
                        "additional_kwargs": msg.get("additional_kwargs", {}),
                        "response_metadata": msg.get("response_metadata", {}),
                        "type": msg.get("type", "human"),
                        "name": msg.get("name"),
                        "id": msg.get("id", str(uuid4())),
                        "tool_calls": msg.get("tool_calls", []),
                        "invalid_tool_calls": msg.get("invalid_tool_calls", []),
                        "usage_metadata": msg.get("usage_metadata", {}),
                    }
                )
            else:
                messages_list.append(msg)

    messages_list = _consolidate_messages(messages_list)

    next_nodes = []
    if history:
        next_nodes = history[0].get("next", [])

    todos = []
    files = {}
    if history and "values" in history[0]:
        todos = history[0]["values"].get("todos", [])
        files = history[0]["values"].get("files", {})
    elif hasattr(thread.values, "todos"):
        todos = thread.values.todos
        files = thread.values.files if hasattr(thread.values, "files") else {}

    return {
        "values": {
            "messages": messages_list,
            "todos": todos,
            "files": files,
        },
        "next": next_nodes,
        "tasks": [],
        "metadata": {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "graph_id": thread.metadata.get("graph_id", ""),
            "assistant_id": thread.metadata.get("assistant_id", ""),
            "source": "update",
            "step": 0,
            "writes": {},
            "parents": {},
        },
        "created_at": datetime.utcnow().isoformat() + "+00:00",
        "checkpoint": {
            "checkpoint_id": checkpoint_id,
            "thread_id": thread_id,
            "checkpoint_ns": "",
        },
        "parent_checkpoint": None,
        "checkpoint_id": checkpoint_id,
        "parent_checkpoint_id": None,
    }


@router.get("/{thread_id}/history")
async def get_thread_history_get(
    thread_id: str,
    limit: int = Query(10),
    offset: int = Query(0),
) -> list[dict[str, Any]]:
    thread = await storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    history = await storage.get_history(thread_id, limit=limit, offset=offset)
    if not history:
        thread_id_clean = thread_id.replace("-", "")[:8]
        return [
            {
                "values": thread.values.model_dump()
                if hasattr(thread.values, "model_dump")
                else thread.values,
                "next": [],
                "tasks": [],
                "metadata": {
                    "thread_id": thread_id,
                    "checkpoint_id": f"{thread_id_clean}-initial",
                    "graph_id": thread.metadata.get("graph_id", ""),
                    "source": "update",
                    "step": 0,
                    "writes": {},
                    "parents": {},
                },
                "created_at": thread.created_at.isoformat() + "+00:00",
                "checkpoint": {
                    "checkpoint_id": f"{thread_id_clean}-initial",
                    "thread_id": thread_id,
                    "checkpoint_ns": "",
                },
                "parent_checkpoint": None,
                "interrupts": [],
                "checkpoint_id": f"{thread_id_clean}-initial",
                "parent_checkpoint_id": None,
            }
        ]
    for entry in history:
        if "values" in entry and "messages" in entry["values"]:
            entry["values"]["messages"] = _consolidate_messages(
                entry["values"]["messages"]
            )
    return history


@router.post("/{thread_id}/history")
async def get_thread_history_post(
    thread_id: str,
    body: dict[str, Any] | None = Body(None),
) -> list[dict[str, Any]]:
    thread = await storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    limit = 10
    offset = 0
    if body:
        limit = int(body.get("limit", 10))
        offset = int(body.get("offset", 0))

    history = await storage.get_history(thread_id, limit=limit, offset=offset)
    if not history:
        thread_id_clean = thread_id.replace("-", "")[:8]
        return [
            {
                "values": thread.values.model_dump()
                if hasattr(thread.values, "model_dump")
                else thread.values,
                "next": [],
                "tasks": [],
                "metadata": {
                    "thread_id": thread_id,
                    "checkpoint_id": f"{thread_id_clean}-initial",
                    "graph_id": thread.metadata.get("graph_id", ""),
                    "source": "update",
                    "step": 0,
                    "writes": {},
                    "parents": {},
                },
                "created_at": thread.created_at.isoformat() + "+00:00",
                "checkpoint": {
                    "checkpoint_id": f"{thread_id_clean}-initial",
                    "thread_id": thread_id,
                    "checkpoint_ns": "",
                },
                "parent_checkpoint": None,
                "interrupts": [],
                "checkpoint_id": f"{thread_id_clean}-initial",
                "parent_checkpoint_id": None,
            }
        ]
    for entry in history:
        if "values" in entry and "messages" in entry["values"]:
            entry["values"]["messages"] = _consolidate_messages(
                entry["values"]["messages"]
            )
    return history


@router.post("/{thread_id}/state")
async def update_thread_state(
    thread_id: str,
    values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    thread = await storage.update_state(thread_id, values)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    from datetime import datetime
    from uuid import uuid4

    checkpoint_id = str(uuid4())

    return {
        "values": thread.values.model_dump()
        if hasattr(thread.values, "model_dump")
        else thread.values,
        "next": [],
        "tasks": [],
        "metadata": {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "graph_id": thread.metadata.get("graph_id", ""),
            "source": "update",
            "step": 0,
            "writes": {},
            "parents": {},
        },
        "created_at": datetime.utcnow().isoformat(),
        "checkpoint": {
            "checkpoint_id": checkpoint_id,
            "thread_id": thread_id,
            "checkpoint_ns": "",
        },
        "parent_checkpoint": None,
        "checkpoint_id": checkpoint_id,
        "parent_checkpoint_id": None,
    }
