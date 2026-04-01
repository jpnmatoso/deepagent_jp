from fastapi import APIRouter, HTTPException, Query
from typing import Any
from models import Thread, ThreadCreate, ThreadUpdate
from storage import storage

router = APIRouter(prefix="/threads", tags=["threads"])


def _consolidate_messages(messages: list) -> list[dict[str, Any]]:
    result = []
    for msg in messages:
        if not isinstance(msg, dict):
            result.append(msg)
            continue
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
                    "id": msg.get("id"),
                    "tool_calls": msg.get("tool_calls", []),
                    "invalid_tool_calls": msg.get("invalid_tool_calls", []),
                    "usage_metadata": msg.get("usage_metadata"),
                }
                result.append(consolidated)
        else:
            result.append(msg)
    return result


@router.post("")
async def create_thread(data: ThreadCreate | None = None) -> dict[str, Any]:
    thread = storage.create_thread(data)
    return {
        "thread_id": thread.thread_id,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
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
    metadata_filter = None
    threads = storage.list_threads(
        limit=limit,
        offset=offset,
        status=status,
        metadata_filter=metadata_filter,
    )
    return [
        {
            "thread_id": t.thread_id,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
            "metadata": t.metadata,
            "status": t.status,
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
    status: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    threads = storage.list_threads(
        limit=limit,
        offset=offset,
        status=status,
        metadata_filter=metadata,
    )
    return [
        {
            "thread_id": t.thread_id,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
            "metadata": t.metadata,
            "status": t.status,
            "values": t.values.model_dump()
            if hasattr(t.values, "model_dump")
            else t.values,
        }
        for t in threads
    ]


@router.get("/{thread_id}")
async def get_thread(thread_id: str) -> dict[str, Any]:
    thread = storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    return {
        "thread_id": thread.thread_id,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
        "metadata": thread.metadata,
        "status": thread.status,
        "config": thread.config,
        "values": thread.values.model_dump()
        if hasattr(thread.values, "model_dump")
        else thread.values,
    }


@router.patch("/{thread_id}")
async def update_thread(thread_id: str, data: ThreadUpdate) -> dict[str, Any]:
    thread = storage.update_thread(thread_id, data.metadata)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    return {
        "thread_id": thread.thread_id,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
        "metadata": thread.metadata,
        "status": thread.status,
    }


@router.get("/{thread_id}/state")
async def get_thread_state(thread_id: str) -> dict[str, Any]:
    thread = storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    from datetime import datetime
    from uuid import uuid4

    checkpoint_id = str(uuid4())

    thread_id_clean = thread_id.replace("-", "")[:8]

    messages_list = []
    if hasattr(thread.values, "messages"):
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

    return {
        "values": {
            "messages": messages_list,
            "todos": thread.values.todos if hasattr(thread.values, "todos") else [],
            "files": thread.values.files if hasattr(thread.values, "files") else {},
        },
        "next": [],
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
    thread = storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    history = storage.get_history(thread_id, limit=limit, offset=offset)
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
    limit: int = Query(10),
    offset: int = Query(0),
) -> list[dict[str, Any]]:
    thread = storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    history = storage.get_history(thread_id, limit=limit, offset=offset)
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
    thread = storage.update_state(thread_id, values)
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
