# AGENTS.md — demo task list

This is a demo project for the dsh-agent-workflow-kit. It follows the kit's
conventions; the full rules live in the kit's
`templates/AGENTS.example.md`.

## Scope

A minimal in-memory task list: add a task, complete it, list pending tasks. No
persistence, no network, no UI.

## Roles

| Role | Skills | Writes |
| --- | --- | --- |
| analyst | `bmad-agent-analyst` | `./docs/planning/**`, `./docs/team/DISCOVERY.md` |
| architect | `bmad-agent-architect` | `./docs/planning/**` |
| developer | `bmad-agent-dev` | `./src/**`, `./tests/**` |
| qa | `bmad-code-review` | `./docs/delivery/**` |

## Gates

K1 → SPEC, K2 → architecture, K3 → code, K4 → delivery. "Continue" may approve
the single approval object and next action explicitly proposed in the previous
turn. Ambiguous replies, multiple objects and silence do not establish approval.
Record the exact words, date and approved object.

## Hard rules

1. Requirements before code; architecture before edits.
2. Tests must pass before completion is claimed.
3. Do not change another role's artifacts; report findings.
4. Keep evidence: command, exit code, output.
5. Do not add dependencies for this demo.

## Verify

```powershell
python -m pytest ./tests -q -p no:cacheprovider
```
