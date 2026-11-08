# DISCOVERY — demo task list

Filled example for the kit. It shows the level of detail expected after two
interview rounds, and a K1 record with the user's own words.

**Last updated:** 2026-01-15
**Interview round:** 2
**Current module:** task list
**K1 status:** approved on 2026-01-15

## 1. Product goal

A tiny in-memory task list used to demonstrate the team workflow. The user can
add a task, complete it, and list what is still pending. Nothing is persisted;
the demo is not a product.

## 2. Users and jobs

| User | Job to be done | Evidence |
| --- | --- | --- |
| demo user | keep a short list of tasks and see what is left | round 1 |

## 3. Confirmed decisions

| # | Decision | Rationale | Round | Date |
| --- | --- | --- | --- | --- |
| 1 | In-memory only, no storage | the demo must stay small and dependency-free | 1 | 2026-01-15 |
| 2 | Reject empty task titles | avoids meaningless entries | 1 | 2026-01-15 |
| 3 | Tasks are completed by index | simplest API for a demo | 2 | 2026-01-15 |

## 4. Constraints

- Technical: Python standard library only; no third-party dependencies.
- Schedule: none; the demo is illustrative.
- Compliance or data: no personal data, no network.
- Explicit non-goals: persistence, priorities, due dates, UI, sync.

## 5. Open questions

| # | Question | Why it matters | Owner |
| --- | --- | --- | --- |
| 1 | Should completing an already-done task raise? | affects API clarity | user |

## 6. Alternatives considered

| Option | Pros | Cons | Status |
| --- | --- | --- | --- |
| JSON file storage | survives restarts | adds I/O and error paths | rejected |
| In-memory list | smallest surface | nothing survives the process | chosen |

## 7. Risks

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| demo grows into a real product | medium | scope creep | keep non-goals explicit |
| tests overfit the implementation | low | weak evidence | qa writes independent probes |

## 8. Next round

Question: "Should completing an already-completed task raise an error, or be a
no-op?" A good answer names one behaviour and the reason.

## 9. K1 record

- Approved by: demo user
- Date: 2026-01-15
- User's words: "Requirements look complete — write the spec."
- What it unlocks: the analyst may write `./docs/planning/SPEC.md`.