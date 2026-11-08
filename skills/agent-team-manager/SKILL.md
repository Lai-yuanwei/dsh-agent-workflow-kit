---
name: agent-team-manager
description: Bootstrap and run a BMAD + AgentTeams delivery team in this project. Use when the user asks to start a team, resume a project, run a requirements interview, consult about the project, approve a gate, or hand off a session.
---

# BMAD Team Manager

## Purpose

This skill encodes the *process* around a BMAD + AgentTeams delivery team. It
does not create agents, schedule tasks or bypass approvals. Real dispatch and
quality gates come from the AgentTeams plugin (`agent_teams_*` tools). If that
plugin is not available, say so and stop — do not imitate its tools.

## When to use

- Starting a new session on an existing project.
- A requirements interview or product discussion.
- A technical question during planning or delivery.
- The user asks to build/implement something (mode C).
- Pausing or ending a session, when a handoff is needed.

Do not use this skill to force a workflow on the user. Ask which mode they want
when their intent is ambiguous.

## Activation

1. Read `./AGENTS.md`, `./docs/team/TEAM_SPEC.md`, `./docs/team/HANDOFF.md` and
   `./docs/team/DISCOVERY.md`, in that order.
2. Check the actual state:
   - `agent_teams_status` (if the AgentTeams tools exist);
   - read-only: list `.agent-teams/*/team.json` for teams this session does not
     control, and note only that they exist.
3. Report the state briefly: phase, gates, artifacts, controllable teams,
   conflicts. Then ask what the user wants.

## Modes

| Mode | Behaviour |
| --- | --- |
| A — requirements interview | One decision per round; no team, no tasks, no formal SPEC before K1; challenge weak ideas with evidence; end with one question |
| B — technical consulting | Read-only answers at any stage; never create delivery tasks |
| C — delivery execution | Only after explicit approval; create teams with a unique name and `approval="required"` |

If the user says "that works", "continue", or asks a question, that is not gate
approval.

## Gates

| Gate | Unlocks |
| --- | --- |
| K1 | The analyst may write the formal SPEC |
| K2 | The architect may start full architecture design |
| K3 | The developer may start implementation and tests |
| K4 | Delivery acceptance |

Write approvals with the date and the user's exact words into
`./docs/team/DISCOVERY.md` and `./docs/team/HANDOFF.md`.

## Creating a team (mode C)

1. Confirm the profile is installed and loaded (a restart may be required).
2. Confirm the required gates are approved.
3. Create one team with a unique dated name:

```text
agent_teams_create(name="<project>-dev-<YYYYMMDD-HHmm>", profile="<profile>", approval="required")
```

4. Present the staged plan and stop; the user approves it.
5. After approval, dispatch one ready task per member; serialize writes.
6. Never reuse an unarchived name, never inherit another team's approvals, and
   never hand-edit `.agent-teams/` state.

## Quality discipline

- Requirements → architecture → implementation → verification → review → integration.
- Express enforceable rules in task contracts (`objective`, `acceptance`,
  `verify`, `inScope`, `outOfScope`), not only in prose.
- Reviews go to someone other than the implementer.
- Evidence: command, exit code, output excerpt, path, hashes where verdicts bind.
- If the governance checker is installed, include `scope`/`review` in `verify`
  and run `delivery` before delivery.

## Evidence discipline

Every report must be reproducible. Never invent an attempt id, a hash, a test
result or a user approval. If you cannot verify something, say "cannot verify"
and explain why.

## Handoff

When pausing: update `./docs/team/HANDOFF.md` (phase, gate status, artifacts and
hashes, open tasks, next action) and note which verdicts became stale. Keep
`./docs/team/DISCOVERY.md` limited to confirmed decisions.

## Boundaries

- This skill cannot schedule, dispatch, retry or gate tasks by itself.
- It does not grant filesystem isolation; `inScope` only governs completion.
- It cannot approve gates for the user.
- It does not modify BMAD skills or the AgentTeams plugin.

## References

- `./docs/workflow.md` — modes, gates, evidence.
- `./docs/configuration.md` — profile fields and naming.
- `./docs/limitations.md` — what is and is not enforced.
- `./templates/START-HERE.template.md` — session bootstrap prompt.