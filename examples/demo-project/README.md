# Demo project — task list

A deliberately small project used to exercise the kit's templates. It is not a
product; it exists so you can run the workflow end to end without inventing a
domain.

## What it demonstrates

- `./AGENTS.md` — a filled project-level agent rules file.
- `./docs/team/DISCOVERY.md` — an interview log with confirmed decisions and an
  example K1 record.
- `./src/todo.py` — the implementation `developer` would own.
- `./tests/test_todo.py` — the tests `qa` would run and extend.

Architecture and SPEC files are intentionally absent: in a real run they appear
only after K1 and K2.

## Try it

```powershell
python -m pytest ./tests -q -p no:cacheprovider
```

To use it as a team workspace:

1. Copy this directory somewhere outside the kit repository.
2. Copy the kit templates for `TEAM_SPEC.md`, `START-HERE.md` and `HANDOFF.md`
   into `./docs/team/`, replacing placeholders. Also copy the kit's
   `docs/recovery.md` as `./docs/team/RECOVERY.md`.
3. Ask the team for mode A and continue the interview in `DISCOVERY.md`.
4. Approve K1, then K2, then K3 in separate steps; create a team only in mode C.
5. Run the governance checker if you installed it under `./tools/governance/`.

## Boundaries

- The demo has no persistence, networking or UI. Keep it that way.
- Passing these tests is not K4; delivery acceptance is a human decision.
- This example is generic by design — no real product data belongs here.
