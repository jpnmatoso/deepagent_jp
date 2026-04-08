import os
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
import json
import time

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    AIMessageChunk,
)

AGENTS_DIR = Path(__file__).parent.parent.parent / "agents"
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from storage import storage

router = APIRouter(prefix="/threads/{thread_id}/runs", tags=["runs"])

GRAPHS: dict[str, Any] = {}

LANGGRAPH_VERSION = os.environ.get("LANGRAPH_VERSION", "1.1.3")
LANGGRAPH_API_VERSION = os.environ.get("LANGRAPH_API_VERSION", "0.7.90")
LANGGRAPH_HOST = os.environ.get("LANGRAPH_HOST", "self-hosted")
LANGGRAPH_API_URL = os.environ.get("LANGRAPH_API_URL", "http://127.0.0.1:8100")


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


def _uuid7() -> str:
    ts = int(time.time() * 1000)
    ts_hex = f"{ts:012x}"
    rand = uuid4().hex[:20]
    return f"{ts_hex[:8]}-{ts_hex[8:12]}-7{rand[:3]}-8{rand[4:7]}-{rand[7:]}0"


def _serialize_msg(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        result = obj.model_dump()
        if isinstance(result, dict) and not result.get("id"):
            result["id"] = str(uuid4())
        return result
    elif hasattr(obj, "dict"):
        result = obj.dict()
        if isinstance(result, dict) and not result.get("id"):
            result["id"] = str(uuid4())
        return result
    elif isinstance(obj, (list, tuple)):
        return [_serialize_msg(i) for i in obj]
    elif isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            result[k] = _serialize_msg(v)
        if not result.get("id") and result.get("type") in (
            "human",
            "ai",
            "system",
            "tool",
            "AIMessageChunk",
        ):
            result["id"] = str(uuid4())
        return result
    return obj


def _parse_json_if_str(val: Any) -> Any:
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, ValueError):
            pass
    return val


def _dict_to_message(msg: dict[str, Any]) -> Any:
    msg_type = msg.get("type", "").lower()
    content = msg.get("content", "")
    if isinstance(content, list):
        content = [
            c if isinstance(c, dict) else {"type": "text", "text": c} for c in content
        ]
    if msg_type in ("human", "humanmessage"):
        return HumanMessage(content=content, id=msg.get("id"))
    elif msg_type in ("ai", "aimessage", "aimessagechunk"):
        kwargs: dict[str, Any] = {
            "content": content,
            "id": msg.get("id"),
        }
        # Process tool_calls: only keep those with valid structure
        raw_tool_calls = msg.get("tool_calls") or []
        valid_tc = []
        for tc in raw_tool_calls:
            if not isinstance(tc, dict):
                continue
            tc_id = tc.get("id")
            tc_name = tc.get("name", "")
            tc_args = tc.get("args", {})
            # Ensure args is always a dict
            if isinstance(tc_args, str):
                tc_args = _parse_json_if_str(tc_args)
            if not isinstance(tc_args, dict):
                tc_args = {}
            # Ensure name is a string
            if not isinstance(tc_name, str):
                tc_name = str(tc_name) if tc_name else ""
            # Only keep if has valid id
            if tc_id and isinstance(tc_id, str) and tc_id.strip():
                valid_tc.append(
                    {
                        "name": tc_name,
                        "args": tc_args,
                        "id": tc_id,
                        "type": tc.get("type", "tool_call"),
                    }
                )
        if valid_tc:
            kwargs["tool_calls"] = valid_tc
        # Ensure metadata fields are dicts
        for field in ["usage_metadata", "response_metadata", "additional_kwargs"]:
            val = msg.get(field)
            if val is not None:
                parsed = _parse_json_if_str(val)
                if isinstance(parsed, dict):
                    kwargs[field] = parsed
        return AIMessage(**kwargs)
    elif msg_type in ("system", "systemmessage"):
        return SystemMessage(content=content, id=msg.get("id"))
    elif msg_type in ("tool", "toolmessage"):
        tool_call_id = msg.get("tool_call_id")
        if not tool_call_id or not isinstance(tool_call_id, str):
            tool_call_id = msg.get("id", "") or str(uuid4())
        return ToolMessage(content=content, tool_call_id=tool_call_id, id=msg.get("id"))
    else:
        return HumanMessage(content=content, id=msg.get("id"))


