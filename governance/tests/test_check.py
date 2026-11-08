"""Tests for governance/check.py.

The tests exercise the checker against temporary project trees. They prove the
logic; the end-to-end wiring is proved by real AgentTeams tasks whose ``verify``
runs the command. Install the checker as ``./tools/governance/`` in a project
before using these paths.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOVERNANCE = HERE.parent
sys.path.insert(0, str(GOVERNANCE))

import check  # noqa: E402


def make_root(tmp_path: Path) -> Path:
    """Create a temporary project with the checker installed as ./tools/governance/."""
    root = tmp_path / "project"
    target = root / "tools" / "governance"
    target.mkdir(parents=True)
    shutil.copy(GOVERNANCE / "check.py", target / "check.py")
    shutil.copy(GOVERNANCE / "roles.example.json", target / "roles.json")
    return root


def make_team(root: Path, tasks: list[dict]) -> None:
    directory = root / ".agent-teams" / "dev-team-default"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "team.json").write_text(
        json.dumps({"tasks": tasks, "members": []}, ensure_ascii=False), encoding="utf-8"
    )


def run(root: Path, *argv: str) -> int:
    return check.main(["--root", str(root), *argv])


def test_developer_cannot_own_spec(tmp_path):
    root = make_root(tmp_path)
    roles = check.load_roles(root)
    assert check.classify(roles["developer"], "docs/planning/x/SPEC.md")[0] == "denied"
    assert check.classify(roles["developer"], "src/app.py")[0] == "allowed"
    assert check.classify(roles["developer"], "unknown/file.txt")[0] == "not_allowed"


def test_scope_blocks_protected_document(tmp_path):
    root = make_root(tmp_path)
    make_team(root, [{"id": "t1", "kind": "implementation", "assignee": "developer"}])
    (root / "_fixture").mkdir()
    (root / "_fixture" / "SPEC.md").write_text("v1\n", encoding="utf-8")
    assert run(root, "baseline", "--task", "t1") == 0

    (root / "_fixture" / "SPEC.md").write_text("v2\n", encoding="utf-8")
    assert run(root, "scope", "--task", "t1") == 2


def test_scope_allows_authorised_code_change(tmp_path):
    root = make_root(tmp_path)
    make_team(root, [{"id": "t1", "kind": "implementation", "assignee": "developer"}])
    assert run(root, "baseline", "--task", "t1") == 0

    (root / "src" / "app").mkdir(parents=True)
    (root / "src" / "app" / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    assert run(root, "scope", "--task", "t1") == 0


def test_scope_cannot_verify_without_baseline(tmp_path):
    root = make_root(tmp_path)
    make_team(root, [{"id": "t1", "kind": "implementation", "assignee": "developer"}])
    assert run(root, "scope", "--task", "t1") == 3


def test_review_rejects_self_review(tmp_path):
    root = make_root(tmp_path)
    make_team(
        root,
        [
            {"id": "t1", "kind": "implementation", "assignee": "developer", "status": "completed"},
            {"id": "t2", "kind": "review", "assignee": "developer", "reviewedTaskId": "t1"},
        ],
    )
    assert run(root, "review", "--task", "t2") == 2


def test_review_accepts_independent_reviewer(tmp_path):
    root = make_root(tmp_path)
    make_team(
        root,
        [
            {"id": "t1", "kind": "implementation", "assignee": "developer", "status": "completed"},
            {"id": "t2", "kind": "review", "assignee": "architect", "reviewedTaskId": "t1"},
        ],
    )
    assert run(root, "review", "--task", "t2") == 0


def test_review_fails_when_repair_owner_matches(tmp_path):
    root = make_root(tmp_path)
    make_team(
        root,
        [
            {"id": "t3", "kind": "implementation", "assignee": "developer", "status": "completed"},
            {
                "id": "t4",
                "kind": "repair",
                "assignee": "developer",
                "sourceTaskId": "t3",
                "dependencies": ["t3"],
                "status": "completed",
            },
            {"id": "t5", "kind": "review", "assignee": "developer", "reviewedTaskId": "t4"},
        ],
    )
    assert run(root, "review", "--task", "t5") == 2


def test_review_requires_reviewer_identity(tmp_path):
    root = make_root(tmp_path)
    make_team(
        root,
        [
            {"id": "t13", "kind": "implementation", "assignee": "developer"},
            {"id": "t16", "kind": "review", "reviewedTaskId": "t13"},
        ],
    )
    assert run(root, "review", "--task", "t16") == 3


def test_review_requires_lineage_owner(tmp_path):
    root = make_root(tmp_path)
    make_team(
        root,
        [
            {"id": "t13", "kind": "implementation"},
            {"id": "t16", "kind": "review", "assignee": "architect", "reviewedTaskId": "t13"},
        ],
    )
    assert run(root, "review", "--task", "t16") == 3


def test_review_handles_integer_attempt_field(tmp_path):
    # Regression: team.json stores ``attempt`` as the attempt number (int).
    root = make_root(tmp_path)
    make_team(
        root,
        [
            {
                "id": "t13",
                "kind": "implementation",
                "assignee": "developer",
                "status": "completed",
                "attempt": 2,
            },
            {"id": "t15", "kind": "review", "assignee": "developer", "reviewedTaskId": "t13"},
        ],
    )
    assert run(root, "review", "--task", "t15") == 2


def test_review_cannot_verify_without_owner(tmp_path):
    root = make_root(tmp_path)
    make_team(
        root,
        [
            {"id": "t1", "kind": "implementation", "status": "completed"},
            {"id": "t2", "kind": "review", "assignee": "architect", "reviewedTaskId": "t1"},
        ],
    )
    assert run(root, "review", "--task", "t2") == 3


def test_delivery_detects_stale_verdict(tmp_path):
    root = make_root(tmp_path)
    target = root / "artifact.md"
    target.write_text("current bytes\n", encoding="utf-8")
    make_team(
        root,
        [
            {
                "id": "t6",
                "kind": "review",
                "assignee": "architect",
                "reviewedTaskId": "t1",
                "status": "completed",
                "verdict": "pass",
                "reviewedArtifacts": [{"path": "artifact.md", "sha256": "0" * 64}],
            }
        ],
    )
    assert run(root, "delivery") == 2


def test_delivery_passes_when_bytes_match(tmp_path):
    root = make_root(tmp_path)
    target = root / "artifact.md"
    target.write_text("current bytes\n", encoding="utf-8")
    digest = check.sha256(target)
    make_team(
        root,
        [
            {
                "id": "t6",
                "kind": "review",
                "assignee": "architect",
                "reviewedTaskId": "t1",
                "status": "completed",
                "verdict": "pass",
                "reviewedArtifacts": [{"path": "artifact.md", "sha256": digest}],
            }
        ],
    )
    assert run(root, "delivery") == 0