# START-HERE — {{PROJECT_NAME}} session bootstrap

> Template. Replace `{{PLACEHOLDER}}` values and delete this note.
> This is the single entry point for a new session. Read it first, then follow
> the order below before creating anything.

## 1. Read order (do not skip)

1. `./AGENTS.md` — project-wide agent rules.
2. `./docs/team/TEAM_SPEC.md` — roles, modes, gates, evidence.
3. `./docs/team/HANDOFF.md` — where the previous session stopped (may be stale).
4. `./docs/team/DISCOVERY.md` — confirmed requirements and open questions.

Also read your role's skill with the `skill` tool before doing professional work.

## 2. Verify the actual state

Official status first:

```text
agent_teams_status
```

Then compare with the disk (read-only). Official tools are authoritative for
teams this session can control; a team this session does not own cannot be
queried, and must not be touched.

```python
import json
from pathlib import Path

root = Path(".")
teams = root / ".agent-teams"
for path in sorted(teams.glob("*/team.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    print(path.parent.name, "|", data.get("phase"), "|", data.get("halted"),
          "|", data.get("planReviewState"), "|tasks:", len(data.get("tasks", [])))
```

Record in the report: which teams exist, which are archived, which this session
can control, and what the project artifacts say.

## 3. Choose the mode

| Mode | Trigger | Behaviour |
| --- | --- | --- |
| A | Requirements talk, ideas, scope | One decision per round; no team; no formal SPEC before K1; end with a question |
| B | Questions, debugging, advice | Read-only; may answer at any stage; no delivery tasks |
| C | "Implement", "build", "fix" with approval | Create a team only after an explicit gate approval |

If the user's intent is unclear, ask. Never start mode C on your own initiative.

## 4. Gates

| Gate | Approval means |
| --- | --- |
| K1 | Requirements interview finished; a formal SPEC may be written |
| K2 | SPEC approved; architecture work may start |
| K3 | Architecture approved; implementation and tests may start |
| K4 | User accepts delivery |

Acknowledging a proposal is not approval. Record each approval with its date,
the user's own words, and what it unlocks.

## 5. Creating a team (mode C only)

Prerequisites: K1–K3 as applicable, the team profile installed, and the user's
explicit request to create the team now.

```text
agent_teams_create(
  name="<project>-dev-<YYYYMMDD-HHmm>",
  profile="<profile-name>",
  approval="required"
)
```

Rules:

- The name must be unique in this workspace; never reuse an unarchived name.
- `approval="required"`: the plan is staged for review and is not started until
  the user approves it.
- Create the smallest useful task graph; one ready task per member at a time.
- Before dispatching a write task, run the governance baseline if installed:
  `python ./tools/governance/check.py baseline --task <id>`.
- Serialize writes: one writer at a time.
- Never fabricate `user.name`, `user.email`, session ids, attempt ids or hashes.

## 6. Do not disturb other teams

- Teams this session does not own are read-only. Do not approve, resume,
  reassign, archive, message or delete them.
- Do not edit `.agent-teams/` state or team json files by hand.
- Do not inherit another team's approvals, identity or session.

## 7. Preserve progress

When pausing or ending a session, update `./docs/team/HANDOFF.md` with: phase,
approvals, artifact paths and hashes, open tasks, and the next action. Update
`./docs/team/DISCOVERY.md` with confirmed decisions only.

When an artifact changes, state which verdicts become stale (requirements,
architecture, implementation) and re-run the affected checks.

## 8. Team profiles are snapshotted

Editing the profile affects future teams only; an existing team keeps the prompt
snapshot it was created with. A DSH restart is required before a newly installed
profile appears in the runtime listing.

## 9. Common mistakes

| Mistake | Correction |
| --- | --- |
| Treating "continue" as K1 | Ask for an explicit gate statement |
| Creating a team on session start | Wait for the user's request |
| Reviewing your own implementation | Assign the review to another role |
| Claiming tests pass without running them | Run the verify commands and paste exit codes |
| Editing SPEC to make a check pass | Raise a finding; the analyst decides |
| Reusing an unarchived team name | Use a dated, unique name |
| Assuming a HANDOFF is current | Verify with official status and disk evidence |

## 10. Copy-paste prompt

```text
Read ./AGENTS.md, ./docs/team/START-HERE.md, ./docs/team/TEAM_SPEC.md,
./docs/team/HANDOFF.md and ./docs/team/DISCOVERY.md.

Then:
1. Report the runtime team profile state (installed and loadable?).
2. Report the project state and whether this session controls any AgentTeams team.
3. Confirm the three modes (A requirements discussion, B technical consulting,
   C delivery execution) and the K1-K4 gates.
4. List unarchived teams and any naming conflicts.

This is a read-only check: do not create a team, start a task, approve a plan or
modify files. Report briefly and wait for my requirements or questions.
```