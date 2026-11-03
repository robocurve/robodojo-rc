"""Score a trial with the rubric level its grader recorded.

A RoboDojo-RC trial scores one of its task's rubric levels, from 0 to 1. The ``robodojo_astra``
and ``robodojo_operator`` graders record the chosen level as the trial's judgement (for example
``"0.75"``); this scorer only reads it, so a saved log scores the same way again.

A trial with no valid rubric score is never scored 0: it was not graded, so a person scores it.
Inspect Robots versions that support abstentions get an abstained score. Earlier versions (0.58
to 0.60, which have none) get ``NotScored`` raised instead, which leaves the trial out of the
mean and marks the run's log as an error with the reason.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from inspect_robots import Score, Scorer, Target, TrialRecord
from inspect_robots.scorer import value_to_float

TARGET_KIND = "robodojo_rubric"
"""The scene target kind whose ``spec["scores"]`` lists the rubric's allowed scores."""


def _supports_abstaining() -> bool:
    try:
        return value_to_float(None) is None  # type: ignore[arg-type]
    except TypeError:
        return False


ABSTAINS = _supports_abstaining()
"""Whether the installed Inspect Robots accepts ``Score(value=None)`` as an abstention."""


class NotScored(Exception):
    """A trial without a valid rubric score, on an Inspect Robots without abstentions."""


@dataclass(frozen=True)
class _RubricScore:
    name: str = "rubric_score"

    def __call__(self, record: TrialRecord, target: Target | None) -> Score:
        reason = self._unscored(record, target)
        if reason is None:
            verdict = str(record.operator_judgement)
            return Score(value=float(verdict), explanation=f"rubric score {verdict.strip()}")
        if ABSTAINS:
            return Score(value=None, explanation=reason)  # type: ignore[arg-type]
        raise NotScored(reason)

    @staticmethod
    def _unscored(record: TrialRecord, target: Target | None) -> str | None:
        verdict = record.operator_judgement
        if verdict is None:
            error = record.metadata.get("grading_error")
            why = f"the judge failed: {error}" if error else "no rubric score recorded"
            return f"not scored ({why}); a person scores this trial"
        try:
            value = float(verdict)
        except ValueError:
            return f"not a rubric score: {verdict!r}"
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            return f"not a rubric score: {verdict!r}"
        allowed = target.spec.get("scores", ()) if target is not None else ()
        if target is not None and target.kind == TARGET_KIND and value not in allowed:
            return f"{verdict!r} is not one of this rubric's scores"
        return None


def rubric_score() -> Scorer:
    """The trial's recorded rubric score; a trial without a valid one is left out, not scored 0."""
    return _RubricScore()
