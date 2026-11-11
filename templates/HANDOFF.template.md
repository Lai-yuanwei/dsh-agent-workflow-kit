# HANDOFF — {{PROJECT_NAME}}

> Template. Replace `{{PLACEHOLDER}}` values. Keep this file short and current;
> history belongs in the changelog at the end.

**Last updated:** {{YYYY-MM-DD HH:mm}} ({{TIMEZONE}})
**Updated by:** {{ROLE / SESSION}}
**Project phase:** {{DISCOVERY | SPEC | ARCHITECTURE | IMPLEMENTATION | VERIFICATION | REVIEW | DELIVERY}}
**Team state:** {{no team | team name + phase (staged/running/halted) }}

## 1. Where we stopped

{{One short paragraph: what was being worked on, what is done, what is next.}}

## 2. Approval gates

| Gate | Status | Evidence (user's words, date) |
| --- | --- | --- |
| K1 | {{open/approved}} | {{quote}} |
| K2 | {{open/approved}} | {{quote}} |
| K3 | {{open/approved}} | {{quote}} |
| K4 | {{open/approved}} | {{quote}} |

If a gate is open, state exactly what the user must decide.

## 3. Artifacts

| Artifact | Path | Hash (sha256) | Verdict / date |
| --- | --- | --- | --- |
| Requirements | `./docs/planning/SPEC.md` | {{hash}} | {{verdict}} |
| Architecture | `./docs/planning/ARCHITECTURE.md` | {{hash}} | {{verdict}} |
| Implementation | `./src/**` | {{commit or hash}} | {{verify result}} |
| QA report | `./docs/delivery/QA-REPORT.md` | {{hash}} | {{verdict}} |

## 4. Open tasks and findings

| Task | Kind | Owner | Status | Blocking? |
| --- | --- | --- | --- | --- |
| {{id}} | {{kind}} | {{role}} | {{status}} | {{yes/no}} |

Open findings that are not yet repaired: {{list or "none"}}.

Historical review replacements: {{old review -> final review, rationale,
exact --supersede options, observed audit exit code; or "none"}}.
Keep failed records; do not delete history to obtain a passing audit.

## 5. Environment

- Verified versions: DSH {{version}}, BMAD {{version}}, AgentTeams {{version}}.
- Team profile: {{name}} (installed? loaded? requires restart?).
- Commands used to verify state: {{commands}}.
- Current write task/attempt/owner: {{ids or "none"}}.
- Baseline and successful scope receipts: {{paths; include deletion evidence}}.
- Active writers: {{none, or stop/finish action and observed runtime result}}.
- Recovery route: {{same team with confirmed control / supported operator
  transfer / approved new team; see RECOVERY.md}}.

## 6. Next action

1. {{Concrete next step}}
2. {{Second step, if needed}}

Do not start implementation while a required gate is open.

## 7. Changelog

| Date | Change | Evidence |
| --- | --- | --- |
| {{date}} | {{change}} | {{command / file}} |
