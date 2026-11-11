# dsh-agent-workflow-kit

A community starter kit for running a four-role software delivery team in
[DeepSeek Harness (DSH)](https://deepseek.com) by combining **BMAD Method**
skills with the **AgentTeams** task plugin.

It packages the working agreements, not the engines: BMAD supplies the role
skills, AgentTeams supplies task dispatch and quality gates, and this kit
supplies the team profile, documents and review discipline that connect them.

This kit is compatible with BMAD Method and requires the AgentTeams plugin. It
ships neither engine and is not an official BMAD, AgentTeams or DSH project.

> **Status: public source preview, not a stable release.** Source is available under MIT, but a tagged GitHub Release has not been published and live DSH/AgentTeams end-to-end acceptance remains pending.
> This is an independent community project; it is not an official BMAD,
> AgentTeams or DSH project. See [LICENSING.md](./LICENSING.md).

## Current validation

| Check | Result |
| --- | --- |
| Source availability | Public GitHub repository, [MIT License](./LICENSE) |
| Local regression tests | 60 tests passed for the governance checker and demo (2026-11-11) |
| GitHub Actions | [Tests workflow](./.github/workflows/tests.yml): passed on Ubuntu and Windows with Python 3.11 and 3.13 (2026-11-11); see the workflow for the latest result |
| Live DSH/AgentTeams integration | **Not yet validated** with a complete real multi-agent delivery |
| Tagged GitHub Release | **None yet**; public source access does not imply a stable release |

This is a workflow-and-evidence kit, not the AgentTeams runtime, a filesystem
sandbox, or a guarantee that AI-generated code is correct. See
[limitations](./docs/limitations.md) and the [real integration acceptance
checklist](./docs/recovery.md).

## What you get

| Area | Content |
| --- | --- |
| Team profile | `./templates/team-profile.yml` — four members, captain-only dispatch, K1–K4 gates, `approval="required"` |
| Project conventions | `./templates/AGENTS.example.md`, `./templates/TEAM_SPEC.template.md` |
| Cross-session handoff | `./templates/START-HERE.template.md`, `./templates/HANDOFF.template.md`, `./templates/DISCOVERY.template.md` |
| Team-manager skill | `./skills/agent-team-manager/SKILL.md` — teaches an agent to bootstrap, interview, consult and hand off |
| Optional governance checker | `./governance/` — post-hoc scope/review/delivery checks wired into task `verify` commands |
| Guide | `./docs/installation.md`, `./docs/workflow.md`, `./docs/configuration.md`, `./docs/limitations.md`, `./docs/recovery.md` |
| Governance reference | `./governance/README.md` — command contracts, evidence checks, repair/re-review procedures |
| Example | `./examples/demo-project/` — a small task-list app the templates are exercised on |

## What is intentionally not included

- No copy of BMAD skills, AgentTeams plugin code, or DSH files.
- No task scheduler, no agent runtime, no "automatic development".
- No claim that the process rules are technically unbypassable.

Install the dependencies from their official sources (see
[`docs/installation.md`](./docs/installation.md)).

## Requirements

| Dependency | Tested with | Notes |
| --- | --- | --- |
| DSH desktop | 0.2.2-rc.1 | Other versions are untested; the profile schema may differ |
| BMAD Method | 6.12.4 (`core` + `bmm`) | Installed through BMAD's own installer |
| AgentTeams plugin | `@nanmicoder/dsh-agent-teams` 0.1.29 | Supplies `agent_teams_*` tools and `approval="required"` |

BMAD Method, the AgentTeams plugin and the DSH source are MIT-licensed. This kit
bundles none of them; see [LICENSING.md](./LICENSING.md).

Check before you start:

```powershell
# BMAD skill count (expect the bmad-* directories you installed)
(Get-ChildItem ./.agents/skills -Directory).Count

# AgentTeams version in your DSH profile package list
Select-String -Path "<your DSH profile>/package.json" -Pattern 'dsh-agent-teams'
```

## Quick start

1. **Read the boundaries.** `./docs/limitations.md` explains what the gates can
   and cannot enforce.
2. **Install dependencies.** BMAD skills and the AgentTeams plugin, from their
   official sources.
3. **Copy the templates** into your project:
   `AGENTS.example.md` → `./AGENTS.md`, and the other templates into
   `./docs/team/`.
4. **Merge the team profile** from `./templates/team-profile.yml` into your DSH
   plugin configuration — back it up first, and restart DSH afterwards.
5. **Start a session** with the copy-paste prompt at the end of
   `./templates/START-HERE.template.md`.

## Working model

Three modes, one captain, four gates:

| Mode | Purpose | Effect |
| --- | --- | --- |
| A | Requirements interview | One decision per round; no team, no formal SPEC before K1 |
| B | Technical consulting | Read-only answers at any stage |
| C | Delivery execution | Teams created only after an explicit gate approval |

| Gate | Approval means |
| --- | --- |
| K1 | The interview is finished; a formal SPEC may be written |
| K2 | The SPEC is approved; architecture work may start |
| K3 | The architecture is approved; implementation and tests may start |
| K4 | The user accepts the delivered result |

The captain dispatches and reports; it never approves a professional gate for a
member. Reviews are assigned to someone other than the implementer.

See [`docs/workflow.md`](./docs/workflow.md) for the full flow and the evidence
each phase must produce.

## Repository layout

```
.
├── README.md
├── README.zh-CN.md
├── LICENSING.md
├── LICENSE
├── .gitignore
├── templates/
│   ├── team-profile.yml
│   ├── TEAM_SPEC.template.md
│   ├── AGENTS.example.md
│   ├── START-HERE.template.md
│   ├── HANDOFF.template.md
│   └── DISCOVERY.template.md
├── skills/
│   └── agent-team-manager/SKILL.md
├── governance/
│   ├── check.py
│   ├── roles.example.json
│   └── tests/test_check.py
├── docs/
│   ├── installation.md
│   ├── workflow.md
│   ├── configuration.md
│   └── limitations.md
└── examples/
    └── demo-project/
        ├── README.md
        ├── AGENTS.md
        ├── docs/team/DISCOVERY.md
        ├── src/todo.py
        └── tests/test_todo.py
```

## Governance checker (optional)

`./governance/check.py` verifies, after the fact, that a task's changed files stay
inside the role's write policy, that a reviewer differs from the implementer, and
that reviewed artifacts still match their recorded hashes. It is not a sandbox
and cannot block a write. Read [`docs/limitations.md`](./docs/limitations.md)
before relying on it.

The `delivery` command checks evidence consistency, not user acceptance.
See [`governance/README.md`](./governance/README.md) for command contracts,
exit codes and offline repair/re-review examples.
See [`docs/recovery.md`](./docs/recovery.md) for session recovery, delivery
sequence and the real integration acceptance checklist.

```powershell
python -m pytest ./governance/tests -q -p no:cacheprovider
```

## Frequently asked questions

**Does loading the team template run `setup` automatically?** No automatic
setup invocation is defined by this kit. The separately supplied
`setup-dsh-manual-test.ps1` is a one-time helper for an isolated manual
integration rehearsal, not a requirement for normal template use. Local DSH
hooks or custom startup commands, if configured separately, must be checked
independently. Do not rerun a rehearsal initializer during an active test:
it may overwrite test-scope and evidence state.

**Can I start a real software project with this?** Yes, for requirements,
architecture, and supervised development. Before relying on a four-agent
delivery workflow, verify the installed plugin/profile compatibility and
complete the [live acceptance checklist](./docs/recovery.md). User approval
at K1–K4 remains required.

**Can a new session automatically control an older team?** Not guaranteed.
Persist the project documents and use the supported recovery paths described
in [recovery](./docs/recovery.md); do not claim team takeover without runtime
confirmation.

## License

The original contents of this kit are licensed under the [MIT License](./LICENSE).
Copyright (c) 2026 Lai-yuanwei. Third-party software is not bundled; see
[`LICENSING.md`](./LICENSING.md) for dependency and trademark notes.
This is publicly available preview source, with no tagged stable GitHub Release yet. Live DSH/AgentTeams integration acceptance remains pending.