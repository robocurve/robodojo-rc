# Changelog

## 1.0.1

Fixes from an independent review; the tasks, rubrics and judge prompt are unchanged.

- Requires Inspect Robots 0.59 or later. On 0.58 a trial without a rubric score crashed the run.
- A console verdict (`/y`, `/n`, `/p`) no longer stops `robodojo_astra` or `robodojo_operator`
  from grading the trial; it is kept in `metadata["console_verdict"]`.
- `robodojo_operator` shows the rubric guidance as well as the levels, and records why a trial
  was skipped so the run is marked as having unscored trials.
- `robodojo_astra` refuses to build without an OpenAI key, so a run fails before its first
  trial rather than after it (Inspect Robots 0.59 and 0.60 do not call `preflight()`).
- README: how Inspect Robots' counting differs from the protocol (errored and set-aside trials).
- CI runs the tests against Inspect Robots 0.59.0 and main as well as the locked 0.60.0.

## 1.0.0

- First release: the six RoboDojo-RC Tier 1 tasks from Robocurve's benchmark release 1.0.0
  (LLM agents), the `robodojo_astra` judge and `robodojo_operator` graders, and the
  `rubric_score` scorer.
