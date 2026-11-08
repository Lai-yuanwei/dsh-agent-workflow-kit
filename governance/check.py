#!/usr/bin/env python3
"""Program-level governance checks for the BMAD + AgentTeams workflow.

The AgentTeams plugin (0.1.29) validates *declared* changed paths, but it has no
reviewer-vs-implementer identity check and no role based write policy.  This
checker closes those two gaps at the only point that is actually enforced by the
runtime: a quality task's ``verify`` command.  A member that cannot make
``verify`` exit 0 cannot complete the task with a passing verdict.

Subcommands
  baseline --task ID       snapshot the working tree before a write task runs
  scope    --task ID       compare the tree with the baseline and apply the
                           role write policy of the task assignee
  review   --task ID       verify reviewer independence (reviewer != implementer)
  delivery --team NAME     verify recorded verdicts still match the bytes on disk

Exit codes: 0 = pass, 2 = violation, 3 = cannot verify.

Nothing here modifies team.json, task state, verdicts or the plugin.  All state
is written under ``.governance/`` inside the project.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = Path(".governance")
BASELINE_DIR = STATE_DIR / "baselines"
IGNORE_DIRS = {
    ".agent-teams",
    ".governance",
    ".memsearch",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
}
IGNORE_SUFFIXES = (".pyc", ".pyo")
ROLE_ALIASES = {
    "需求分析师": "analyst",
    "软件架构师": "architect",
    "开发工程师": "developer",
    "测试审查工程师": "qa",
    "协调者": "captain",
}
WRITE_KINDS = {"implementation", "repair", "integration"}


# --------------------------------------------------------------------------- io


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ------------------------------------------------------------------- snapshots


def snapshot(root: Path) -> dict:
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORE_DIRS)
        for name in sorted(filenames):
            if name.endswith(IGNORE_SUFFIXES):
                continue
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if rel.split("/", 1)[0] in IGNORE_DIRS:
                continue
            try:
                files[rel] = sha256(path)
            except OSError:
                continue
    return files


def diff(before: dict, after: dict) -> dict:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(name for name in set(before) & set(after) if before[name] != after[name])
    return {"added": added, "modified": modified, "removed": removed}


# ------------------------------------------------------------------- the team


def team_dir(root: Path, name: str | None) -> Path:
    base = root / ".agent-teams"
    if name:
        candidate = base / name
        if (candidate / "team.json").is_file():
            return candidate
        raise SystemExit(f"cannot verify: no team JSON at {candidate / 'team.json'}")
    candidates = sorted(path.parent for path in base.glob("*/team.json"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise SystemExit("cannot verify: no .agent-teams/*/team.json in this project")
    raise SystemExit(
        "cannot verify: several teams present, pass --team: "
        + ", ".join(path.name for path in candidates)
    )


def load_team(root: Path, name: str | None) -> tuple[Path, dict]:
    directory = team_dir(root, name)
    return directory, load_json(directory / "team.json")


def find_task(team: dict, task_id: str) -> dict:
    for task in team.get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise SystemExit(f"cannot verify: task {task_id} not found in team state")


def role_of(team: dict, task: dict, roles: dict) -> str:
    assignee = str(task.get("assignee") or "")
    if assignee in roles:
        return assignee
    member = next((m for m in team.get("members", []) if m.get("name") == assignee), None)
    if member is not None:
        label = str(member.get("role") or "")
        if label in roles:
            return label
        if label in ROLE_ALIASES:
            return ROLE_ALIASES[label]
    if assignee in ROLE_ALIASES:
        return ROLE_ALIASES[assignee]
    raise SystemExit(
        f"cannot verify: cannot map assignee {assignee!r} to a role policy "
        f"(known roles: {', '.join(sorted(roles))})"
    )


# ------------------------------------------------------------------- policies


def load_roles(root: Path) -> dict:
    payload = load_json(root / "tools" / "governance" / "roles.json")
    return payload["roles"]


def pattern_match(patterns, path: str) -> str | None:
    for pattern in patterns:
        if fnmatch.fnmatchcase(path, pattern):
            return pattern
        # Let "**/NAME" also match NAME at the repository root.
        if pattern.startswith("**/") and fnmatch.fnmatchcase(path, "*" + pattern[2:]):
            return pattern
    return None


def classify(policy: dict, path: str) -> tuple[str, str | None]:
    denied = pattern_match(policy.get("deny", []), path)
    if denied:
        return "denied", denied
    allowed = pattern_match(policy.get("allow", []), path)
    if allowed:
        return "allowed", allowed
    return "not_allowed", None


# ------------------------------------------------------------- command bodies


def cmd_baseline(args, root: Path) -> int:
    team_path, team = load_team(root, args.team)
    task = find_task(team, args.task)
    files = snapshot(root)
    payload = {
        "label": args.task,
        "created": datetime.now(timezone.utc).isoformat(),
        "team": team_path.name,
        "task": args.task,
        "assignee": task.get("assignee"),
        "kind": task.get("kind", "work"),
        "fileCount": len(files),
        "files": files,
    }
    target = root / BASELINE_DIR / f"{args.task}.json"
    write_json(target, payload)
    print(f"baseline {args.task}: {len(files)} files -> {target.relative_to(root).as_posix()}")
    return 0


def cmd_scope(args, root: Path) -> int:
    team_path, team = load_team(root, args.team)
    task = find_task(team, args.task)
    roles = load_roles(root)
    role = role_of(team, task, roles)
    policy = roles[role]

    label = args.baseline or args.task
    base_path = root / BASELINE_DIR / f"{label}.json"
    if not base_path.is_file() and args.baseline is None:
        # A repair task inherits the verify command of its source task, so fall
        # back to the nearest ancestor baseline that exists.
        for candidate in (task.get("sourceTaskId"), ):
            if candidate:
                alternate = root / BASELINE_DIR / f"{candidate}.json"
                if alternate.is_file():
                    base_path, label = alternate, candidate
                    break
    if not base_path.is_file():
        print(f"scope: CANNOT VERIFY - no baseline {label}.json; run baseline first")
        return 3

    before = load_json(base_path)
    changes = diff(before["files"], snapshot(root))
    violations = []
    for category in ("added", "modified", "removed"):
        for path in changes[category]:
            verdict, pattern = classify(policy, path)
            if verdict != "allowed":
                violations.append(
                    {"category": category, "path": path, "verdict": verdict, "rule": pattern}
                )

    result = {
        "task": args.task,
        "team": team_path.name,
        "role": role,
        "baseline": str(base_path.relative_to(root).as_posix()),
        "changes": changes,
        "allowedCount": sum(
            len(changes[key]) for key in changes
        ) - len(violations),
        "violations": violations,
    }
    print(f"scope: task={args.task} role={role} baseline={label}")
    for category in ("added", "modified", "removed"):
        for path in changes[category]:
            print(f"  {category:8s} {path}")
    if violations:
        for item in violations:
            rule = item["rule"] or "no allow rule"
            print(f"VIOLATION {item['verdict']}: {item['path']} ({rule})")
        print(f"scope: FAIL ({len(violations)} violation(s))")
        if args.json:
            write_json(Path(args.json), result)
        return 2
    print("scope: PASS")
    if args.json:
        write_json(Path(args.json), result)
    return 0


def implementers_of(team: dict, task: dict) -> tuple[list[dict], list[str]]:
    by_id = {item.get("id"): item for item in team.get("tasks", [])}
    lineage = [task]
    seen = {task.get("id")}
    stack = [task]
    while stack:
        current = stack.pop()
        parents = []
        if current.get("sourceTaskId"):
            parents.append(current["sourceTaskId"])
        for dependency in current.get("dependencies") or []:
            upstream = by_id.get(dependency)
            if upstream is not None and upstream.get("kind") in WRITE_KINDS:
                parents.append(dependency)
        for parent_id in parents:
            if parent_id in seen:
                continue
            parent = by_id.get(parent_id)
            if parent is None:
                continue
            seen.add(parent_id)
            lineage.append(parent)
            stack.append(parent)

    implementers = []
    unknown = []
    for item in lineage:
        if item.get("kind") not in WRITE_KINDS:
            continue
        owner = item.get("assignee")
        if not owner:
            unknown.append(str(item.get("id")))
            continue
        implementers.append({"task": item.get("id"), "kind": item.get("kind"), "assignee": owner})
        # Attempt-level ownership, when the runtime recorded it.  ``attempt`` is
        # the attempt *number* (an int) in current state files, so only inspect
        # it when it really is an object/list of objects.
        records = []
        attempt = item.get("attempt")
        if isinstance(attempt, dict):
            records.append(attempt)
        elif isinstance(attempt, list):
            records.extend(entry for entry in attempt if isinstance(entry, dict))
        for record in records:
            for key in ("assignee", "owner", "member"):
                value = record.get(key)
                if value and value != owner:
                    implementers.append(
                        {"task": item.get("id"), "kind": item.get("kind"), "assignee": value}
                    )
    return implementers, unknown


def cmd_review(args, root: Path) -> int:
    team_path, team = load_team(root, args.team)
    task = find_task(team, args.task)
    kind = task.get("kind", "work")
    if kind != "review":
        print(f"review: CANNOT VERIFY - task {args.task} has kind {kind}, not review")
        return 3
    reviewed_id = task.get("reviewedTaskId")
    if not reviewed_id:
        print("review: CANNOT VERIFY - review task carries no reviewedTaskId")
        return 3
    reviewed = find_task(team, reviewed_id)

    reviewer = task.get("assignee")
    if not reviewer:
        print(
            f"review: CANNOT VERIFY - review task {args.task} has no assignee; "
            "independence cannot be proven"
        )
        return 3
    implementers, unknown = implementers_of(team, reviewed)
    if not implementers:
        print(
            f"review: CANNOT VERIFY - no implementation/repair owner recorded in the "
            f"lineage of {reviewed_id}; independence cannot be proven"
        )
        return 3
    if unknown:
        print(
            "review: CANNOT VERIFY - lineage tasks carry no owner: "
            + ", ".join(unknown)
            + "; independence cannot be proven"
        )
        return 3

    owners = {item["assignee"] for item in implementers}
    result = {
        "task": args.task,
        "team": team_path.name,
        "reviewer": reviewer,
        "reviewedTaskId": reviewed_id,
        "lineage": implementers,
        "unknownOwners": unknown,
        "independent": reviewer not in owners,
    }
    print(f"review: task={args.task} reviewer={reviewer} reviewed={reviewed_id}")
    for item in implementers:
        print(f"  lineage {item['task']} ({item['kind']}) executed by {item['assignee']}")
    if unknown:
        print(f"  unresolved lineage owners: {', '.join(unknown)}")
    if reviewer in owners:
        same = sorted({item["task"] for item in implementers if item["assignee"] == reviewer})
        print(
            f"review: FAIL - reviewer {reviewer} executed the reviewed work "
            f"({', '.join(same)}); this is not an independent review"
        )
        if args.json:
            write_json(Path(args.json), result)
        return 2
    print(f"review: PASS - {reviewer} is independent of every implementation/repair in the lineage")
    if args.json:
        write_json(Path(args.json), result)
    return 0


def cmd_delivery(args, root: Path) -> int:
    team_path, team = load_team(root, args.team)
    roles = load_roles(root)
    problems = []
    checked = 0

    for task in team.get("tasks", []):
        artifacts = task.get("reviewedArtifacts") or []
        for artifact in artifacts:
            checked += 1
            path = artifact.get("path") or ""
            recorded = artifact.get("sha256") or ""
            target = root / path
            if not path:
                problems.append({"task": task.get("id"), "path": path, "problem": "empty path"})
                continue
            if not target.is_file():
                problems.append(
                    {"task": task.get("id"), "path": path, "problem": "artifact missing on disk"}
                )
                continue
            actual = sha256(target)
            if recorded and actual != recorded:
                problems.append(
                    {
                        "task": task.get("id"),
                        "path": path,
                        "problem": "verdict bytes are stale",
                        "recorded": recorded,
                        "actual": actual,
                    }
                )

        for path in task.get("changedPaths") or []:
            declared = root / path
            if not declared.exists():
                problems.append(
                    {"task": task.get("id"), "path": path, "problem": "changedPath missing on disk"}
                )

        if task.get("kind") in WRITE_KINDS and task.get("changedPaths"):
            try:
                role = role_of(team, task, roles)
            except SystemExit:
                role = None
            if role:
                for path in task["changedPaths"]:
                    verdict, pattern = classify(roles[role], path)
                    if verdict != "allowed":
                        problems.append(
                            {
                                "task": task.get("id"),
                                "path": path,
                                "problem": f"changedPath outside role policy ({verdict})",
                                "rule": pattern,
                            }
                        )

    print(f"delivery: team={team_path.name} artifacts_checked={checked} problems={len(problems)}")
    for item in problems:
        print(f"  {item['task']}: {item['path']} -> {item['problem']}")
    if problems:
        print("delivery: BLOCKED")
        return 2
    print("delivery: PASS")
    return 0


# ---------------------------------------------------------------------- entry


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=str(ROOT), help="project root (default: repository root)")
    parser.add_argument("--team", default=None, help="team name under .agent-teams/")
    parser.add_argument("--json", default=None, help="write machine readable result to this path")
    sub = parser.add_subparsers(dest="command", required=True)

    baseline = sub.add_parser("baseline", help="snapshot the tree before a write task")
    baseline.add_argument("--task", required=True)
    baseline.set_defaults(func=cmd_baseline)

    scope = sub.add_parser("scope", help="check the tree diff against the role policy")
    scope.add_argument("--task", required=True)
    scope.add_argument("--baseline", default=None, help="baseline label (default: task id)")
    scope.set_defaults(func=cmd_scope)

    review = sub.add_parser("review", help="check reviewer independence")
    review.add_argument("--task", required=True)
    review.set_defaults(func=cmd_review)

    delivery = sub.add_parser("delivery", help="check verdict freshness before delivery")
    delivery.set_defaults(func=cmd_delivery)

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"cannot verify: root {root} is not a directory")
        return 3
    return args.func(args, root)


if __name__ == "__main__":
    sys.exit(main())