def _dicts_to_messages(messages: list[dict[str, Any]]) -> list:
    return [_dict_to_message(m) if isinstance(m, dict) else m for m in messages]


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


class _NonSerializable:
    pass


def _make_serializable(obj: Any) -> Any:
    """Recursively ensure all objects are JSON-serializable."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_make_serializable(i) for i in obj]
    if isinstance(obj, dict):
        return {str(k): _make_serializable(v) for k, v in obj.items()}
    # For any other type, convert to string
    return str(obj)


def _sse(event: str, data: Any) -> str:
    try:
        safe_data = _make_serializable(data)
        return f"event: {event}\ndata: {json.dumps(safe_data)}\r\n\r\n"
    except Exception as e:
        print(f"[SSE] JSON serialization error for event '{event}': {e}")
        return f'event: error\ndata: {{"error": "SSE serialization failed: {str(e)}"}}\r\n\r\n'


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


async def _stream_graph_with_checkpoints(
    graph: Any,
    thread_id: str,
    input_messages: list[dict[str, Any]],
    config: dict[str, Any] | None,
    assistant_id: str,
) -> AsyncGenerator[str, None]:
    from storage import storage

    run_id = _uuid7()
    langgraph_request_id = str(uuid4())
    yield _sse("metadata", {"run_id": run_id, "attempt": 1})

    thread = await storage.get_thread(thread_id)
    history = await storage.get_history(thread_id, limit=1, offset=0)

    existing_messages = []
    if history and "values" in history[0] and "messages" in history[0]["values"]:
        existing_messages = history[0]["values"]["messages"]

    all_messages = list(existing_messages) + list(input_messages)

    await storage.save_checkpoint(
        thread_id=thread_id,
        checkpoint_id=_uuid7(),
        values={
            "messages": _consolidate_messages(list(all_messages)),
            "todos": [],
            "files": {},
            "email": None,
            "ui": None,
        },
        metadata={
            "graph_id": assistant_id,
            "assistant_id": assistant_id,
            "user_id": "",
            "created_by": "system",
            "run_id": run_id,
            "langgraph_request_id": langgraph_request_id,
            "thread_id": thread_id,
            "source": "loop",
            "step": 0,
            "next_node": "assistant",
            "parents": {},
        },
    )

    step = 0
    stream_config = (
        {"configurable": {"thread_id": thread_id}} if config is None else config
    )

    def _build_state():
        consolidated = _consolidate_messages(all_messages)
        base_values = {}
        if history and "values" in history[0]:
            base_values = history[0]["values"]
        thread_todos = (
            thread.values.todos if thread and hasattr(thread.values, "todos") else []
        )
        thread_files = (
            thread.values.files if thread and hasattr(thread.values, "files") else {}
        )
        return {
            "messages": consolidated,
            "todos": base_values.get("todos", thread_todos),
            "files": base_values.get("files", thread_files),
            "email": base_values.get("email", None),
            "ui": base_values.get("ui", None),
        }

    try:
        graph_messages = _dicts_to_messages(all_messages)
        print(f"[STREAM] Converting {len(all_messages)} messages to LangChain objects")
        for i, gm in enumerate(graph_messages):
            msg_type = type(gm).__name__
            content_preview = ""
            if hasattr(gm, "content"):
                c = gm.content
                if isinstance(c, str):
                    content_preview = c[:80]
                elif isinstance(c, list):
                    content_preview = f"[list:{len(c)}]"
            print(f"  msg[{i}] {msg_type}: {content_preview}")
        async for event in graph.astream(
            {"messages": graph_messages},
            config=stream_config,
            stream_mode="messages",
        ):
            if isinstance(event, tuple) and len(event) == 2:
                msg, meta = event
                msg_data = _serialize_msg(msg)
                if not (msg_data.get("content") or msg_data.get("tool_calls")):
                    continue

                all_messages.append(msg_data)
                meta_data = _serialize_msg(meta)

                langgraph_meta = {
                    "created_by": "system",
                    "graph_id": assistant_id,
                    "assistant_id": assistant_id,
                    "run_attempt": 1,
                    "langgraph_version": LANGGRAPH_VERSION,
                    "langgraph_api_version": LANGGRAPH_API_VERSION,
                    "langgraph_plan": "enterprise",
                    "langgraph_host": LANGGRAPH_HOST,
                    "langgraph_api_url": LANGGRAPH_API_URL,
                    "langgraph_request_id": langgraph_request_id,
                    "run_id": run_id,
                    "thread_id": thread_id,
                    "user_id": "",
                    "langgraph_step": meta_data.get("langgraph_step", step),
                    "langgraph_node": meta_data.get("langgraph_node", "assistant"),
                    "langgraph_triggers": meta_data.get("langgraph_triggers", []),
                    "langgraph_path": meta_data.get("langgraph_path", []),
                    "langgraph_checkpoint_ns": meta_data.get(
                        "langgraph_checkpoint_ns", f"{assistant_id}:{thread_id}"
                    ),
                    "checkpoint_ns": meta_data.get(
                        "checkpoint_ns", f"{assistant_id}:{thread_id}"
                    ),
                }
                meta_data.update(langgraph_meta)

                msg_tuple = [msg_data, meta_data]
                yield _sse("messages", msg_tuple)
                yield _sse("values", _build_state())

                if step % 5 == 0:
                    await storage.save_checkpoint(
                        thread_id=thread_id,
                        checkpoint_id=_uuid7(),
                        values=_build_state(),
                        metadata={
                            "graph_id": assistant_id,
                            "assistant_id": assistant_id,
                            "user_id": "",
                            "created_by": "system",
                            "run_id": run_id,
                            "langgraph_request_id": langgraph_request_id,
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
        yield _sse("error", {"error": str(e)})
    finally:
        try:
            if thread:
                thread.values.messages = _consolidate_messages(all_messages)
                thread.status = "idle"
                thread.updated_at = datetime.utcnow()
            final_state = _build_state()
            await storage.save_checkpoint(
                thread_id=thread_id,
                checkpoint_id=_uuid7(),
                values=final_state,
                metadata={
                    "graph_id": assistant_id,
                    "assistant_id": assistant_id,
                    "user_id": "",
                    "created_by": "system",
                    "run_id": run_id,
                    "langgraph_request_id": langgraph_request_id,
                    "thread_id": thread_id,
                    "source": "loop",
                    "step": step,
                    "next_node": "__end__",
                    "parents": {},
                },
            )
            print(
                f"[STREAM] Final checkpoint saved with {len(final_state.get('messages', []))} messages"
            )
        except Exception as e:
            print(f"[STREAM] Finally block error: {e}")
        yield _sse("values", _build_state())


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
):
    thread = await storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    if not assistant_id:
        raise HTTPException(status_code=422, detail="assistant_id is required")

    if assistant_id not in GRAPHS:
        raise HTTPException(
            status_code=404, detail=f"Assistant {assistant_id} not found"
        )

    messages = _extract_messages(input)

    return StreamingResponse(
        _stream_graph_with_checkpoints(
            GRAPHS[assistant_id], thread_id, messages, config, assistant_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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
    thread = await storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    if not assistant_id:
        raise HTTPException(status_code=422, detail="assistant_id is required")

    if assistant_id not in GRAPHS:
        raise HTTPException(
            status_code=404, detail=f"Assistant {assistant_id} not found"
        )

    messages = _extract_messages(input)

    return StreamingResponse(
        _stream_graph_with_checkpoints(
            GRAPHS[assistant_id], thread_id, messages, config, assistant_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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
    thread = await storage.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    if not assistant_id:
        raise HTTPException(status_code=422, detail="assistant_id is required")

    if assistant_id not in GRAPHS:
        raise HTTPException(
            status_code=404, detail=f"Assistant {assistant_id} not found"
        )

    graph = GRAPHS[assistant_id]
    run_id = _uuid7()
    messages = _extract_messages(input)
    thread.status = "running"

    try:
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
        await storage.update_thread(thread_id, {"status": "idle"})
    except Exception as e:
        thread.status = "error"
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "assistant_id": assistant_id,
        "status": thread.status,
        "created_at": datetime.utcnow().isoformat(),
        "messages": _consolidate_messages(thread.values.messages),
    }
