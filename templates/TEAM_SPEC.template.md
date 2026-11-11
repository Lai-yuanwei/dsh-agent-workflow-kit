# TEAM_SPEC — {{PROJECT_NAME}} delivery team

> Template. Replace every `{{PLACEHOLDER}}` and delete this note.
> Paths are relative to the project root (`./`).

## 1. Purpose and scope

This document defines how the AI delivery team works on **{{PROJECT_NAME}}**:
who is allowed to do what, which approvals gate which phase, what evidence each
phase must produce, and what the process cannot enforce.

It is a working agreement, not a permission system. AgentTeams supplies task
dispatch and quality gates; this document supplies the human process around
them. Read `./docs/limitations.md` (or §10 below) before claiming any isolation.

## 2. Roles and skill mapping

Each member must actually load the listed skills with the `skill` tool and cite
the loaded skill in its first report. Holding a role name without loading the
skill is not acceptable.

| Role | BMAD role | Primary skills | Fallback skills |
| --- | --- | --- | --- |
| analyst | Business Analyst / Product Manager | `bmad-agent-analyst`, `bmad-agent-pm`, `bmad-prd` | `bmad-spec`, `bmad-forge-idea` |
| architect | System Architect | `bmad-agent-architect`, `bmad-architecture` | `bmad-review`, `bmad-correct-course` |
| developer | Senior Software Engineer | `bmad-agent-dev`, `bmad-build` | `bmad-create-epics-and-stories` |
| qa | Test and independent review | `bmad-code-review`, `bmad-review` | `bmad-qa-generate-e2e-tests`, `bmad-walkthrough` |
| captain | — | None; dispatch and reporting only | — |

The captain never performs a professional review and never approves a gate on a
member's behalf.

## 3. Working modes

| Mode | Name | Rules |
| --- | --- | --- |
| A | Requirements interview (default) | One decision per round; no team, no tasks, no formal SPEC before K1; challenge unsound designs with evidence; end the round with a question |
| B | Technical consulting | Read-only answers at any stage; never creates delivery tasks |
| C | Delivery execution | Only after an explicit gate approval; create teams with a unique dated name and `approval="required"` |

The user does not need to know mode names. If intent is ambiguous, ask which mode
is intended. Never create a team merely because a session started.

## 4. Approval gates

| Gate | Approval means | Only then |
| --- | --- | --- |
| K1 | The requirements interview is finished | The analyst may write the formal SPEC |
| K2 | The SPEC is approved | The architect may start full architecture design |
| K3 | The architecture is approved | The developer may start implementation and tests |
| K4 | The user accepts the delivered result | Delivery is complete |

Rules:

1. Interpret the user's words in context. "That works" or "continue" may approve
   the single approval object and next action explicitly proposed in the previous
   turn. Ambiguous replies, multiple objects, questions alone and silence do not
   establish approval. Record the exact words, date and approved object.
2. Testing may start after K3. A green test suite is not K4.
3. If a gate is rejected, record the reason and the changes required before it
   can be re-proposed.
4. Never claim a gate is approved because a document exists or a member said so.

## 5. Delivery workflow and task kinds

```
requirements → architecture → implementation → verification → review → integration
```

Gate rules (mirrored in task dependencies):

1. No implementation task before the requirements task completes with
   `verdict=pass`.
2. No source change before the architecture task completes with its feasibility
   conclusion and risk list.
3. No verification or review before the implementation task's `verify` commands
   pass.
4. Review completes only with `verdict=pass`; `needs_revision` or `reject` means
   repair plus a new review round.
5. Integration depends only on completed and passed tasks.

Express enforceable constraints as AgentTeams quality tasks
(`kind = requirements | implementation | verification | review | integration`)
with `objective`, `acceptance`, `verify`, `inScope` and `outOfScope`. A rule that
only lives in a prompt is a convention, not a gate.

## 6. Evidence

Every report must be reproducible:

- The exact command, its exit code, and the relevant output lines.
- File paths (with line numbers where possible) and the section changed.
- The current `attempt_id` for the running task.
- `changedPaths`, `commandsRun`, `acceptanceResults` for writes and verification.
- Hashes for any artifact a verdict binds to.

"Directory exists", "the model confirmed" and screenshots without a command do
not count as evidence.

## 7. Write ownership

Ownership follows the artifact, not who is named in a task.

