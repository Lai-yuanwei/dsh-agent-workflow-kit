# AGENTS.md — {{PROJECT_NAME}} agent conventions

> Template. Replace `{{PLACEHOLDER}}` values and delete this note.
> This file governs every AI agent working in this repository, including the
> team captain and every member.

## 1. Scope

`{{PROJECT_NAME}}` is {{ONE_SENTENCE_DESCRIPTION}}.

This repository uses the dsh-agent-workflow-kit conventions: BMAD role skills for
professional work, AgentTeams for task dispatch and quality gates. This file
binds all agents; more specific files (`./docs/team/TEAM_SPEC.md`) refine it and
take precedence where they are stricter.

## 2. Prerequisites (verify, do not assume)

| Component | Verified version | Where |
| --- | --- | --- |
| DeepSeek Harness | {{DSH_VERSION}} | Host application |
| BMAD Method | {{BMAD_VERSION}} | `./.agents/skills/bmad-*` |
| AgentTeams plugin | {{AGENT_TEAMS_VERSION}} | DSH profile package list |

Do not change the model, upgrade the host, edit global profiles, or rotate API
keys to "make the workflow run". If a version change is genuinely required,
propose it and wait for approval.

## 3. Roles and skills

Roles must load their skills with the `skill` tool before acting:

| Role | Skills | Writes |
| --- | --- | --- |
| analyst | `bmad-agent-analyst`, `bmad-agent-pm`, `bmad-prd` | `./docs/planning/**` (requirements only), `./docs/team/DISCOVERY.md` |
| architect | `bmad-agent-architect`, `bmad-architecture` | `./docs/planning/**` (architecture), `./docs/delivery/**` |
| developer | `bmad-agent-dev`, `bmad-build` | `./src/**`, `./tests/**`, implementation reports |
| qa | `bmad-code-review`, `bmad-review` | `./docs/delivery/**` (reports and probes) |
| captain | — | dispatch and reporting; no professional review |

## 4. Workflow and gates

```
requirements → architecture → implementation → verification → review → integration
```

Gate rules (also enforced through task dependencies and `verify` commands):

1. No implementation before the requirements task passes (`verdict=pass`).
2. No source change before the architecture task completes with feasibility and
   risk conclusions.
3. No verification or review before the implementation task's `verify` commands
   pass.
4. Review passes only with `verdict=pass`; otherwise repair and re-review.
5. Integration depends only on completed, passed tasks.

Human gates: K1 ends the requirements interview (a formal SPEC may then be
written), K2 approves the SPEC (architecture may start), K3 approves the
architecture (coding and tests may start), K4 is delivery acceptance. Approval
must be grounded in the user's words. A short reply such as "continue" or
"that works" can approve the single approval object and next action explicitly
proposed in the previous turn. Ambiguous replies, multiple objects and silence
do not establish approval. Record the exact words, date and approved object.

## 5. Hard rules

1. Do not assume the user's technical decisions are correct.
2. Push back on material requirement defects with evidence and an alternative.
3. Do not start development before requirements and architecture approvals.
4. Do not claim completion when tests fail.
5. Do not add dependencies, services or abstractions without a stated reason and
   a comparison of alternatives.
6. Keep review evidence reproducible: command, exit code, output excerpt, path.
7. Agents do not approve their own professional work; the captain does not
   replace a member's approval.
8. Do not edit approved requirements, architecture or acceptance criteria to make
   a failing check pass.

## 6. Evidence

Every completion report carries:

- `attempt_id`, `changedPaths`, `commandsRun` (with exit codes),
  `acceptanceResults`;
- the exact file paths and sections changed;
- hashes for artifacts a verdict binds to, when applicable.

## 7. Write ownership

| Artifact | Owner |
| --- | --- |
| `./docs/planning/**/SPEC.md`, acceptance criteria | analyst |
| `./docs/planning/**/ARCHITECTURE.md` | architect |
| `./src/**`, `./tests/**` | developer |
| `./docs/delivery/**` | the report's author |
| `./docs/team/DISCOVERY.md` | analyst or captain; confirmed decisions only |
| `./AGENTS.md`, other `./docs/team/**`, plugin config | captain, with user approval |

## 8. Program-level versus prompt-level

Program-level in AgentTeams 0.1.29: `inScope` path classification on completion,
required acceptance/command evidence, `verdict` bound to artifact bytes, and
dependency ordering. Prompt-level only: no write-time blocking, member-declared
`changedPaths`, no per-agent sandbox, and reviewer independence by assignment.
Do not describe prompt rules as technical isolation.

## 9. Optional governance checker

When `./tools/governance/check.py` exists:

- implementation verify: `python ./tools/governance/check.py scope --task <id>`;
- review verify: `python ./tools/governance/check.py review --task <id>`;
- delivery: `python ./tools/governance/check.py delivery`.

Exit 3 means the check could not verify the claim. Never treat it as a pass.

## 10. Forbidden

- Editing another role's owned artifacts instead of raising a finding.
- Forging test output, skipping `verify`, or weakening acceptance criteria.
- Hand-editing `.agent-teams/` state, `team.json`, or copying team identities.
- Approving a staged team plan on the user's behalf.
- Writing machine-specific absolute paths into repository files.

## 11. Self-check

```powershell
# Skill count
(Get-ChildItem ./.agents/skills -Directory).Count
# Governance checker regression tests (when installed)
python -m pytest ./governance/tests -q -p no:cacheprovider
```
