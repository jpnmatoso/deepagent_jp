from typing import Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["human", "ai", "system", "tool"]
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    invalid_tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    additional_kwargs: dict[str, Any] = Field(default_factory=dict)
    response_metadata: dict[str, Any] = Field(default_factory=dict)
    example: bool = False


class ThreadState(BaseModel):
    messages: list[Message] = Field(default_factory=list)
    todos: list[dict[str, Any]] = Field(default_factory=list)
    files: dict[str, str] = Field(default_factory=dict)
    email: dict[str, Any] | None = None
    ui: dict[str, Any] | None = None


class Thread(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: Literal["idle", "busy", "interrupted", "error", "running"] = "idle"
    values: ThreadState = Field(default_factory=ThreadState)
    config: dict[str, Any] = Field(default_factory=dict)


class ThreadCreate(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)
    thread_id: str | None = None


class ThreadUpdate(BaseModel):
    metadata: dict[str, Any] | None = None


class ThreadStateUpdate(BaseModel):
    values: dict[str, Any] | None = None


class Assistant(BaseModel):
    assistant_id: str
    graph_id: str
    name: str | None = None
    description: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class RunInput(BaseModel):
    input: dict[str, Any] | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    command: dict[str, Any] | None = None
    interrupt_before: list[str] | None = None
    interrupt_after: list[str] | None = None
    checkpoint: str | None = None


class RunCreate(BaseModel):
    assistant_id: str
    input: dict[str, Any] | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    command: dict[str, Any] | None = None
    interrupt_before: list[str] | None = None
    interrupt_after: list[str] | None = None
    checkpoint: str | None = None


class Run(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    thread_id: str
    assistant_id: str
    status: Literal["pending", "running", "completed", "failed", "interrupted"] = (
        "pending"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CheckpointMetadata(BaseModel):
    thread_id: str
    checkpoint_id: str
    graph_id: str
    source: str
    step: int
    writes: dict[str, Any] = Field(default_factory=dict)
    parents: dict[str, str] = Field(default_factory=dict)


class ThreadStateResponse(BaseModel):
    values: dict[str, Any]
    next: list[str] = Field(default_factory=list)
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    metadata: CheckpointMetadata
    created_at: datetime
    checkpoint: dict[str, Any] | None = None
    parent_checkpoint: dict[str, Any] | None = None
    checkpoint_id: str
    parent_checkpoint_id: str | None = None
