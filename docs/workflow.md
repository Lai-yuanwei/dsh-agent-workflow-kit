# Workflow

## 1. Three modes

### A — requirements interview (default)

- One decision per round. Ask the single most consequential question, then stop.
- No team, no tasks, no formal SPEC until K1.
- Push back on unsound ideas with evidence and an alternative; do not agree just
  to please.
- Record confirmed decisions in `./docs/team/DISCOVERY.md`; keep open questions
  open.
- The user does not need to say "mode A". If a session opens without a request,
  this is the assumed behaviour once the user starts describing a product.

### B — technical consulting

- Read-only answers at any stage: architecture questions, error analysis, code
  reading, tooling advice.
- Never creates delivery tasks and never changes artifacts.
- May be answered by the captain or delegated to the relevant role for a
  read-only analysis.

### C — delivery execution

- Requires the applicable gates to be approved and the user's explicit request
  to start work.
- The captain creates one team with a unique dated name and
  `approval="required"`, presents the staged plan, and waits.
- After approval, dispatch one ready task per member; serialize writes.

## 2. Gates in practice

| Gate | What the user approves | What the team may then do |
| --- | --- | --- |
| K1 | "The interview is done; write the spec." | analyst writes `./docs/planning/SPEC.md` |
| K2 | "The spec is right." | architect writes `./docs/planning/ARCHITECTURE.md` |
| K3 | "The architecture is right." | developer implements; qa may start tests |
| K4 | "I accept the delivery." | delivery closes |

Interpret approval wording in context. A short reply such as "可以", "继续",
"okay", or "that works" approves the single object and next action explicitly
named in the immediately preceding turn. If that turn named multiple objects or
was unclear, the reply does not establish approval; silence never does. Record
the user's exact words and the object approved.

These are not approvals by themselves:

- "That works." / "Okay." / "Continue."
- "Explain how this feature works."
- "Can it also do X?" (a new requirement, not a gate)
- Silence, or a member's own claim that a gate passed.

When in doubt, ask: "Is this K1 approval, or should we keep discussing?"

## 3. Phases and task kinds

| Phase | Task kind | Owner | Evidence |
| --- | --- | --- | --- |
| Requirements | `requirements` | analyst | SPEC path, acceptance list, `verdict=pass` |
| Architecture | `requirements` | architect | ARCHITECTURE path, acceptance criteria, verify commands, feasibility and risks, `verdict=pass` |
| Implementation | `implementation` | developer | changed paths, verify commands, exit codes |
| Verification | `verification` | qa (or developer for unit checks) | test output, probes, coverage notes |
| Review | `review` | non-implementer | findings with file/line/command, `verdict` |
| Repair | `repair` | implementer | findings closed, re-run verify |
| Integration | `integration` | developer | full suite, delivery check |

Gate rules are mirrored in dependencies: an implementation task cannot be
claimed before its requirements dependency completes with `verdict=pass`.
Architecture design is a quality task: use `requirements` with acceptance
criteria, verify commands and a passing verdict. K2 authorizes starting it;
task completion then checks the design evidence. `work` has no quality gate and
must not be used for architecture writes. A `requirements` task may also review
design read-only.

## 4. Quality contracts

Put enforceable rules in the task, not only in chat:

```text
objective:     What the task delivers, in one paragraph.
acceptance:    Testable criteria, each with evidence.
verify:        Commands that must pass; failures fail the task.
inScope:       Paths the task may change.
outOfScope:    Paths it must not change (docs, config, other roles' artifacts).
```

A review completes only with `verdict=pass`. `needs_revision` or `reject` fails
the task and starts a repair loop; do not soften the acceptance criteria to
escape the loop.

## 5. Evidence format

Every completion report includes:

```text
attempt_id:   <current attempt>
changedPaths: <paths>
commandsRun:  <command -> exit code -> relevant output>
acceptanceResults: <criterion -> passed/failed -> evidence>
```

Rules:

- Paste the failing line, not the whole log.
- Cite file paths and line numbers for every finding.
- Record hashes for artifacts a verdict binds to.
- Never paste secrets, tokens or personal data into reports.

## 6. Review independence

- A review task must be assigned to someone other than the implementer.
- The captain checks this before dispatch; if a task's owner matches the
  reviewed task's owner, reassign it.
- The governance checker (`review` subcommand) can verify independence from
  `team.json` lineage; exit 3 means "cannot verify", which is not a pass.

## 7. Staleness

When an artifact changes, the verdict that bound its bytes is stale:

| Changed | Invalidates |
| --- | --- |
| `./src/**` | implementation verification and code review verdicts |
| SPEC | requirements verdict; re-check acceptance coverage |
| ARCHITECTURE | architecture review and acceptance mapping |

Re-run the affected checks and state in the handoff which verdicts were
re-issued and which artifacts are unchanged (with hashes).

## 8. Handoff

At the end of a session:

1. Update `./docs/team/HANDOFF.md`: phase, gate status with quotes, artifacts and
   hashes, open tasks, next action.
2. Update `./docs/team/DISCOVERY.md` only with confirmed decisions.
3. Leave the team in a known state (idle, or archived); never leave a write task
   running while you stop.
4. Report what the next session must verify first.

Use [the recovery procedure](./recovery.md) to decide whether the next session
can continue the same team or needs an approved new team. Preserve history and
scope receipts. Delivery after repairs uses explicit validated supersession
mappings; see [checker contracts](../governance/README.md). The real integration
acceptance record in the recovery guide remains required before claiming a
tested DSH/AgentTeams session-to-session workflow.
