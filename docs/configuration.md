# Configuration

## 1. Where the profile lives

`./templates/team-profile.yml` contains a `profiles:` block to merge into the
AgentTeams section of your DSH plugin configuration. Keep the merge minimal:
AgentTeams rejects unknown keys, so copy only documented fields.

All paths inside prompts are relative to the project root (`./`). Do not paste
machine-specific absolute paths into the profile.

## 2. Profile fields (AgentTeams 0.1.29)

| Field | Required | Meaning |
| --- | --- | --- |
| `description` | yes | Short summary shown in the session's profile listing (truncated to 240 characters) |
| `protocol` | yes | Full working agreement injected into the captain's prompt |
| `executionPrompt` | no | Shared instructions for every member; per-member prompts override |
| `fallback` | no | Fallback instructions when a member or the captain is unavailable |
| `members` | yes (1–8) | Team roster |
| `tasks` | no | Seed tasks (max 32), used when `taskPlanning: seed` |
| `taskPlanning` | no | `captain` (captain designs the graph) or `seed` (default: use `tasks`) |
| `reviewPolicy` | no | Automatic review-round limits |

## 3. Member fields

| Field | Required | Notes |
| --- | --- | --- |
| `name` | yes | Unique; `captain` is reserved |
| `role` | no | Human-readable role label |
| `provider` | only with `model` | LLM route override |
| `model` | only with `provider` | Exact model id |
| `reasoning_effort` | no | Model-specific effort id |
| `executionPrompt` | no | Role instructions; keep relative paths |
| `fallback` | no | Member-specific fallback |
| `tool_policy` | no | Owner-declared policy id; restricts tool visibility only |

A member route must be complete or absent: `provider` without `model` is
rejected.

## 4. Review policy (optional)

```yaml
reviewPolicy:
  requirementsMinRounds: 1
  requirementsMaxRounds: 2
  codeMaxRounds: 2
  maxRepairAttempts: 2
  requiredReviewers: [qa, architect]
```

Limits only decide how many automatic rounds the plugin allows; they never
approve on the user's behalf. Keep them small and explicit.

## 5. Naming and creation

- Team names are workspace-wide and must be unique among **unarchived** teams.
- Recommended pattern: `<project>-dev-<YYYYMMDD-HHmm>`, or a stable name per
  project when only one team exists.
- Create with `approval="required"`: the plan is staged for review and starts
  only after explicit user approval.
- A profile is snapshotted into the team at creation. Editing the profile affects
  future teams only.
- The workspace allows up to 16 profiles; keep one canonical profile per project
  family.

## 6. Captain and members

- `taskPlanning: captain` makes the captain design the task graph; it must create
  the smallest useful DAG and one ready task per member at a time.
- Members claim tasks only after dependencies complete; overlapping `inScope`
  serializes writers.
- The captain communicates with the user and dispatches; it never reviews a
  member's professional work.

## 7. Paths and project layout

The templates assume this layout; rename it consistently if your project differs:

```
./AGENTS.md
./docs/team/START-HERE.md
./docs/team/TEAM_SPEC.md
./docs/team/HANDOFF.md
./docs/team/DISCOVERY.md
./docs/team/RECOVERY.md
./docs/planning/SPEC.md
./docs/planning/ARCHITECTURE.md
./src/
./tests/
./docs/delivery/
./tools/governance/          (optional checker)
```

If you keep BMAD's `_bmad-output/` convention, replace `./docs/planning/` and
`./docs/delivery/` accordingly — and update the profile prompts and
`governance/roles.example.json` together.

## 8. Governance roles

`./governance/roles.example.json` maps each role to allowed and denied globs.
Deny wins; a path matching neither is a violation. Customize the globs to your
layout, then copy the file to `./tools/governance/roles.json`.

```json
{
  "roles": {
    "developer": {
      "allow": ["src/**", "tests/**"],
      "deny": ["**/SPEC.md", "**/ARCHITECTURE.md", "docs/planning/**"]
    }
  }
}
```

## 9. Customizing the templates

- Add project facts (stack, versions, domain constraints) to `AGENTS.md`, not to
  the team profile.
- Keep the team profile focused on process: modes, gates, dispatch, evidence.
- Never hard-code a developer's home directory, drive letter, or username.
- When the layout changes, update the profile prompts, `AGENTS.md`,
  `TEAM_SPEC.md` and `roles.example.json` in one change.

## 10. Version compatibility

The schema above was validated against AgentTeams 0.1.29. A different release may
add or remove keys; run the offline `resolveTeamProfile` check from
`./docs/installation.md` §4 after upgrading.
