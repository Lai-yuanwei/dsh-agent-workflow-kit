"""Tests for governance/check.py.

The tests exercise the checker against temporary project trees. They prove the
logic; the end-to-end wiring is proved by real AgentTeams tasks whose ``verify``
runs the command. Install the checker as ``./tools/governance/`` in a project
before using these paths.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

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


def delivery_record(root):
    target = root / "artifact.md"
    target.write_text("reviewed bytes\n", encoding="utf-8")
    return {
        "id": "r1", "kind": "review", "status": "completed", "verdict": "pass",
        "reviewedArtifacts": [{"path": "artifact.md", "sha256": check.sha256(target)}],
    }


@pytest.mark.parametrize("digest", [None, "", "bad", 123])
def test_delivery_requires_valid_hash(tmp_path, digest):
    root = make_root(tmp_path)
    record = delivery_record(root)
    record["reviewedArtifacts"][0]["sha256"] = digest
    make_team(root, [record])
    assert run(root, "delivery") == 3


def test_delivery_requires_role_even_without_changed_paths(tmp_path):
    root = make_root(tmp_path)
    make_team(root, [delivery_record(root), {"id": "w1", "kind": "implementation", "assignee": "unknown"}])
    assert run(root, "delivery") == 3


@pytest.mark.parametrize("tasks", [[], [{"id": "r1", "kind": "review", "status": "completed", "verdict": "pass"}]])
def test_delivery_requires_artifact_evidence(tmp_path, tasks):
    root = make_root(tmp_path)
    make_team(root, tasks)
    assert run(root, "delivery") == 3


@pytest.mark.parametrize("verdict", ["reject", "needs_revision"])
def test_delivery_blocks_rejected_review(tmp_path, verdict):
    root = make_root(tmp_path)
    record = delivery_record(root)
    record["verdict"] = verdict
    make_team(root, [record])
    assert run(root, "delivery") == 2


@pytest.mark.parametrize("field,value,expected", [("verdict", None, 3), ("status", None, 3), ("status", "running", 2)])
def test_delivery_requires_completed_passing_record(tmp_path, field, value, expected):
    root = make_root(tmp_path)
    record = delivery_record(root)
    record[field] = value
    make_team(root, [record])
    assert run(root, "delivery") == expected


@pytest.mark.parametrize("links", [{"sourceTaskId": "missing"}, {"dependencies": ["missing"]}, {"sourceTaskId": "w1"}])
def test_review_requires_complete_acyclic_lineage(tmp_path, links):
    root = make_root(tmp_path)
    make_team(root, [
        {"id": "w1", "kind": "repair", "assignee": "developer", **links},
        {"id": "r1", "kind": "review", "assignee": "qa", "reviewedTaskId": "w1"},
    ])
    assert run(root, "review", "--task", "r1") == 3


def test_review_follows_intermediate_review_to_original_owner(tmp_path):
    root = make_root(tmp_path)
    make_team(root, [
        {"id": "w1", "kind": "implementation", "assignee": "developer"},
        {"id": "r1", "kind": "review", "assignee": "qa", "reviewedTaskId": "w1"},
        {"id": "w2", "kind": "repair", "assignee": "architect", "sourceTaskId": "r1"},
        {"id": "r2", "kind": "review", "assignee": "developer", "reviewedTaskId": "w2"},
    ])
    assert run(root, "review", "--task", "r2") == 2


def test_missing_team_is_cannot_verify(tmp_path):
    assert run(make_root(tmp_path), "delivery") == 3


def test_analyst_can_record_discovery_only(tmp_path):
    policy = check.load_roles(make_root(tmp_path))["analyst"]
    assert check.classify(policy, "docs/team/DISCOVERY.md")[0] == "allowed"
    for path in ["docs/team/HANDOFF.md", "docs/team/START-HERE.md", "docs/team/other.md"]:
        assert check.classify(policy, path)[0] != "allowed"


def test_offline_repair_and_reaudit_workflow(tmp_path, capsys):
    """Synthetic state exercises the checker lifecycle, not the DSH runtime."""
    root = make_root(tmp_path)
    write = {"id": "w1", "kind": "implementation", "assignee": "developer"}
    make_team(root, [write])
    assert run(root, "baseline", "--task", "w1") == 0
    target = root / "src" / "app.py"
    target.parent.mkdir()
    target.write_text("value = 1\n", encoding="utf-8")
    assert run(root, "scope", "--task", "w1") == 0

    review = {"id": "r1", "kind": "review", "assignee": "developer", "reviewedTaskId": "w1"}
    make_team(root, [write, review])
    assert run(root, "review", "--task", "r1") == 2
    review.update(assignee="qa", status="completed", verdict="pass",
                  reviewedArtifacts=[{"path": "src/app.py", "sha256": check.sha256(target)}])
    write.update(status="completed", changedPaths=["src/app.py"])
    make_team(root, [write, review])
    assert run(root, "review", "--task", "r1") == 0
    assert run(root, "delivery") == 0
    assert "not delivery approval" in capsys.readouterr().out
    repair = {"id": "w2", "kind": "repair", "assignee": "developer", "sourceTaskId": "r1"}
    make_team(root, [write, review, repair])
    assert run(root, "baseline", "--task", "w2") == 0
    target.write_text("value = 2\n", encoding="utf-8")
    assert run(root, "scope", "--task", "w2") == 0
    assert run(root, "delivery") == 2
    new_review = dict(review, id="r2", reviewedTaskId="w2",
                      reviewedArtifacts=[{"path": "src/app.py", "sha256": check.sha256(target)}])
    repair.update(status="completed", changedPaths=["src/app.py"])
    make_team(root, [write, review, repair, new_review])
    assert run(root, "review", "--task", "r2") == 0
    assert run(root, "delivery", "--supersede", "r1=r2") == 0


def repair_history(root):
    target = root / "src/app.py"
    target.parent.mkdir()
    target.write_text("fixed\n", encoding="utf-8")
    write = {"id": "w1", "kind": "implementation", "assignee": "developer",
             "status": "completed", "changedPaths": ["src/app.py"]}
    old = {"id": "r1", "kind": "review", "assignee": "qa", "reviewedTaskId": "w1",
           "status": "failed", "verdict": "reject",
           "reviewedArtifacts": [{"path": "src/app.py", "sha256": "0" * 64}]}
    repair = {"id": "w2", "kind": "repair", "assignee": "developer", "sourceTaskId": "r1",
              "status": "completed", "changedPaths": ["src/app.py"]}
    new = {"id": "r2", "kind": "review", "assignee": "qa", "reviewedTaskId": "w2",
           "status": "completed", "verdict": "pass",
           "reviewedArtifacts": [{"path": "src/app.py", "sha256": check.sha256(target)}]}
    return [write, old, repair, new]


def test_delivery_supersedes_rejection_without_rewriting_history(tmp_path):
    root = make_root(tmp_path)
    tasks = repair_history(root)
    make_team(root, tasks)
    state = root / ".agent-teams/dev-team-default/team.json"
    original = state.read_bytes()
    assert run(root, "delivery") == 2
    assert run(root, "delivery", "--supersede", "r1=r2") == 0
    assert state.read_bytes() == original


@pytest.mark.parametrize("fault", ["unrelated", "self_review", "stale", "partial", "failed", "missing", "wrong_reviewer", "repair_extra"])
def test_invalid_successor_cannot_hide_rejection(tmp_path, fault):
    root = make_root(tmp_path)
    tasks = repair_history(root)
    if fault == "unrelated":
        tasks[2].pop("sourceTaskId")
    elif fault == "self_review":
        tasks[3]["assignee"] = "developer"
    elif fault == "stale":
        tasks[3]["reviewedArtifacts"][0]["sha256"] = "f" * 64
    elif fault == "partial":
        tasks[1]["reviewedArtifacts"].append({"path": "src/other.py", "sha256": "0" * 64})
    elif fault == "failed":
        tasks[3]["verdict"] = "reject"
    elif fault == "missing":
        tasks.pop()
    elif fault == "repair_extra":
        (root / "src/extra.py").write_text("not reviewed", encoding="utf-8")
        tasks[2]["changedPaths"].append("src/extra.py")
    else:
        tasks[3]["assignee"] = "architect"
    make_team(root, tasks)
    assert run(root, "delivery", "--supersede", "r1=r2") in (2, 3)


def test_delivery_allows_proven_deletion_but_not_unrecorded_loss(tmp_path):
    root = make_root(tmp_path)
    record = delivery_record(root)
    task = {"id": "w1", "kind": "implementation", "assignee": "developer"}
    target = root / "src/obsolete.py"
    target.parent.mkdir()
    target.write_text("obsolete", encoding="utf-8")
    make_team(root, [task, record])
    assert run(root, "baseline", "--task", "w1") == 0
    target.unlink()
    task.update(status="completed", changedPaths=["src/obsolete.py"])
    make_team(root, [task, record])
    assert run(root, "delivery") != 0
    assert run(root, "scope", "--task", "w1") == 0
    assert run(root, "delivery") == 0
    task["attempt"] = 2
    make_team(root, [task, record])
    assert run(root, "delivery") != 0  # receipt from another attempt is stale


def test_baselines_are_isolated_by_team(tmp_path):
    root = make_root(tmp_path)
    task = {"id": "w1", "kind": "implementation", "assignee": "developer"}
    make_team(root, [task])
    assert run(root, "--team", "dev-team-default", "baseline", "--task", "w1") == 0
    other = root / ".agent-teams/other"
    other.mkdir()
    (other / "team.json").write_text(json.dumps({"tasks": [task]}), encoding="utf-8")
    (root / "SPEC.md").write_text("protected", encoding="utf-8")
    assert run(root, "--team", "other", "baseline", "--task", "w1") == 0
    assert run(root, "--team", "dev-team-default", "scope", "--task", "w1") == 2


def test_deleted_reviewed_artifact_closes_with_history_and_fresh_process(tmp_path):
    root = make_root(tmp_path)
    tasks = repair_history(root)
    tasks[2].pop("status")
    make_team(root, tasks)
    assert run(root, "baseline", "--task", "w2") == 0
    (root / "src/app.py").unlink()
    report = root / "src/replacement.py"
    report.write_text("replacement\n", encoding="utf-8")
    assert run(root, "scope", "--task", "w2") == 0
    tasks[2].update(status="completed", changedPaths=["src/app.py", "src/replacement.py"])
    tasks[3]["reviewedArtifacts"] = [{"path": "src/replacement.py", "sha256": check.sha256(report)}]
    make_team(root, tasks)
    result = subprocess.run([sys.executable, "-B", str(root / "tools/governance/check.py"),
                             "delivery", "--supersede", "r1=r2"], cwd=root,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "EVIDENCE CONSISTENT" in result.stdout
    assert "historical review r1 superseded by r2" in result.stdout


def test_unrelated_rejected_review_still_blocks(tmp_path):
    root = make_root(tmp_path)
    tasks = repair_history(root)
    tasks.append(dict(tasks[1], id="unresolved"))
    make_team(root, tasks)
    assert run(root, "delivery", "--supersede", "r1=r2") == 2


@pytest.mark.parametrize("pairs", [["r1=r1"], ["r1=r2", "r2=r1"], ["r1=r2", "r1=r2"], ["r1"]])
def test_invalid_supersession_mapping_fails_closed(tmp_path, pairs):
    root = make_root(tmp_path)
    make_team(root, repair_history(root))
    argv = [word for pair in pairs for word in ("--supersede", pair)]
    assert run(root, "delivery", *argv) == 3


def test_two_repair_rounds_preserve_all_history(tmp_path):
    root = make_root(tmp_path)
    tasks = repair_history(root)
    tasks[3].update(status="failed", verdict="needs_revision")
    tasks.extend([
        dict(tasks[2], id="w3", sourceTaskId="r2"),
        dict(tasks[3], id="r3", reviewedTaskId="w3", status="completed", verdict="pass"),
    ])
    make_team(root, tasks)
    assert run(root, "delivery", "--supersede", "r1=r3", "--supersede", "r2=r3") == 0


def test_baseline_change_invalidates_deletion_receipt(tmp_path):
    root = make_root(tmp_path)
    record = delivery_record(root)
    task = {"id": "w1", "kind": "implementation", "assignee": "developer",
            "status": "completed", "changedPaths": ["src/obsolete.py"]}
    target = root / "src/obsolete.py"
    target.parent.mkdir()
    target.write_text("obsolete", encoding="utf-8")
    make_team(root, [task, record])
    assert run(root, "baseline", "--task", "w1") == 0
    target.unlink()
    assert run(root, "scope", "--task", "w1") == 0
    assert run(root, "delivery") == 0
    assert run(root, "baseline", "--task", "w1") == 0
    assert run(root, "delivery") != 0


def test_unreadable_snapshot_cannot_create_passing_baseline(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    make_team(root, [{"id": "w1", "kind": "implementation", "assignee": "developer"}])
    def unreadable(path):
        raise PermissionError("fixture cannot read file")
    monkeypatch.setattr(check, "sha256", unreadable)
    assert run(root, "baseline", "--task", "w1") == 3
