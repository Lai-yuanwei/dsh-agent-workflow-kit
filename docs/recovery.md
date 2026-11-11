# Session recovery and delivery rehearsal

This is an operating procedure, not a claim that DSH supports session takeover.
Copy this file into the target project as `docs/team/RECOVERY.md`.

## Before ending a session

1. Stop dispatching writes. Use the actual runtime controls to wait for writers
   to finish or stop them; record their final status. Do not leave writers active.
2. Update HANDOFF with team name, current task and attempt ids, completed work,
   remaining findings, gates (object, exact user words, date), artifact hashes,
   baseline/receipt locations and the exact verification commands and exit codes.
3. Record rejected/stale reviews and any proposed `--supersede OLD=NEW` mappings.
   A proposed mapping is not a passing check. Preserve runtime history unchanged.

## At the start of the next session

Read START-HERE, TEAM_SPEC, HANDOFF and DISCOVERY. Query `agent_teams_status` and
compare artifact hashes with HANDOFF. Establish which team this session can
actually control, whether writers are active, and which artifacts changed.
Never infer control or approval merely because files exist.

| Observed state | Next action |
| --- | --- |
| Official tools confirm this session controls the existing team | Reconcile actual task status and remaining findings; rerun checks affected by changed bytes. Resume only work already authorized. Use the runtime's exposed operations. |
| This session cannot control the old team, but the host explicitly offers a supported resume/transfer operation | Have the authorized operator use that operation. Re-query status to confirm control before any dispatch. This kit does not invent an API or copy captain identity. |
| No supported transfer is available | Keep the old team read-only. Ask for authorization to create a new uniquely named team for the remaining work, with a staged plan. Reuse artifacts as inputs, not old task states, ownership or passing verdicts. |
| An old writer is active, or its state cannot be established | Do not write in the shared workspace. Have its controlling session/operator stop it, or use a separate workspace with an explicitly selected stable artifact snapshot. |

For a new team, list which product decisions remain applicable and which are
invalidated by changed requirements or artifacts. Preserve the original user
quotes as history; obtain approval for the new team's plan and unresolved scope.
Create new verification/review tasks over the existing artifacts before relying
on them. Do not copy `.agent-teams` state or `.governance` receipts into the new
team as evidence. New write attempts need fresh baselines before their first
write, with stable owner and attempt ids. Keep obsolete teams untouched unless
their authorized controller archives them.

## Delivery sequence

1. Confirm required implementation/repair tasks are complete and their test and
   acceptance evidence is present. Inspect findings; no unresolved blocking item
   may be hidden by an unrelated passing review.
2. Run scope checks during each write attempt, before other writers begin.
   Preserve successful receipts. A delivery-time scope rerun over intervening
   tasks is not a substitute for the original per-task check.
3. Run independent review checks for current reviews. Then run the evidence audit
   with explicit team and validated historical-review mappings, for example:
   `python tools/governance/check.py --root . --team NAME delivery --supersede r1=r2`.
4. Report current hashes, all relevant test/check exit codes, remaining limitations
   and requirement-to-evidence coverage. Exit 0 from the audit is not K4.
5. Present that concrete result for user acceptance. Record K4 only after the
   user accepts it; then save the final handoff and leave the runtime quiescent.

## Real integration acceptance record (not yet executed by this kit)

Perform this in an actual DSH/AgentTeams environment. Keep a report containing
the following evidence; never replace it with synthetic `team.json` edits:

- Exact DSH, AgentTeams, BMAD and Python versions; successful profile resolution.
- K1/K2/K3 records, real task ids, task contracts and captured verification output.
- One genuine rejected review, a completed repair and a separate passing review;
  retain the rejected record and demonstrate the validated supersession command.
- One authorized deletion with baseline, scope receipt and a passing final audit;
  one unrecorded loss that the audit blocks.
- End one session with no writers active. Start another and follow the applicable
  recovery branch above. Record status before/after, unchanged/changed hashes and
  renewed verification evidence. If transfer is unsupported, demonstrate the
  approved new-team branch instead of claiming takeover succeeded.
- Final requirement coverage, test results, evidence audit and the user's K4 quote.

Only mark integration validated after this record exists. Offline tests prove
checker behavior and persisted-state loading, not real session recovery.
