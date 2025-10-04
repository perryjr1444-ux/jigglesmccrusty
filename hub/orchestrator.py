from __future__ import annotations

import asyncio
from collections import deque
from typing import Deque, Dict, Optional
from uuid import uuid4

from .models import Task, TaskCreate, TaskEnvelope, TaskStatus, Team
from .storage import TaskStorage


class Orchestrator:
    """In-memory task queues per team with persistence hooks."""

    def __init__(self, storage: TaskStorage) -> None:
        self._storage = storage
        self._queues: Dict[Team, Deque[str]] = {team: deque() for team in Team}
        self._events: Dict[Team, asyncio.Event] = {team: asyncio.Event() for team in Team}
        self._lock = asyncio.Lock()
        self._tasks: Dict[str, Task] = {}
        self._load_from_storage()

    def _load_from_storage(self) -> None:
        tasks = self._storage.all()
        self._tasks = tasks
        for task in tasks.values():
            if task.status != TaskStatus.completed:
                self._queues[task.team].append(task.id)
                if task.status == TaskStatus.queued:
                    continue
                # Mark as queued because in-memory queue lost consumer state
                task.with_status(TaskStatus.queued)
        self._storage.bulk_upsert(self._tasks.values())

    async def create_task(self, payload: TaskCreate) -> Task:
        task = Task(
            id=str(uuid4()),
            team=payload.team,
            type=payload.type,
            payload=payload.payload,
        )
        async with self._lock:
            self._tasks[task.id] = task
            self._queues[task.team].append(task.id)
            self._storage.upsert(task)
            self._events[task.team].set()
        return task

    async def next_task(self, team: Team, *, wait: bool = False) -> Optional[TaskEnvelope]:
        queue = self._queues[team]
        event = self._events[team]
        if wait:
            while not queue:
                event.clear()
                await event.wait()
        async with self._lock:
            if not queue:
                return None
            task_id = queue[0]
            task = self._tasks[task_id]
            task.with_status(TaskStatus.in_progress)
            self._storage.upsert(task)
            return TaskEnvelope(task=task, queue_position=0)

    async def acknowledge(self, task_id: str, result: Dict) -> Optional[Task]:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            task.with_result(result)
            queue = self._queues[task.team]
            if task_id in queue:
                queue.remove(task_id)
            self._storage.upsert(task)
            return task

    async def release(self, task_id: str) -> Optional[Task]:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            task.with_status(TaskStatus.queued)
            queue = self._queues[task.team]
            if task_id not in queue:
                queue.appendleft(task_id)
            self._storage.upsert(task)
            self._events[task.team].set()
            return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> Dict[str, Task]:
        return dict(self._tasks)
