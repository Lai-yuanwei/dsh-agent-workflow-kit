"""Tests for the demo task list."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from todo import TaskList  # noqa: E402


def test_add_returns_task_and_counts() -> None:
    tasks = TaskList()
    task = tasks.add("write the spec")

    assert task.title == "write the spec"
    assert task.done is False
    assert len(tasks) == 1


def test_add_strips_whitespace() -> None:
    tasks = TaskList()
    assert tasks.add("  review findings  ").title == "review findings"


@pytest.mark.parametrize("bad_title", ["", "   ", "\t\n"])
def test_add_rejects_empty_title(bad_title: str) -> None:
    with pytest.raises(ValueError):
        TaskList().add(bad_title)


def test_complete_marks_done() -> None:
    tasks = TaskList()
    tasks.add("a")
    tasks.add("b")

    tasks.complete(1)

    assert tasks.all_tasks()[1].done is True
    assert [task.title for task in tasks.pending()] == ["a"]


def test_complete_rejects_out_of_range() -> None:
    with pytest.raises(IndexError):
        TaskList().complete(3)


def test_pending_preserves_insertion_order() -> None:
    tasks = TaskList()
    for title in ("first", "second", "third"):
        tasks.add(title)
    tasks.complete(1)

    assert [task.title for task in tasks.pending()] == ["first", "third"]