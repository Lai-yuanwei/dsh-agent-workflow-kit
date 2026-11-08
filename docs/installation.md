# Installation

## 1. Prerequisites

| Dependency | Tested version | Check |
| --- | --- | --- |
| DSH desktop | 0.2.2-rc.1 | `dsh --version` or the About dialog |
| BMAD Method (`core`, `bmm`) | 6.12.4 | the `bmad-*` skill directories under `./.agents/skills/` |
| AgentTeams plugin | `@nanmicoder/dsh-agent-teams` 0.1.29 | your DSH profile's package list |

Versions other than the ones above are untested. This kit does not claim
compatibility with every DSH release; check the profile schema before reusing it.

## 2. Prepare your project

Copy the templates into the project root:

```text
./AGENTS.md                                  <- templates/AGENTS.example.md
./docs/team/START-HERE.md                    <- templates/START-HERE.template.md
./docs/team/TEAM_SPEC.md                     <- templates/TEAM_SPEC.template.md
./docs/team/HANDOFF.md                       <- templates/HANDOFF.template.md
./docs/team/DISCOVERY.md                     <- templates/DISCOVERY.template.md
```

Replace every `{{PLACEHOLDER}}` and delete the template notes. Keep paths
relative to the project root.

## 3. Install the team profile

The profile is a YAML block in your DSH plugin configuration, under the
AgentTeams section (`agent-teams` → `config` → `profiles`). The exact file
location depends on your DSH profile; resolve it from your environment or
DSH's configuration command — do not hard-code a machine path here.

1. **Back up first.** Copy the current configuration file to
   `config.backup-<YYYYMMDD-HHmm>` and keep it outside version control.
2. **Merge, don't overwrite.** Add the `profiles:` block from
   `./templates/team-profile.yml` under the existing `profiles:` key. If the key
   already exists, merge the entries; do not replace the whole file.
3. **Keep names unique.** Rename `dev-team-default` if your workspace already has an
   unarchived team with that name. Team names are workspace-wide.
4. **Restart DSH.** Profiles are read at runtime. Existing teams keep the prompt
   snapshot they were created with; only new teams see the edited profile.

## 4. Verify the installation

1. Start a new session and run the bootstrap prompt from
   `./templates/START-HERE.template.md` §10.
2. `agent_teams_status` should report that this session leads no team.
3. Optional offline schema check, using the installed plugin:

```js
// Run from a directory where the plugin is resolvable.
const path = require("path");
const { resolveTeamProfile } = require(path.join(
  process.env.DSH_PROFILE_DIR || "<your DSH profile directory>",
  "node_modules/@nanmicoder/dsh-agent-teams/lib/profiles.js"
));
// load the merged config object, then:
console.log(resolveTeamProfile(config.profiles, "dev-team-default", 8));
```

A successful result lists the four members and `taskPlanning: captain`.
If it throws, the message names the invalid key or member.

4. Run the checker tests when you plan to use the governance component:

```powershell
python -m pytest ./governance/tests -q -p no:cacheprovider
```

## 5. Starting a delivery team

Only after the required gates are approved:

```text
agent_teams_create(
  name="<project>-dev-<YYYYMMDD-HHmm>",
  profile="dev-team-default",
  approval="required"
)
```

The plan is staged; review it as the user and approve explicitly. Nothing starts
before that approval.

## 6. Backup and rollback

- **Before editing config:** copy the file to `config.backup-<timestamp>`.
- **Rollback:** restore the backup, restart DSH. Teams created with the new
  profile keep their snapshot; archive them instead of editing their state.
- **Uninstall:** remove the profile entry (or restore the backup), restart DSH,
  and archive teams that are no longer used.

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Profile missing from the session prompt | DSH was not restarted, or the block is at the wrong level | Fix the nesting, restart |
| `unknown profile key` | A key outside the allowed set was added | See `./docs/configuration.md` §2 |
| `provider requires model` | Member route override incomplete | Provide both, or neither |
| Team name rejected | Name already used by an unarchived team | Use a dated, unique name |
| Plan staged but nothing runs | `approval="required"` waits for the user | Ask the user to approve |
| Existing team ignores the new prompt | Profiles are snapshotted per team | Archive and create a new team |