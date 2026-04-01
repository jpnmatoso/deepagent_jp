import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from fastapi.responses import StreamingResponse
import json

AGENTS_DIR = (
    Path(__file__).parent.parent.parent / "agents_and_backend" / "src" / "agent"
)
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from storage import storage

router = APIRouter(prefix="/threads/{thread_id}/runs", tags=["runs"])

GRAPHS: dict[str, Any] = {}


def _load_graphs():
    global GRAPHS
    if GRAPHS:
        return

    try:
        from research_graph import graph as research_graph

        GRAPHS["research"] = research_graph
    except Exception as e:
        print(f"Failed to load research graph: {e}")

    try:
        from planning_graph import graph as planning_graph

        GRAPHS["planning"] = planning_graph
    except Exception as e:
        print(f"Failed to load planning graph: {e}")

    try:
        from simpleagent_graph import graph as simple_graph

        GRAPHS["simple"] = simple_graph
    except Exception as e:
        print(f"Failed to load simple graph: {e}")


_load_graphs()


def _serialize_messages(messages: list) -> list[dict[str, Any]]:
    result = []
    for msg in messages:
        if hasattr(msg, "model_dump"):
            result.append(msg.model_dump())
        elif hasattr(msg, "dict"):
            result.append(msg.dict())
        else:
            result.append({"content": str(msg)})
    return result


@router.post("")
async def create_run(
    thread_id: str,
    assistant_id: str | None = Body(None),
    input: dict[str, Any] | None = Body(None),
    config: dict[str, Any] | None = Body(None),
    command: dict[str, Any] | None = Body(None),
    interrupt_before: list[str] | None = Body(None),
    interrupt_after: list[str] | None = Body(None),
    checkpoint: str | dict[str, Any] | None = Body(None),
) -> dict[str, Any]:
    thread = storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    if not assistant_id:
        raise HTTPException(status_code=422, detail="assistant_id is required")

    if assistant_id not in GRAPHS:
        raise HTTPException(
            status_code=404, detail=f"Assistant {assistant_id} not found"
        )

    graph = GRAPHS[assistant_id]
    run_id = str(uuid4())

    thread.status = "running"

    messages = []
    if input and "messages" in input:
        for msg in input["messages"]:
            if isinstance(msg, dict):
                messages.append(msg)
            elif hasattr(msg, "model_dump"):
                messages.append(msg.model_dump())
            else:
                messages.append({"content": str(msg), "type": "human"})

    for msg in messages:
        thread.values.messages.append(msg)

    try:
        state = (
            thread.values.model_dump()
            if hasattr(thread.values, "model_dump")
            else thread.values
        )

        result = graph.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}}
            if config is None
            else config,
        )

        if result and "messages" in result:
            thread.values.messages = result["messages"]

        thread.status = "idle"
        thread.updated_at = datetime.utcnow()

    except Exception as e:
        thread.status = "error"
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "assistant_id": assistant_id,
        "status": thread.status,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.post("/wait")
async def run_wait(
    thread_id: str,
    assistant_id: str | None = Body(None),
    input: dict[str, Any] | None = Body(None),
    config: dict[str, Any] | None = Body(None),
    command: dict[str, Any] | None = Body(None),
    interrupt_before: list[str] | None = Body(None),
    interrupt_after: list[str] | None = Body(None),
    checkpoint: str | dict[str, Any] | None = Body(None),
) -> dict[str, Any]:
    thread = storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    if not assistant_id:
        raise HTTPException(status_code=422, detail="assistant_id is required")

    if assistant_id not in GRAPHS:
        raise HTTPException(
            status_code=404, detail=f"Assistant {assistant_id} not found"
        )

    graph = GRAPHS[assistant_id]
    run_id = str(uuid4())

    thread.status = "running"

    messages = []
    if input and "messages" in input:
        for msg in input["messages"]:
            if isinstance(msg, dict):
                messages.append(msg)
            elif hasattr(msg, "model_dump"):
                messages.append(msg.model_dump())
            else:
                messages.append({"content": str(msg), "type": "human"})

    for msg in messages:
        thread.values.messages.append(msg)

    try:
        state = (
            thread.values.model_dump()
            if hasattr(thread.values, "model_dump")
            else thread.values
        )

        result = graph.invoke(
            {"messages": messages},
            config={"configurable": {"thread_id": thread_id}}
            if config is None
            else config,
        )

        if result and "messages" in result:
            thread.values.messages = result["messages"]

        thread.status = "idle"
        thread.updated_at = datetime.utcnow()

    except Exception as e:
        thread.status = "error"
        raise HTTPException(status_code=500, detail=str(e))

    messages_output = _serialize_messages(thread.values.messages)

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "assistant_id": assistant_id,
        "status": thread.status,
        "created_at": datetime.utcnow().isoformat(),
        "messages": messages_output,
    }


