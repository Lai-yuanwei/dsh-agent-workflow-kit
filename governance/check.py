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
  delivery                audit recorded evidence (not delivery approval)

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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = Path(".governance")
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


class CannotVerify(ValueError):
    """Required evidence is missing or structurally invalid."""


# --------------------------------------------------------------------------- io


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def state_path(root: Path, category: str, team: str, task: str) -> Path:
    # Opaque ids may contain characters that are not safe Windows path names.
    key = lambda value: hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return root / STATE_DIR / category / key(team) / f"{key(task)}.json"


def task_identity(team: str, task: dict) -> dict:
    return {"team": team, "task": task.get("id"), "assignee": task.get("assignee"),
            "kind": task.get("kind", "work"), "attempt": task.get("attempt")}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ------------------------------------------------------------------- snapshots


def snapshot(root: Path) -> dict:
    files = {}
    def unreadable(error):
        raise error

    for dirpath, dirnames, filenames in os.walk(root, onerror=unreadable):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORE_DIRS)
        for name in sorted(filenames):
            if name.endswith(IGNORE_SUFFIXES):
                continue
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if rel.split("/", 1)[0] in IGNORE_DIRS:
                continue
            files[rel] = sha256(path)
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
        raise CannotVerify(f"no team JSON at {candidate / 'team.json'}")
    candidates = sorted(path.parent for path in base.glob("*/team.json"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise CannotVerify("no .agent-teams/*/team.json in this project")
    raise CannotVerify(
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
    raise CannotVerify(f"task {task_id} not found in team state")


def role_of(team: dict, task: dict, roles: dict) -> str:
    assignee = str(task.get("assignee") or "")
    if assignee in roles:
        return assignee
    member = next((m for m in team.get("members", []) if m.get("name") == assignee), None)
    if member is not None:
        label = str(member.get("role") or "")
        if label in roles:
            return label
        if label in ROLE_ALIASES and ROLE_ALIASES[label] in roles:
            return ROLE_ALIASES[label]
    if assignee in ROLE_ALIASES and ROLE_ALIASES[assignee] in roles:
        return ROLE_ALIASES[assignee]
    raise CannotVerify(
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
    payload.update(task_identity(team_path.name, task))
    target = state_path(root, "baselines", team_path.name, args.task)
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
    base_path = state_path(root, "baselines", team_path.name, label)
    if not base_path.is_file():
        print(f"scope: CANNOT VERIFY - no baseline {label}.json; run baseline first")
        return 3

    before = load_json(base_path)
    if any(before.get(key) != value for key, value in task_identity(team_path.name, task).items()):
        raise CannotVerify("baseline belongs to a different team, task, owner or attempt")
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
    # Receipt records actual removals, not merely declared changedPaths.
    receipt = dict(result, identity=task_identity(team_path.name, task),
                   baselineSha256=sha256(base_path), policy=policy)
    write_json(state_path(root, "scopes", team_path.name, args.task), receipt)
    if args.json:
        write_json(Path(args.json), result)
    return 0


def implementers_of(team: dict, task: dict) -> tuple[list[dict], list[str]]:
    by_id = {item.get("id"): item for item in team.get("tasks", [])}
    if not all(by_id) or len(by_id) != len(team.get("tasks", [])):
        raise CannotVerify("lineage requires unique, nonempty task ids")
    lineage = []
    visited, visiting = set(), set()

    def visit(task_id):
        if task_id in visiting:
            raise CannotVerify(f"cycle in task lineage at {task_id}")
        if task_id in visited:
            return
        current = by_id.get(task_id)
        if current is None:
            raise CannotVerify(f"missing lineage task {task_id}")
        visiting.add(task_id)
        lineage.append(current)
        parents = list(current.get("dependencies") or [])
        for key in ("sourceTaskId", "reviewedTaskId"):
            if current.get(key):
                parents.append(current[key])
        for parent_id in parents:
            visit(parent_id)
        visiting.remove(task_id)
        visited.add(task_id)

    visit(task.get("id"))

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


def verified_removals(root: Path, team_name: str, task: dict, roles: dict, team: dict) -> set[str]:
    """A successful scope receipt is required to distinguish deletion from loss."""
    receipt_path = state_path(root, "scopes", team_name, task.get("id"))
    if task.get("status") != "completed" or not receipt_path.is_file():
        return set()
    receipt = load_json(receipt_path)
    baseline = state_path(root, "baselines", team_name, task.get("id"))
    policy = roles[role_of(team, task, roles)]
    if (receipt.get("identity") != task_identity(team_name, task)
            or receipt.get("violations") != [] or receipt.get("policy") != policy
            or not baseline.is_file() or receipt.get("baselineSha256") != sha256(baseline)):
        return set()
    before = load_json(baseline)
    return {path for path in receipt.get("changes", {}).get("removed", [])
            if path in before.get("files", {}) and path in (task.get("changedPaths") or [])
            and classify(policy, path)[0] == "allowed" and not (root / path).exists()}


def superseded_reviews(team: dict, pairs: list[str], removals: dict) -> dict[str, str]:
    """Validate explicit replacement edges without changing runtime history."""
    replacements = {}
    for pair in pairs:
        old_id, separator, new_id = pair.partition("=")
        if not separator or not old_id or not new_id or old_id == new_id or old_id in replacements:
            raise CannotVerify(f"invalid or duplicate supersession: {pair}")
        replacements[old_id] = new_id
    # Each old review must point straight to a current terminal review. This
    # also rejects cycles; multi-round history can map every old id to the final id.
    if set(replacements) & set(replacements.values()):
        raise CannotVerify("supersession chains/cycles are not allowed; name the terminal review")
    for old_id, new_id in replacements.items():
        old, new = find_task(team, old_id), find_task(team, new_id)
        if old.get("kind") != "review" or new.get("kind") != "review":
            raise CannotVerify("only code review records can be superseded")
        if not old.get("assignee") or old.get("assignee") != new.get("assignee"):
            raise CannotVerify("replacement must preserve the reviewer identity")
        if new.get("status") != "completed" or new.get("verdict") != "pass":
            raise CannotVerify(f"replacement review {new_id} has not passed")
        old_target = find_task(team, old.get("reviewedTaskId"))
        target = find_task(team, new.get("reviewedTaskId"))
        owners, unknown = implementers_of(team, target)
        if not owners or unknown or new["assignee"] in {item["assignee"] for item in owners}:
            raise CannotVerify(f"replacement review {new_id} is not provably independent")
        # Follow repair-source links, not arbitrary scheduling dependencies.
        current, seen, repair_ids = target, set(), []
        while current.get("id") not in {old_id, old_target.get("id")}:
            current_id = current.get("id")
            if current_id in seen:
                raise CannotVerify("cycle in replacement lineage")
            seen.add(current_id)
            if current.get("kind") == "review":
                current = find_task(team, current.get("reviewedTaskId"))
            elif current.get("kind") == "repair" and current.get("status") == "completed":
                repair_ids.append(current_id)
                current = find_task(team, current.get("sourceTaskId"))
            else:
                raise CannotVerify(f"{new_id} is not a completed repair of {old_id}")
        if not repair_ids:
            raise CannotVerify("replacement needs a completed repair, not a parallel review")
        required = {item.get("path") for item in old.get("reviewedArtifacts") or []}
        required.update(old_target.get("changedPaths") or [])
        for repair_id in repair_ids:
            required.update(find_task(team, repair_id).get("changedPaths") or [])
        if not required or None in required or "" in required:
            raise CannotVerify(f"cannot establish the scope of {old_id}")
        covered = {item.get("path") for item in new.get("reviewedArtifacts") or []}
        for repair_id in repair_ids:
            covered.update(removals.get(repair_id, set()))
        if not required <= covered:
            raise CannotVerify(f"{new_id} does not cover all paths from {old_id}")
    return replacements


def cmd_delivery(args, root: Path) -> int:
    team_path, team = load_team(root, args.team)
    roles = load_roles(root)
    problems = []
    unknown = []
    checked = 0
    removals = {}
    for task in team.get("tasks", []):
        if task.get("kind") in WRITE_KINDS:
            removals[task.get("id")] = verified_removals(root, team_path.name, task, roles, team)
    deleted = set().union(*removals.values()) if removals else set()
    replacements = superseded_reviews(team, args.supersede, removals)

    for task in team.get("tasks", []):
        replaced = task.get("id") in replacements
        if replaced:
            print(f"delivery: historical review {task['id']} superseded by {replacements[task['id']]}")
        artifacts = [] if replaced else task.get("reviewedArtifacts") or []
        if not replaced and (artifacts or task.get("kind") in {"review", "requirements"}):
            for field, expected in (("status", "completed"), ("verdict", "pass")):
                value = task.get(field)
                if not value:
                    unknown.append(f"{task.get('id')}: missing {field}")
                elif value != expected:
                    problems.append({"task": task.get("id"), "path": "",
                                     "problem": f"{field} is {value}, expected {expected}"})
            if not artifacts:
                unknown.append(f"{task.get('id')}: no reviewed artifacts")
        for artifact in artifacts:
            checked += 1
            path = artifact.get("path") or ""
            recorded = artifact.get("sha256") or ""
            target = root / path
            if not path:
                unknown.append(f"{task.get('id')}: empty artifact path")
                continue
            if not isinstance(recorded, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", recorded):
                unknown.append(f"{task.get('id')}: {path}: missing or invalid sha256")
                continue
            if not target.is_file():
                problems.append(
                    {"task": task.get("id"), "path": path, "problem": "artifact missing on disk"}
                )
                continue
            actual = sha256(target)
            if actual != recorded.lower():
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
            if not declared.exists() and path not in deleted:
                problems.append(
                    {"task": task.get("id"), "path": path, "problem": "changedPath missing on disk"}
                )

        if task.get("kind") in WRITE_KINDS:
            try:
                role = role_of(team, task, roles)
            except CannotVerify as exc:
                unknown.append(f"{task.get('id')}: {exc}")
                role = None
            if role:
                for path in task.get("changedPaths") or []:
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

    if not checked:
        unknown.append("no recorded artifacts to audit")
    print(f"delivery evidence audit: team={team_path.name} artifacts_checked={checked} problems={len(problems)}")
    for item in problems:
        print(f"  {item['task']}: {item['path']} -> {item['problem']}")
    for message in unknown:
        print(f"  CANNOT VERIFY: {message}")
    if problems:
        print("delivery: BLOCKED")
        return 2
    if unknown:
        print("delivery: CANNOT VERIFY")
        return 3
    print("delivery: EVIDENCE CONSISTENT - not delivery approval; scope, review and K4 remain separate")
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

    delivery = sub.add_parser("delivery", help="audit recorded evidence; does not approve delivery")
    delivery.add_argument("--supersede", action="append", default=[], metavar="OLD=NEW",
                          help="explicit historical review replacement (repeatable; validated)")
    delivery.set_defaults(func=cmd_delivery)

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"cannot verify: root {root} is not a directory")
        return 3
    try:
        return args.func(args, root)
    except (CannotVerify, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"{args.command}: CANNOT VERIFY - {exc}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
