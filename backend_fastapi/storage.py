from datetime import datetime
from uuid import uuid4
from typing import Any
from models import Thread, ThreadState, ThreadCreate


class Checkpoint:
    def __init__(
        self,
        checkpoint_id: str,
        thread_id: str,
        values: dict[str, Any],
        metadata: dict[str, Any],
        created_at: datetime,
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

    def create_thread(self, data: ThreadCreate | None = None) -> Thread:
        thread_id = data.thread_id if data and data.thread_id else str(uuid4())
        thread = Thread(
            thread_id=thread_id,
            metadata=data.metadata if data else {},
        )
        self._threads[thread_id] = thread
        self._checkpoints[thread_id] = []
        return thread

    def get_thread(self, thread_id: str) -> Thread | None:
        return self._threads.get(thread_id)

    def list_threads(
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

    def update_thread(
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

    def get_state(self, thread_id: str) -> ThreadState | None:
        thread = self._threads.get(thread_id)
        return thread.values if thread else None

    def update_state(
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

    def save_checkpoint(
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

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            thread_id=thread_id,
            values=values,
            metadata=metadata,
            created_at=datetime.utcnow(),
            parent_checkpoint_id=parent_id,
        )
        self._checkpoints[thread_id].append(checkpoint)

    def get_history(
        self,
        thread_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        checkpoints = self._checkpoints.get(thread_id, [])

        reversed_checkpoints = list(reversed(checkpoints))
        result = []

        for i, cp in enumerate(reversed_checkpoints[offset : offset + limit]):
            next_nodes = []
            if i < len(reversed_checkpoints) - 1:
                next_checkpoint = reversed_checkpoints[offset + i + 1]
                next_nodes = [next_checkpoint.metadata.get("next_node", "assistant")]
            else:
                next_nodes = ["assistant"]

            result.append(
                {
                    "values": cp.values,
                    "next": next_nodes,
                    "tasks": [],
                    "metadata": cp.metadata,
                    "created_at": cp.created_at.isoformat() + "+00:00",
                    "checkpoint": {
                        "checkpoint_id": cp.checkpoint_id,
                        "thread_id": cp.thread_id,
                        "checkpoint_ns": "",
                    },
                    "parent_checkpoint": {
                        "checkpoint_id": cp.parent_checkpoint_id,
                        "thread_id": cp.thread_id,
                        "checkpoint_ns": "",
                    }
                    if cp.parent_checkpoint_id
                    else None,
                    "interrupts": [],
                    "checkpoint_id": cp.checkpoint_id,
                    "parent_checkpoint_id": cp.parent_checkpoint_id,
                }
            )

        return result

    def delete_thread(self, thread_id: str) -> bool:
        if thread_id in self._threads:
            del self._threads[thread_id]
            if thread_id in self._checkpoints:
                del self._checkpoints[thread_id]
            return True
        return False


storage = InMemoryStorage()