def _serialize_msg(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    elif isinstance(obj, (list, tuple)):
        return [_serialize_msg(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _serialize_msg(v) for k, v in obj.items()}
    return str(obj)


def _consolidate_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for msg in messages:
        msg_type = msg.get("type", "")
        if msg_type == "AIMessageChunk" or (
            msg_type == "ai"
            and msg.get("content")
            and isinstance(msg.get("content"), str)
            and result
            and result[-1].get("type") in ("ai", "AIMessageChunk")
            and result[-1].get("id") == msg.get("id")
        ):
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


async def _stream_graph(
    graph: Any,
    thread_id: str,
    input_messages: list[dict[str, Any]],
    config: dict[str, Any] | None,
) -> AsyncGenerator[str, None]:
    from storage import storage

    thread = storage.get_thread(thread_id)
    all_messages = []
    stream_config = (
        {"configurable": {"thread_id": thread_id}} if config is None else config
    )

    def _build_state():
        return {
            "messages": _consolidate_messages(all_messages),
            "todos": thread.values.todos if thread else [],
            "files": thread.values.files if thread else {},
            "email": thread.values.email if thread else None,
            "ui": thread.values.ui if thread else None,
        }

    try:
        async for event in graph.astream(
            {"messages": input_messages},
            config=stream_config,
            stream_mode="messages",
        ):
            if isinstance(event, tuple) and len(event) == 2:
                msg, meta = event
                msg_data = _serialize_msg(msg)
                if msg_data.get("content") or msg_data.get("tool_calls"):
                    all_messages.append(msg_data)
                    msg_tuple = [msg_data, _serialize_msg(meta)]
                    yield f"event: messages\ndata: {json.dumps(msg_tuple)}\n\n"
                    yield f"event: values\ndata: {json.dumps(_build_state())}\n\n"
    except Exception as e:
        print(f"[STREAM] Error: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    finally:
        if thread:
            thread.values.messages = _consolidate_messages(all_messages)
            thread.status = "idle"
            thread.updated_at = datetime.utcnow()
        yield f"event: values\ndata: {json.dumps(_build_state())}\n\n"


async def _stream_graph_with_checkpoints(
    graph: Any,
    thread_id: str,
    input_messages: list[dict[str, Any]],
    config: dict[str, Any] | None,
    assistant_id: str,
) -> AsyncGenerator[str, None]:
    from storage import storage

    thread = storage.get_thread(thread_id)
    all_messages = input_messages.copy()
    step = 0
    stream_config = (
        {"configurable": {"thread_id": thread_id}} if config is None else config
    )

    def _build_state():
        return {
            "messages": _consolidate_messages(all_messages),
            "todos": thread.values.todos if thread else [],
            "files": thread.values.files if thread else {},
            "email": thread.values.email if thread else None,
            "ui": thread.values.ui if thread else None,
        }

    try:
        async for event in graph.astream(
            {"messages": input_messages},
            config=stream_config,
            stream_mode="messages",
        ):
            if isinstance(event, tuple) and len(event) == 2:
                msg, meta = event
                msg_data = _serialize_msg(msg)
                if msg_data.get("content") or msg_data.get("tool_calls"):
                    all_messages.append(msg_data)
                    msg_tuple = [msg_data, _serialize_msg(meta)]
                    yield f"event: messages\ndata: {json.dumps(msg_tuple)}\n\n"
                    yield f"event: values\ndata: {json.dumps(_build_state())}\n\n"

                    if step % 5 == 0:
                        storage.save_checkpoint(
                            thread_id=thread_id,
                            checkpoint_id=str(uuid4()),
                            values=_build_state(),
                            metadata={
                                "graph_id": assistant_id,
                                "assistant_id": assistant_id,
                                "thread_id": thread_id,
                                "source": "loop",
                                "step": step,
                                "next_node": "assistant",
                                "parents": {},
                            },
                        )
                    step += 1
    except Exception as e:
        print(f"[STREAM] Error: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    finally:
        if thread:
            thread.values.messages = _consolidate_messages(all_messages)
            thread.status = "idle"
            thread.updated_at = datetime.utcnow()
        storage.save_checkpoint(
            thread_id=thread_id,
            checkpoint_id=str(uuid4()),
            values=_build_state(),
            metadata={
                "graph_id": assistant_id,
                "assistant_id": assistant_id,
                "thread_id": thread_id,
                "source": "loop",
                "step": step,
                "next_node": "__end__",
                "parents": {},
            },
        )
        yield f"event: values\ndata: {json.dumps(_build_state())}\n\n"


def _extract_messages(input: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not input or "messages" not in input:
        return []
    result = []
    for msg in input["messages"]:
        if isinstance(msg, dict):
            result.append(msg)
        elif hasattr(msg, "model_dump"):
            result.append(msg.model_dump())
        else:
            result.append({"content": str(msg), "type": "human"})
    return result


@router.post("/stream")
async def run_stream(
    thread_id: str,
    assistant_id: str | None = Body(None),
    input: dict[str, Any] | None = Body(None),
    config: dict[str, Any] | None = Body(None),
    command: dict[str, Any] | None = Body(None),
    interrupt_before: list[str] | None = Body(None),
    interrupt_after: list[str] | None = Body(None),
    checkpoint: str | dict[str, Any] | None = Body(None),
):
    thread = storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    if not assistant_id:
        raise HTTPException(status_code=422, detail="assistant_id is required")

    if assistant_id not in GRAPHS:
        raise HTTPException(
            status_code=404, detail=f"Assistant {assistant_id} not found"
        )

    messages = _extract_messages(input)
    thread.status = "running"

    return StreamingResponse(
        _stream_graph_with_checkpoints(
            GRAPHS[assistant_id], thread_id, messages, config, assistant_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
