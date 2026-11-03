# RoboDojo-RC Tier 1

Six of [RoboDojo](https://robodojo-benchmark.com/)'s real-world manipulation tasks, set up on
bimanual YAM arms, with the rubrics and the judge behind every
[published RoboDojo-RC Tier 1 score](https://robocurve.org/all-runs/?leaderboard=capability&benchmark=robodojo-rc-tier-1).
Built on [Inspect Robots](https://github.com/robocurve/inspect-robots) and listed in
[WorldEvals](https://github.com/robocurve/worldevals).

Each task has one fixed setup and 20 trials per model. A trial scores one level of the task's
rubric, from 0 to 1. A model's task score is the mean of its 20 trials, and its benchmark score
is the mean of its six task scores.

> [!NOTE]
> This release (1.0.0) covers LLM agents. VLA policies ran to a step cap in the published runs
> and their scores were still rising there, so their numbers are not comparable with these until
> VLAs have a stopping rule of their own.

## Quick start

```bash
pip install "robodojo-rc @ git+https://github.com/robocurve/robodojo-rc"
inspect-robots list tasks     # shows robodojo-rc/*
```

Try the pipeline without a robot on Inspect Robots' `cubepick` mock, scoring the trial by hand:

```bash
inspect-robots run --task robodojo-rc/cap_pen --policy random --embodiment cubepick \
  --grader robodojo_operator --epochs 1
```

The mock does not model these tasks. It only checks that the task, grader and scorer run.

## The tasks

| Task (`--task`) | RoboDojo task | Instruction (all the model is told) |
|---|---|---|
| [`robodojo-rc/pack_and_pour_fruit`](docs/tasks/pack_and_pour_fruit.md) | [Pack And Pour Fruit](https://robodojo-benchmark.com/doc/real-tasks/pack-and-pour-fruit/) | Place all the fruits into the blue bowl, then pour the fruits from the blue bowl into the large white bowl. |
| [`robodojo-rc/stack_bowls`](docs/tasks/stack_bowls.md) | [Stack Bowls](https://robodojo-benchmark.com/doc/real-tasks/stack-bowls/) | Stack the bowls on the table. |
| [`robodojo-rc/store_in_safe`](docs/tasks/store_in_safe.md) | [Store In Safe](https://robodojo-benchmark.com/doc/real-tasks/store-in-safe/) | Place all the objects into the safe, then close the safe. |
| [`robodojo-rc/cap_pen`](docs/tasks/cap_pen.md) | [Cap Pen](https://robodojo-benchmark.com/doc/real-tasks/cap-pen/) | Pick up the pen and the pen cap, then put the cap on the pen. |
| [`robodojo-rc/stand_up_bottles`](docs/tasks/stand_up_bottles.md) | [Stand Up Bottles](https://robodojo-benchmark.com/doc/real-tasks/stand-up-bottles/) | Stand all three bottles upright. |
| [`robodojo-rc/sort_objects`](docs/tasks/sort_objects.md) | [Classify Objects](https://robodojo-benchmark.com/doc/real-tasks/classify-objects/) | Classify the two types of objects on the table and place them into the two baskets. |

Each task page has the setup photo, setup and reset steps, the equipment with the products the
published runs used, and the rubric with its pinned revision.

## Scoring

Pick a grader with `--grader`. Both record the chosen rubric score, which the `rubric_score`
scorer reads.

- **`robodojo_astra`:** the judge behind every published score. GPT-6 Astra (reasoning effort
  high) sees the three cameras (`top_cam`, `left_cam`, `right_cam`) at one frame per second of
  30 fps playback plus the final frame, with the instruction and the task's rubric, and picks one
  rubric score. Needs `OPENAI_API_KEY`. The model's own claim to be done is not evidence.
- **`robodojo_operator`:** shows the rubric and asks the person at the terminal for a score.

A trial the judge cannot grade (an API error, an answer without a valid score) is left ungraded
with the reason in the log, and abstains instead of scoring 0. Score it by hand from the video.
Inspect Robots' own `operator` and `vlm` graders record success or failure, which is not a rubric
score, so those trials abstain too.

Differences from the published grades: the published judge read its frames from H.264 clips
rendered for review, while `robodojo_astra` reads the same frames from the trial record before
compression. The published judge switched to JPEG when a trial's PNG frames passed 45 MB; this
grader leaves such a trial for a person instead. A 900-step trial sends at most 93 images.

## Comparable runs

Scores compare when they come from the same release and protocol. The published runs used:

- **Robot:** I2RT YAM bimanual arms with Inspect Robots 0.58.0 and inspect-robots-yam 0.36.0,
  end-effector position targets at 25% of maximum speed, motor temperature cutoff 65 °C.
- **Agent:** inspect-robots-agent 0.26.0 with two later changes (service tiers and Responses
  caching, both in 0.28.0). At most 40 LLM calls and 900 control steps per trial, no time
  limit. Three cameras (overhead and both wrists) at 224 x 224 with rendered depth, images every
  step, the last 2 kept.
- **Models:** GPT-6.1 Terra and GPT-5.6 Terra (effort max, fast service tier) and Kimi K3.1 Pro
  (effort high, through OpenRouter) used exactly these rubric revisions. Older published runs
  used other revisions on some tasks or recorded none.
- **Trials:** 20 per model per task, models taking turns so no model runs twice in a row on a
  rig.
- **Counted:** every trial that ran, including model give-ups, the 40-call limit, model errors
  (scored from the video), and overheats during the model's own trial when the rig started cool.
- **Set aside and rerun with the same model:** infrastructure failures (API, network, motor bus
  or camera), overheats from heat left by the previous trial, batches restarted after a setup
  change, and interrupted tries.

An LLM agent on a YAM rig, from a rig directory with `./run` and `config.ini`:

```bash
pip install "robodojo-rc @ git+https://github.com/robocurve/robodojo-rc"   # into the rig venv
./run --task robodojo-rc/cap_pen --epochs 20 --grader robodojo_astra --store-frames \
  -E auto_start=false -E control_interface=eef_pos -E report_joint_eff=true -E motor_temp_limit=65 \
  --policy agent -P model=openai/gpt-6.1-terra -P wire=responses -P effort=max -P service_tier=fast \
  -P max_llm_calls=40 -P max_speed_frac=0.25 -P images=always -P image_horizon=2 -P depth=render
```

`--store-frames` keeps camera frames on disk, so the judge loads only the frames it samples.
`-E auto_start=false` pauses before each trial so the scene can be reset after the arms reach
home. Keep clear of the arms while they move.

## Differences from RoboDojo

RoboDojo runs these tasks on its own robots (Piper X and ARX X5) with RoboDojo's scoring. Here
they run on YAM arms with the objects in each task's equipment list, a reference setup photo, and
rubrics adapted with more partial-credit levels. Sort Objects is RoboDojo's Classify Objects; the
judge's rubric keeps that name.

## Development

Inspect Robots comes from PyPI (`inspect-robots>=0.58`). After changing dependencies, run
`uv lock` and commit `uv.lock`.

```bash
uv sync --locked --extra dev && uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest --cov
```

Coverage must be 100%, mypy is strict, and Ruff D1 requires contract docstrings for public
modules, classes, and functions. Task pages are generated from `specs.py` with
`uv run python tools/task_pages.py`. See [CLAUDE.md](CLAUDE.md) for repository conventions.

## Citation

```bibtex
@software{robodojo_rc,
  author  = {Robocurve},
  title   = {RoboDojo-RC Tier 1: RoboDojo real-world tasks with pinned rubrics and judge},
  year    = {2026},
  url     = {https://github.com/robocurve/robodojo-rc},
  version = {1.0.0},
  license = {MIT}
}
```

Please also cite [RoboDojo](https://robodojo-benchmark.com/), where the tasks come from.

[MIT license](LICENSE). Task instructions and descriptions are adapted from RoboDojo; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
