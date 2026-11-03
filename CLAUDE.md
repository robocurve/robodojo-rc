# robodojo-rc: agent guide

A standalone Inspect Robots benchmark plugin: six RoboDojo real-world tasks (release 1.0.0 of
Robocurve's RoboDojo-RC Tier 1), each one fixed setup with 20 mean-reduced trials, scored with a
pinned rubric by the published judge or by hand.

## Map

| Path | Contract |
|---|---|
| `src/robodojo_rc/specs.py` | Frozen `TaskSpec`s copied from the release: instruction, setup, reset, rubric (name, revision, guidance, levels), equipment, photo. The source of truth. |
| `src/robodojo_rc/tasks.py` | One `Scene` per task (rubric in `metadata["robodojo"]`, allowed scores in the `Target`), 20 trials, `max_steps` 900 by default, six registered factories. |
| `src/robodojo_rc/scoring.py` | `rubric_score`: reads the recorded rubric score; abstains when there is none or it is not a level. |
| `src/robodojo_rc/grader.py` | `robodojo_astra` (the published judge, frames from the trial record) and `robodojo_operator` (by hand). |
| `src/robodojo_rc/_workbench.py` | The published judge's code, byte for byte between the VERBATIM markers. Excluded from ruff and mypy; a test pins its hash. |
| `tools/task_pages.py` | Renders `docs/tasks/<key>.md` from the specs; a test fails when a page drifts. |

## Rules

- Never edit the instruction, rubric or anything between the VERBATIM markers to tidy them. They
  decide scores. A real change is a new task version, a new rubric revision and a new release,
  made in Robocurve's benchmark release first and copied here.
- Rubric scores 0 and 1 stay integers where the release has them: the judge prompt prints
  `Score 0`, not `Score 0.0`.
- Entry-point name, `@task` name and `Task.name` match exactly: `robodojo-rc/<key>`. Keep the
  WorldEvals catalog's `task_keys` in sync.
- Inspect Robots 0.59 is the floor: `rubric_score` raises `NotScored` there (0.59 and 0.60
  leave the trial out) and abstains on later versions. Keep the integration tests passing on
  0.59.0, the locked version and main (CI's `compat-min` and `compat-main`).
- Scene metadata is JSON-native; `metadata["rubric"]` is a non-blank string so Inspect Robots
  prints it above an operator prompt.

## Gates

```bash
uv sync --locked --extra dev && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest --cov
```

Mypy is strict and coverage stays at 100%. CI installs from `uv.lock`; run `uv lock` after
changing dependencies. `ci-ok` is the single required check.

## Public writing

No em dashes in prose, bold only for definition-list lead-ins, no decorative emoji, headers use
colons. Keep instruction and rubric text, commands, numbers and safety notes unchanged when
editing prose.
