# Limitations

Read this before relying on any gate. The process is a discipline and evidence
layer. It is **not** a security boundary and it does not make agents trustworthy.

## 1. What is actually enforced (AgentTeams 0.1.29)

Program-level, checked by the plugin:

1. **Dependencies.** A task cannot be claimed before its dependencies complete.
2. **Scope on completion.** For `implementation` and `repair` tasks, every
   `changedPaths` entry is classified against `inScope`; an out-of-scope path
   rejects completion.
3. **Evidence.** Completion requires `acceptanceResults` for all acceptance
   criteria and `commandsRun` for all `verify` commands; a failed command fails
   the task.
4. **Verdict.** `requirements` and `review` complete only with `verdict=pass`,
   bound to the reviewed artifact's bytes at that moment.
5. **Serialization.** Tasks with overlapping `inScope` cannot run at the same
   time.

## 2. What is not enforced

- **No write-time blocking.** The plugin has no pre-write hook. An out-of-scope
  write can land before the task fails; the failure is detected afterwards.
- **No per-agent filesystem sandbox.** `inScope` is an audit rule, not a
  permission. Any member that can write the workspace can write outside its
  scope; the only consequence is a rejected completion.
- **`changedPaths` is self-declared.** A member can omit a path. The governance
  checker exists to compare against a baseline, but it still runs after writes.
- **Reviewer independence is not native.** The plugin only checks that
  `reviewedTaskId` exists. Nothing stops an implementer from being assigned the
  review; the captain must enforce it, and the governance checker can detect
  violations after the fact.
- **Automatic repair scope is derived from findings.** The generated `inScope`
  comes from paths mentioned in finding text. If a finding mentions a SPEC or
  architecture path, the document path can become writable for the implementer.
  Inspect and amend generated repair tasks before dispatch.
- **Automatic repair inherits the source task's `verify`.** The command may point
  at the source task id and miss the repair's own changes. Review it manually.
- **Prompts are not gates.** Rules written only in a prompt can be ignored by a
  model, especially under pressure. Only task contracts and `verify` commands
  have program-level force.
- **`kind=work` has no quality gate.** Never use it for writes you intend to
  check.

## 3. Governance checker boundaries

`./governance/check.py`:

- runs at task completion or delivery time, never before a write;
- only has force where it is wired into a task's `verify` command — a missing
  `verify` entry means no enforcement;
- returns exit 3 ("cannot verify") when it lacks the baseline, the owner record
  or the lineage; exit 3 is never a pass;
- must not be run concurrently with other writers, or it will attribute their
  changes to the current task;
- is a post-hoc detector, not an isolation mechanism. Real isolation requires
  separate workspaces, containers or an enforcing filesystem layer.

The `delivery` command audits recorded evidence; it is not a full delivery gate.
Success says `EVIDENCE CONSISTENT`, and never substitutes for separate scope,
review, acceptance-coverage or K4 checks. Empty evidence, missing hashes and
unknown write-task roles cannot pass. Historical rejected or stale code reviews
require an explicit, validated `--supersede OLD=NEW` mapping. Deleted files need
successful scope receipts bound to the deleting task and baseline. Neither
mechanism proves findings were semantically resolved. See
[`governance/README.md`](../governance/README.md) for exact command contracts,
exit codes and the reproducible offline scenario.

## 4. Process limits

- Gate approvals are only as good as the record. Store the user's words and the
  date; never infer approval from silence.
- The captain can make planning mistakes. The smallest useful task graph beats a
  large speculative one.
- A profile is snapshotted per team; editing it does not change existing teams.
- Team names are workspace-wide; reusing an unarchived name is rejected.
- A "cannot verify" result means the evidence is missing, not that the claim is
  true.

## 5. Compatibility

- Validated with AgentTeams 0.1.29, BMAD 6.12.4 and DSH 0.2.2-rc.1.
- Other versions may change the profile schema, team state format or quality-gate
  behaviour. Run the resolve check and the checker tests after upgrading.
- This kit copies no third-party source, so upstream changes require no code
  sync — but documented behaviour may drift.

## 6. What to do instead

- For real isolation: separate working directories, separate DSH profiles, or
  containers per agent.
- For trustworthy reviews: human review of product decisions; the checker can
  only prove mechanical facts.
- For reproducibility: keep commands, exit codes and artifact hashes in the
  handoff, and re-run them when bytes change.

## 7. Suggested disclaimer for reports

> This repository enforces dependency order, completion evidence, verdict/hash
> binding and post-hoc scope checks. It does not prevent writes before
> completion, does not sandbox agents, and does not guarantee reviewer
> independence. Human approval remains required for gates and delivery.
