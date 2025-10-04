from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Dict, Iterable

from .models import Task


class TaskStorage:
    """Simple JSON file storage for tasks and results."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({})

    def _read(self) -> Dict[str, Dict]:
        with self._path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, payload: Dict[str, Dict]) -> None:
        with self._path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)

    def upsert(self, task: Task) -> None:
        with self._lock:
            data = self._read()
            data[task.id] = task.model_dump(mode="json")
            self._write(data)

    def bulk_upsert(self, tasks: Iterable[Task]) -> None:
        with self._lock:
            data = self._read()
            for task in tasks:
                data[task.id] = task.model_dump(mode="json")
            self._write(data)

    def get(self, task_id: str) -> Task | None:
        with self._lock:
            data = self._read()
        payload = data.get(task_id)
        if payload is None:
            return None
        return Task.model_validate(payload)

    def all(self) -> Dict[str, Task]:
        with self._lock:
            data = self._read()
        return {task_id: Task.model_validate(payload) for task_id, payload in data.items()}