| Artifact | Owner | Others |
| --- | --- | --- |
| `./docs/planning/**/SPEC.md`, requirements and acceptance criteria | analyst | read-only; raise findings |
| `./docs/planning/**/ARCHITECTURE.md`, architecture decisions | architect | read-only; raise findings |
| `./src/**`, `./tests/**` | developer | read-only; qa may add probes under `./docs/delivery/probes/` |
| `./docs/delivery/**` (QA and review reports) | the author (qa / architect) | read-only |
| `./docs/team/DISCOVERY.md` | analyst or captain; confirmed decisions only | read-only |
| `./AGENTS.md`, other `./docs/team/**`, plugin configuration | captain, with user approval | forbidden |

Developers never edit approved requirements or architecture. Requirement changes
belong to the analyst; architecture changes belong to the architect; test
criteria are never changed by the person whose code is under test.

## 8. Program-level versus prompt-level constraints

Program-level (AgentTeams 0.1.29):

- `implementation` / `repair` tasks: each `changedPaths` entry is classified
  against `inScope`; an out-of-scope path rejects completion.
- Completion requires `acceptanceResults` for every acceptance criterion and
  `commandsRun` for every `verify` command; a failed command fails the task.
- `review` / `requirements` complete only with `verdict=pass`, bound to the
  artifact hash at review time; changing the artifact invalidates the verdict.
- Tasks cannot be claimed before their dependencies complete; overlapping
  `inScope` forces serialization.

Prompt-level only (do not describe as isolation):

- No write-time blocking: an out-of-scope write can land before the task fails.
- `changedPaths` is still declared by the member.
- There is no per-agent filesystem sandbox; `inScope` governs only completion.
- Reviewer ≠ implementer is not validated natively; it relies on assignment.
- Automatically generated repair tasks derive their scope from findings text;
  the captain must inspect and, if needed, amend them (see §10).

## 9. Optional governance checker

`./governance/check.py` performs post-hoc checks:

```powershell
python ./tools/governance/check.py baseline --task <id>
python ./tools/governance/check.py scope --task <id>
python ./tools/governance/check.py review --task <id>
python ./tools/governance/check.py delivery
```

- `implementation` / `repair` verify commands include `scope --task <id>`; the
  captain takes `baseline --task <id>` after owner/attempt initialization but
  before the first write. Pause the writer if needed. Repairs use their own
  task id and fresh baseline; never inherit the source task's verify id.
- `review` verify includes `review --task <id>`.
- Before delivery, run `delivery`.

Preserve historical reviews. Use validated `delivery --supersede OLD=NEW`
mappings for completed repair chains and record the exact command in HANDOFF.
Missing files require successful scope deletion receipts. On a new session,
follow `./docs/team/RECOVERY.md`; never assume ownership of the old team.

Exit codes: 0 pass, 2 violation, 3 cannot verify. Exit 3 is never a pass.

## 10. Operating rules

1. Create teams with `approval="required"` and a name that has never existed in
   this workspace.
2. One captain, one clear entry point. Members report to the captain; the captain
   reports to the user.
3. Serialize writes: no two agents (captain included) edit checked files at the
   same time.
4. When a repair task is generated automatically, inspect its `inScope`; move
   documentation findings to analyst/architect tasks with single-file scope.
5. A changed artifact invalidates verdicts bound to the old bytes; re-run the
   affected checks and say which verdicts are stale.
6. Do not approve your own implementation, and do not ask for a deliberate
   failure to unlock a repair loop.
7. Stop and ask when a requirement, architecture decision or acceptance criterion
   needs human approval.

## 11. Known limitations

- Gates are enforced at completion/delivery time, not before writes.
- Task results, verdicts and hashes are stored in `.agent-teams/` state; treat
  that directory as runtime state, never as source.
- Team profiles are snapshotted into a team at creation. Editing the profile does
  not change existing teams.
- A "cannot verify" result (exit 3) means the check could not establish
  independence; it is not evidence of independence.
- The process does not replace human review of product decisions.

## 12. Configuration summary

| Item | Value |
| --- | --- |
| Team profile | `{{TEAM_PROFILE_NAME}}` in `./templates/team-profile.yml` |
| Members | analyst, architect, developer, qa |
| Task planning | captain |
| Creation | `approval="required"`, unique dated name |
| Governance | optional, `./governance/` |
| Artifact directories | planning `./docs/planning/`, delivery `./docs/delivery/` |
