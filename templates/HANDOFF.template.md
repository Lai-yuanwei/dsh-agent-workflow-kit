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

## 5. Environment

- Verified versions: DSH {{version}}, BMAD {{version}}, AgentTeams {{version}}.
- Team profile: {{name}} (installed? loaded? requires restart?).
- Commands used to verify state: {{commands}}.

## 6. Next action

1. {{Concrete next step}}
2. {{Second step, if needed}}

Do not start implementation while a required gate is open.

## 7. Changelog

| Date | Change | Evidence |
| --- | --- | --- |
| {{date}} | {{change}} | {{command / file}} |