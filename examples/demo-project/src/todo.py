"""Minimal in-memory task list used by the team-kit demo.

The demo deliberately keeps one small module so the workflow, not the code, is
the subject under test.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Task:
    """A single task entry."""

    title: str
    done: bool = False


class TaskList:
    """An ordered list of tasks with add/complete/query operations."""

    def __init__(self) -> None:
        self._tasks: list[Task] = []

    def __len__(self) -> int:
        return len(self._tasks)

    def add(self, title: str) -> Task:
        """Append a task and return it. Empty titles are rejected."""
        cleaned = title.strip()
        if not cleaned:
            raise ValueError("task title must not be empty")
        task = Task(title=cleaned)
        self._tasks.append(task)
        return task

    def complete(self, index: int) -> Task:
        """Mark the task at ``index`` as done and return it."""
        try:
            task = self._tasks[index]
        except IndexError as exc:
            raise IndexError(f"no task at index {index}") from exc
        task.done = True
        return task

    def pending(self) -> list[Task]:
        """Return the tasks that are not done, in insertion order."""
        return [task for task in self._tasks if not task.done]

    def all_tasks(self) -> list[Task]:
        return list(self._tasks)