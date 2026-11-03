"""rubric_score reads the recorded level; anything else is left out, never scored 0."""

import pytest
from inspect_robots import Target, TrialRecord

from robodojo_rc import TARGET_KIND, rubric_score, scoring

LEVELS = Target(kind=TARGET_KIND, spec={"scores": [0, 0.2, 0.5, 0.75, 1]})


def record(verdict: str | None, **metadata: str) -> TrialRecord:
    return TrialRecord(
        scene_id="cap_pen", epoch=0, seed=0, operator_judgement=verdict, metadata=dict(metadata)
    )


@pytest.mark.parametrize(
    ("verdict", "target", "expected"),
    [
        ("0.75", LEVELS, 0.75),
        ("1", LEVELS, 1.0),
        ("0", LEVELS, 0.0),
        (" 0.2 ", LEVELS, 0.2),
        ("0.3", None, 0.3),  # without the rubric target, any score in [0, 1]
        ("0.3", Target(kind="other"), 0.3),
    ],
)
def test_scores(verdict: str, target: Target | None, expected: float) -> None:
    scorer = rubric_score()
    assert scorer.name == "rubric_score"
    score = scorer(record(verdict), target)
    assert score.value == expected
    assert score.explanation == f"rubric score {verdict.strip()}"


UNSCORED = [
    (record("0.3"), "is not one of this rubric's scores"),
    (record("y"), "not a rubric score: 'y'"),  # success/failure graders are not rubric scores
    (record("nan"), "not a rubric score"),
    (record("1.5"), "not a rubric score"),
    (record(None, grading_error="Astra API HTTP 500"), "the judge failed: Astra API HTTP 500"),
    (record(None), "no rubric score recorded"),
]


@pytest.mark.parametrize(("trial", "why"), UNSCORED)
def test_unscored_abstains_when_supported(
    trial: TrialRecord, why: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(scoring, "ABSTAINS", True)
    score = rubric_score()(trial, LEVELS)
    assert score.value is None
    assert why in (score.explanation or "")


@pytest.mark.parametrize(("trial", "why"), UNSCORED)
def test_unscored_is_left_out_on_older_inspect_robots(
    trial: TrialRecord, why: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(scoring, "ABSTAINS", False)
    with pytest.raises(scoring.NotScored, match=why.replace("(", r"\(")):
        rubric_score()(trial, LEVELS)


def test_detects_abstention_support(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scoring, "value_to_float", lambda value: None)
    assert scoring._supports_abstaining() is True

    def old(value: object) -> float:
        return float(value)  # type: ignore[arg-type]

    monkeypatch.setattr(scoring, "value_to_float", old)
    assert scoring._supports_abstaining() is False
