# Governance checks

Install `check.py` at `tools/governance/check.py` in the target project and copy
`roles.example.json` to `tools/governance/roles.json`. Customize the role policy
before taking a baseline. Use `--root` explicitly when running the checker from
this kit rather than from its installed location. Global options precede the
subcommand:

```text
python tools/governance/check.py --root . --team my-team baseline --task w1
python tools/governance/check.py --root . --team my-team scope --task w1
python tools/governance/check.py --root . --team my-team review --task r1
python tools/governance/check.py --root . --team my-team delivery
```

## Command contracts

| Command | What success establishes |
| --- | --- |
| `baseline` | A file snapshot was recorded before a write task. |
| `scope` | Changes since the baseline comply with the assignee's role policy. Saves a successful scope receipt, including removed files. Run with other writers idle. |
| `review` | The reviewer differs from all recorded implementation, repair and integration owners reachable through dependencies, source tasks and reviewed tasks. Missing references, missing owners and cycles cannot establish independence. |
| `delivery` | Recorded review/requirements evidence has a completed, passing verdict, valid SHA-256 hashes and matching files; declared write-task paths comply with identifiable role policies. |

`delivery` is retained for command compatibility. Its success message is
**EVIDENCE CONSISTENT**, not approval to deliver. It does not prove that every
required task exists or is complete, that all changes were declared, that
acceptance criteria are covered, or that the user approved K4. Run `scope` and
`review` separately and inspect the task graph and acceptance evidence.

Exit codes are `0` for success, `2` for a detected violation and `3` when evidence
cannot be verified. If both a violation and missing evidence are found by the
delivery audit, both are reported and exit `2` takes precedence. Missing or
malformed hashes, unknown write-task roles, empty artifact evidence and missing
state files never count as success.

## Repair history and deletions

Keep failed and stale review records. After a completed repair and independent
passing review, explicitly identify which old review the new one replaces:

```text
python tools/governance/check.py --root . --team my-team delivery --supersede r1=r2
```

This is a checker option, not a new AgentTeams field or API. Record the exact
command and replacement rationale in the handoff. The checker reads runtime
state and never rewrites old tasks. Without this option, old records still block.

A replacement must be a completed, passing `review` by the **same reviewer**,
independent of all recorded implementers. Its completed repair source chain
must lead to the old review or its reviewed task. Scheduling dependencies alone
do not establish replacement. The new review must cover every old artifact,
every declared changed path of the old target, and all repairs on that chain,
using current artifact hashes or verified deletion receipts. Other unresolved
reviews continue to block. Findings themselves still require human/QA assessment.

Repeat the option for multiple historical reviews. For multiple repair rounds,
point each old review directly to the final passing review, for example
`--supersede r1=r3 --supersede r2=r3`. Cycles, duplicate old ids, partial coverage,
unrelated repairs and failed successors cannot pass. Requirements approvals and
reviewer changes are not automatically superseded: they require a separately
designed and validated runtime workflow, not hand-edited history.

Deletion is accepted only if a **completed write task** declares the path and a
successful `scope` receipt proves it existed in that task's baseline and was
removed. Receipts bind team, task, owner, kind, attempt, baseline hash and current
role policy. Unrecorded loss, a different attempt, changed policy or overwritten
baseline cannot reuse that proof. An absent reviewed artifact still blocks unless
its review is explicitly superseded by a valid repair/review covering the deletion.

Baselines and scope receipts are stored under `.governance/baselines/` and
`.governance/scopes/`, keyed by SHA-256 of team and task ids. These are local audit
records, not tamper-proof authorization. Preserve them for the same team across
sessions; never copy them to claim another team's work. Old flat baseline files
and inherited parent-task baselines are no longer accepted. Start a new task or
attempt with a fresh baseline **before any write**; do not retroactively create
one to validate already-finished work.

The assignee and current attempt must be established before the baseline. If the
runtime initializes the attempt only on claim, pause the writer after claim and
before its first write to take the baseline. Do not dispatch unpaused writers
before the baseline. A new attempt needs its own baseline and `scope --task` id.

## Reproducible offline checks

Requires Python 3.10+ and pytest:

```text
python -m pytest governance/tests examples/demo-project/tests -q -p no:cacheprovider
python -m pytest governance/tests -q -k offline_repair_and_reaudit
```

The second command uses synthetic state in a temporary project: baseline,
authorized implementation, blocked self-review, independent review, stale hash
after repair, and an appended new review while preserving history. Additional
tests cover rejected reviews, multiple repair rounds, authorized deletion and
reopening the saved state in a fresh Python process. These are executable
checker regression scenarios, **not** evidence of a real DSH/AgentTeams run or
cross-session recovery. Real integration validation still needs actual plugin
tasks, a rejected review, repair, re-review and a session handoff with logs.

CI runs both suites on Windows and Linux with Python 3.11 and 3.13. Local tests
do not establish that the remote CI matrix or plugin integration has passed.
