import copy
import os
import json
import time
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)

import asyncpg

from models import Thread, ThreadState, ThreadCreate


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid7() -> str:
    ts = int(time.time() * 1000)
    ts_hex = f"{ts:012x}"
    rand = uuid4().hex[:20]
    return f"{ts_hex[:8]}-{ts_hex[8:12]}-7{rand[:3]}-8{rand[4:7]}-{rand[7:]}0"


def _format_history_entry(
    checkpoint_id: str,
    thread_id: str,
    checkpoint_ns: str,
    values: dict[str, Any],
    metadata: dict[str, Any],
    created_at: str,
    parent_checkpoint_id: str | None,
    next_nodes: list[str],
    tasks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    checkpoint_obj = {
        "checkpoint_id": checkpoint_id,
        "thread_id": thread_id,
        "checkpoint_ns": checkpoint_ns,
    }
    parent_cp = None
    if parent_checkpoint_id:
        parent_cp = {
            "checkpoint_id": parent_checkpoint_id,
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
        }
    return {
        "values": values,
        "next": next_nodes,
        "tasks": tasks or [],
        "metadata": metadata,
        "created_at": created_at,
        "checkpoint": checkpoint_obj,
        "parent_checkpoint": parent_cp,
        "interrupts": [],
        "checkpoint_id": checkpoint_id,
        "parent_checkpoint_id": parent_checkpoint_id,
    }


class Checkpoint:
    def __init__(
        self,
        checkpoint_id: str,
        thread_id: str,
        values: dict[str, Any],
        metadata: dict[str, Any],
        created_at: str,
        parent_checkpoint_id: str | None = None,
    ):
        self.checkpoint_id = checkpoint_id
        self.thread_id = thread_id
        self.values = values
        self.metadata = metadata
        self.created_at = created_at
        self.parent_checkpoint_id = parent_checkpoint_id


class InMemoryStorage:
    def __init__(self):
        self._threads: dict[str, Thread] = {}
        self._checkpoints: dict[str, list[Checkpoint]] = {}

    async def init(self):
        pass

    async def close(self):
        pass

    async def create_thread(self, data: ThreadCreate | None = None) -> Thread:
        thread_id = data.thread_id if data and data.thread_id else str(uuid4())
        thread = Thread(
            thread_id=thread_id,
            metadata=data.metadata if data else {},
        )
        self._threads[thread_id] = thread
        self._checkpoints[thread_id] = []

        await self.save_checkpoint(
            thread_id=thread_id,
            checkpoint_id=_uuid7(),
            values={
                "messages": [],
                "todos": [],
                "files": {},
                "email": None,
                "ui": None,
            },
            metadata={
                "graph_id": data.metadata.get("graph_id", "") if data else "",
                "assistant_id": data.metadata.get("assistant_id", "") if data else "",
                "user_id": "",
                "created_by": "system",
                "thread_id": thread_id,
                "source": "input",
                "step": -1,
                "next_node": "__start__",
                "parents": {},
            },
        )

        return thread

    async def get_thread(self, thread_id: str) -> Thread | None:
        thread = self._threads.get(thread_id)
        if not thread:
            return None

        checkpoints = self._checkpoints.get(thread_id, [])
        if checkpoints:
            last_checkpoint = checkpoints[-1]
            if last_checkpoint.values.get("messages"):
                thread.values.messages = last_checkpoint.values.get("messages", [])
            if last_checkpoint.values.get("todos"):
                thread.values.todos = last_checkpoint.values.get("todos", [])
            if last_checkpoint.values.get("files"):
                thread.values.files = last_checkpoint.values.get("files", {})

        return thread

    async def list_threads(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[Thread]:
        threads = list(self._threads.values())
        if status:
            threads = [t for t in threads if t.status == status]
        if metadata_filter:
            for key, value in metadata_filter.items():
                threads = [t for t in threads if t.metadata.get(key) == value]
        threads.sort(key=lambda t: t.updated_at, reverse=True)
        return threads[offset : offset + limit]

    async def update_thread(
        self,
        thread_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Thread | None:
        thread = self._threads.get(thread_id)
        if not thread:
            return None
        if metadata is not None:
            thread.metadata.update(metadata)
        thread.updated_at = datetime.utcnow()
        return thread

    async def get_state(self, thread_id: str) -> ThreadState | None:
        thread = self._threads.get(thread_id)
        return thread.values if thread else None

    async def update_state(
        self,
        thread_id: str,
        values: dict[str, Any] | None = None,
    ) -> Thread | None:
        thread = self._threads.get(thread_id)
        if not thread:
            return None
        if values:
            for key, value in values.items():
                if hasattr(thread.values, key):
                    setattr(thread.values, key, value)
        thread.updated_at = datetime.utcnow()
        return thread

    async def save_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str,
        values: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        if thread_id not in self._checkpoints:
            self._checkpoints[thread_id] = []
        parent_id = None
        if self._checkpoints[thread_id]:
            parent_id = self._checkpoints[thread_id][-1].checkpoint_id
        values_copy = copy.deepcopy(values)

        full_metadata = {
            "graph_id": metadata.get("graph_id", ""),
            "assistant_id": metadata.get("assistant_id", ""),
            "user_id": metadata.get("user_id", ""),
            "created_by": metadata.get("created_by", "system"),
            "run_attempt": metadata.get("run_attempt", 1),
            "langgraph_version": metadata.get("langgraph_version", "1.1.3"),
            "langgraph_api_version": metadata.get("langgraph_api_version", "0.7.90"),
            "langgraph_plan": metadata.get("langgraph_plan", "enterprise"),
            "langgraph_host": metadata.get("langgraph_host", "self-hosted"),
            "langgraph_api_url": metadata.get(
                "langgraph_api_url", "http://127.0.0.1:8100"
            ),
            "langgraph_request_id": metadata.get("langgraph_request_id", str(uuid4())),
            "run_id": metadata.get("run_id", _uuid7()),
            "thread_id": thread_id,
            "source": metadata.get("source", "loop"),
            "step": metadata.get("step", 0),
            "parents": metadata.get("parents", {}),
            "langgraph_auth_user_id": metadata.get("user_id", ""),
        }

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            thread_id=thread_id,
            values=values_copy,
            metadata=full_metadata,
            created_at=_now_iso(),
            parent_checkpoint_id=parent_id,
        )
        self._checkpoints[thread_id].append(checkpoint)

    async def get_history(
        self,
        thread_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        checkpoints = self._checkpoints.get(thread_id, [])
        reversed_checkpoints = list(reversed(checkpoints))
        sliced = reversed_checkpoints[offset : offset + limit]

        result = []
        for cp in sliced:
            next_node = cp.metadata.get("next_node", "assistant")
            next_nodes = [] if next_node == "__end__" else [next_node]

            tasks = []
            for node_name in next_nodes:
                tasks.append(
                    {
                        "id": str(uuid4()),
                        "name": node_name,
                        "path": ["__pregel_pull", node_name],
                        "error": None,
                        "interrupts": [],
                        "checkpoint": None,
                        "state": None,
                        "result": None,
                    }
                )

            result.append(
                _format_history_entry(
                    checkpoint_id=cp.checkpoint_id,
                    thread_id=cp.thread_id,
                    checkpoint_ns="",
                    values=cp.values,
                    metadata=cp.metadata,
                    created_at=cp.created_at,
                    parent_checkpoint_id=cp.parent_checkpoint_id,
                    next_nodes=next_nodes,
                    tasks=tasks,
                )
            )
        return result

    async def delete_thread(self, thread_id: str) -> bool:
        if thread_id in self._threads:
            del self._threads[thread_id]
            if thread_id in self._checkpoints:
                del self._checkpoints[thread_id]
            return True
        return False


class PostgresStorage:
    """PostgreSQL storage using the existing LangGraph server schema.

    Tables used:
    - threads_metadata: thread_id, created_at, updated_at, metadata
    - checkpoints: thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint (jsonb), metadata (jsonb)
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool: asyncpg.Pool | None = None

    async def init(self):
        self._pool = await asyncpg.create_pool(dsn=self.database_url)

    async def close(self):
        if self._pool:
            await self._pool.close()

    async def create_thread(self, data: ThreadCreate | None = None) -> Thread:
        thread_id = data.thread_id if data and data.thread_id else str(uuid4())
        now = datetime.utcnow()
        thread = Thread(
            thread_id=thread_id,
            metadata=data.metadata if data else {},
            created_at=now,
            updated_at=now,
        )
        async with self._pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO threads_metadata (thread_id, created_at, updated_at, metadata)
                   VALUES ($1, $2, $3, $4)
                   ON CONFLICT (thread_id) DO NOTHING""",
                thread_id,
                now,
                now,
                json.dumps(thread.metadata),
            )

        await self.save_checkpoint(
            thread_id=thread_id,
            checkpoint_id=_uuid7(),
            values={
                "messages": [],
                "todos": [],
                "files": {},
                "email": None,
                "ui": None,
            },
            metadata={
                "graph_id": data.metadata.get("graph_id", "") if data else "",
                "assistant_id": data.metadata.get("assistant_id", "") if data else "",
                "user_id": "",
                "created_by": "system",
                "thread_id": thread_id,
                "source": "input",
                "step": -1,
                "next_node": "__start__",
                "parents": {},
            },
        )

        return thread

    async def get_thread(self, thread_id: str) -> Thread | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM threads_metadata WHERE thread_id = $1", thread_id
            )
            if not row:
                return None
            metadata = row["metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            cp_row = await conn.fetchrow(
                """SELECT checkpoint FROM checkpoints
                   WHERE thread_id = $1
                   ORDER BY checkpoint_id DESC LIMIT 1""",
                thread_id,
            )

            messages = []
            todos = []
            files = {}
            if cp_row:
                checkpoint = cp_row["checkpoint"]
                if isinstance(checkpoint, str):
                    checkpoint = json.loads(checkpoint)
                messages = checkpoint.get("messages", [])
                todos = checkpoint.get("todos", [])
                files = checkpoint.get("files", {})

            return Thread(
                thread_id=row["thread_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                metadata=metadata or {},
                status="idle",
                values=ThreadState(messages=messages, todos=todos, files=files),
                config={},
            )

    async def list_threads(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[Thread]:
        query = "SELECT * FROM threads_metadata"
        conditions = []
        params: list = []
        param_idx = 1

        if metadata_filter:
            for key, value in metadata_filter.items():
                conditions.append(f"metadata->>'{key}' = ${param_idx}::text")
                params.append(str(value))
                param_idx += 1

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY updated_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        thread_ids = [r["thread_id"] for r in rows]

        latest_checkpoints = {}
        if thread_ids:
            placeholders = ",".join(f"${param_idx + i}" for i in range(len(thread_ids)))
            cp_query = f"""
                SELECT DISTINCT ON (thread_id) thread_id, checkpoint
                FROM checkpoints
                WHERE thread_id IN ({placeholders})
                ORDER BY thread_id, checkpoint_id DESC
            """
            async with self._pool.acquire() as conn:
                cp_rows = await conn.fetch(cp_query, *thread_ids)
            for cp_row in cp_rows:
                checkpoint = cp_row["checkpoint"]
                if isinstance(checkpoint, str):
                    checkpoint = json.loads(checkpoint)
                latest_checkpoints[cp_row["thread_id"]] = checkpoint

        result = []
        for r in rows:
            tid = r["thread_id"]
            cp_values = latest_checkpoints.get(tid, {})
            messages = cp_values.get("messages", [])

            result.append(
                Thread(
                    thread_id=tid,
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    metadata=(
                        json.loads(r["metadata"])
                        if isinstance(r["metadata"], str)
                        else r["metadata"]
                    )
                    or {},
                    status="idle",
                    values=ThreadState(messages=messages),
                    config={},
                )
            )
        return result

    async def update_thread(
        self,
        thread_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Thread | None:
        thread = await self.get_thread(thread_id)
        if not thread:
            return None

        updates = ["updated_at = NOW()"]
        params: list = [thread_id]
        param_idx = 2

        if metadata is not None:
            updates.append(
                f"metadata = COALESCE(metadata, '{{}}') || ${param_idx}::jsonb"
            )
            params.append(json.dumps(metadata))
            param_idx += 1
            thread.metadata.update(metadata)

        query = f"UPDATE threads_metadata SET {', '.join(updates)} WHERE thread_id = $1 RETURNING *"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            if row:
                thread.updated_at = row["updated_at"]

        return thread

    async def get_state(self, thread_id: str) -> ThreadState | None:
        thread = await self.get_thread(thread_id)
        return thread.values if thread else None

    async def update_state(
        self,
        thread_id: str,
        values: dict[str, Any] | None = None,
    ) -> Thread | None:
        thread = await self.get_thread(thread_id)
        if not thread:
            return None
        if values:
            for key, value in values.items():
                if hasattr(thread.values, key):
                    setattr(thread.values, key, value)
        thread.updated_at = datetime.utcnow()
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE threads_metadata SET updated_at = NOW() WHERE thread_id = $1",
                thread_id,
            )
        return thread

    async def save_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str,
        values: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        parent_id = None
        values_copy = copy.deepcopy(values)

        full_metadata = {
            "graph_id": metadata.get("graph_id", ""),
            "assistant_id": metadata.get("assistant_id", ""),
            "user_id": metadata.get("user_id", ""),
            "created_by": metadata.get("created_by", "system"),
            "run_attempt": metadata.get("run_attempt", 1),
            "langgraph_version": metadata.get("langgraph_version", "1.1.3"),
            "langgraph_api_version": metadata.get("langgraph_api_version", "0.7.90"),
            "langgraph_plan": metadata.get("langgraph_plan", "enterprise"),
            "langgraph_host": metadata.get("langgraph_host", "self-hosted"),
            "langgraph_api_url": metadata.get(
                "langgraph_api_url", "http://127.0.0.1:8100"
            ),
            "langgraph_request_id": metadata.get("langgraph_request_id", str(uuid4())),
            "run_id": metadata.get("run_id", _uuid7()),
            "thread_id": thread_id,
            "source": metadata.get("source", "loop"),
            "step": metadata.get("step", 0),
            "parents": metadata.get("parents", {}),
            "langgraph_auth_user_id": metadata.get("user_id", ""),
        }

        values_json = json.dumps(values_copy)
        metadata_json = json.dumps(full_metadata)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT checkpoint_id FROM checkpoints
                   WHERE thread_id = $1
                   ORDER BY checkpoint_id DESC LIMIT 1""",
                thread_id,
            )
            if row:
                parent_id = row["checkpoint_id"]

            await conn.execute(
                """INSERT INTO checkpoints
                   (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)
                   ON CONFLICT (thread_id, checkpoint_ns, checkpoint_id)
                   DO UPDATE SET checkpoint = $6, metadata = $7""",
                thread_id,
                "",
                checkpoint_id,
                parent_id,
                "graph",
                values_json,
                metadata_json,
            )
            print(
                f"[STORAGE] Saved checkpoint {checkpoint_id} with {len(values.get('messages', []))} messages"
            )

    async def get_history(
        self,
        thread_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM checkpoints
                   WHERE thread_id = $1
                   ORDER BY checkpoint_id DESC
                   LIMIT $2 OFFSET $3""",
                thread_id,
                limit,
                offset,
            )

        print(
            f"[STORAGE] get_history: found {len(rows)} checkpoints for thread {thread_id}"
        )
        for i, row in enumerate(rows):
            print(f"[STORAGE] checkpoint {i}: checkpoint_id={row['checkpoint_id']}")

        result = []
        for i, row in enumerate(rows):
            metadata = row["metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            values = row["checkpoint"]
            if isinstance(values, str):
                values = json.loads(values)

            next_node = metadata.get("next_node", "assistant")
            if next_node == "__end__":
                next_nodes = []
            else:
                global_idx = offset + i
                if global_idx + 1 < (await self._count_checkpoints(thread_id)):
                    next_meta_row = await self._get_checkpoint_by_offset(
                        thread_id, global_idx + 1
                    )
                    if next_meta_row:
                        next_meta = next_meta_row["metadata"]
                        if isinstance(next_meta, str):
                            next_meta = json.loads(next_meta)
                        next_nodes = [next_meta.get("next_node", "assistant")]
                    else:
                        next_nodes = [next_node]
                else:
                    next_nodes = [next_node]

            tasks = []
            if next_nodes and next_nodes != ["__end__"]:
                for node_name in next_nodes:
                    tasks.append(
                        {
                            "id": str(uuid4()),
                            "name": node_name,
                            "path": ["__pregel_pull", node_name],
                            "error": None,
                            "interrupts": [],
                            "checkpoint": None,
                            "state": None,
                            "result": None,
                        }
                    )

            created_at = metadata.get("created_at")
            if not created_at:
                created_at = _now_iso()

            result.append(
                _format_history_entry(
                    checkpoint_id=row["checkpoint_id"],
                    thread_id=row["thread_id"],
                    checkpoint_ns=row.get("checkpoint_ns", ""),
                    values=values,
                    metadata=metadata,
                    created_at=created_at,
                    parent_checkpoint_id=row["parent_checkpoint_id"],
                    next_nodes=next_nodes,
                    tasks=tasks,
                )
            )
        return result

    async def _count_checkpoints(self, thread_id: str) -> int:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT COUNT(*) as cnt FROM checkpoints WHERE thread_id = $1",
                thread_id,
            )
            return row["cnt"] if row else 0

    async def _get_checkpoint_by_offset(
        self, thread_id: str, offset: int
    ) -> dict | None:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT metadata FROM checkpoints
                   WHERE thread_id = $1
                   ORDER BY checkpoint_id DESC
                   LIMIT 1 OFFSET $2""",
                thread_id,
                offset,
            )
            return rows[0] if rows else None

    async def delete_thread(self, thread_id: str) -> bool:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM checkpoints WHERE thread_id = $1", thread_id
            )
            result = await conn.execute(
                "DELETE FROM threads_metadata WHERE thread_id = $1", thread_id
            )
            return result.split()[-1] != "0"


def _get_database_url() -> str | None:
    return os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URI")


class StorageProxy:
    """Proxy that always resolves to the current storage instance.

    This is needed because `init_postgres()` reassigns the module-level
    `storage` variable after other modules have already imported it.
    Without the proxy, those modules would hold a stale reference to the
    original InMemoryStorage instance.
    """

    def __init__(self):
        self._instance: InMemoryStorage | PostgresStorage = InMemoryStorage()

    def _get(self):
        return self._instance

    def __getattr__(self, name):
        return getattr(self._get(), name)

    def set(self, instance: InMemoryStorage | PostgresStorage):
        self._instance = instance


storage = StorageProxy()


async def init_postgres():
    db_url = _get_database_url()
    if db_url:
        try:
            pg = PostgresStorage(db_url)
            await pg.init()
            storage.set(pg)
            print(f"PostgreSQL storage initialized: {db_url.split('@')[-1]}")
        except Exception as e:
            print(f"Failed to initialize PostgreSQL, falling back to in-memory: {e}")
            storage.set(InMemoryStorage())
    else:
        print("No DATABASE_URL or POSTGRES_URI found, using in-memory storage")
        storage.set(InMemoryStorage())
