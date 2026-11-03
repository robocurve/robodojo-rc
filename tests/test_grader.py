"""The judge and hand graders, end to end through inspect_robots.eval on a three-camera stand-in."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest
from inspect_robots import Epochs, Scene, TrialRecord, resolve
from inspect_robots import eval as rl_eval
from inspect_robots.errors import ConfigError
from inspect_robots.mock import NoopPolicy

from robodojo_rc import SPEC_BY_KEY, AstraGrader, OperatorGrader, _workbench, make_task
from robodojo_rc.grader import (
    CAMERAS,
    JUDGE_VERSION,
    frame_at,
    frame_count,
    png_bytes,
    record_evidence,
    scene_rubric,
)
from robodojo_rc.tasks import workbench_rubric

from .fakes import ThreeCameraRig, frame_image
from .pngdecode import decode_data_url, decode_png

CAP_PEN = SPEC_BY_KEY["cap_pen"]


def reply(text: str, *, model: str = "gpt-6-astra", finish: str = "stop") -> dict[str, Any]:
    return {
        "model": model,
        "choices": [{"finish_reason": finish, "message": {"content": text}}],
        "usage": {"total_tokens": 42},
    }


class Judge:
    """Stands in for the OpenAI call: keeps every request, answers in turn (the last repeats)."""

    def __init__(self, *answers: str | Exception) -> None:
        self.answers = list(answers) or ["The cap is on.\nSCORE: 0.75"]
        self.requests: list[dict[str, Any]] = []

    def __call__(self, request: dict[str, Any]) -> dict[str, Any]:
        self.requests.append(request)
        answer = self.answers[min(len(self.requests), len(self.answers)) - 1]
        if isinstance(answer, Exception):
            raise answer
        return reply(answer)


def ungraded_run(log: Any) -> bool:
    """The run says some trials went unscored (wording differs between Inspect Robots versions)."""
    text = f"{log.error} {[s.error for s in log.samples]}"
    return log.status == "error" and ("not scored" in text or "ungraded" in text)


def run(
    grader: Any,
    *,
    steps: int = 61,
    rig: ThreeCameraRig | None = None,
    trials: int = 1,
    **kwargs: Any,
) -> Any:
    task = replace(make_task(CAP_PEN, max_steps=steps), epochs=Epochs(count=trials, reducer="mean"))
    rig = rig or ThreeCameraRig()
    with patch("inspect_robots.eval._git_commit", return_value=None):
        (log,) = rl_eval(
            task, NoopPolicy(), rig, sinks=[], store_actions=False, grader=grader, **kwargs
        )
    return log


def test_judge_scores_a_trial_like_the_published_judge() -> None:
    judge = Judge()
    log = run(AstraGrader(post=judge))
    (sample,) = log.samples
    assert sample.reduced["rubric_score"] == 0.75
    assert sample.operator_judgements == ("0.75",)
    assert sample.operator_notes == ("The cap is on.\nSCORE: 0.75",)
    (request,) = judge.requests
    assert request["model"] == "gpt-6-astra"
    assert request["reasoning_effort"] == "high"
    assert request["max_completion_tokens"] == 32768
    content = request["messages"][0]["content"]
    assert content[0]["text"] == _workbench.prompt_for(
        CAP_PEN.instruction, workbench_rubric(CAP_PEN)
    )
    assert "Score 0: Neither pen nor cap picked up." in content[0]["text"]
    # 61 steps make 62 frames: one per second of 30 fps playback (0, 30, 60) plus the last (61).
    labels = [part["text"] for part in content[1::2]]
    assert len(labels) == 12
    assert labels[0] == "Video time 0.000 s, initial frame, camera 'left_cam'"
    assert labels[4] == "Video time 1.000 s, sampled frame, camera 'right_cam'"
    assert labels[-1] == "Video time 2.033 s, final frame, camera 'top_cam'"
    images = [part["image_url"]["url"] for part in content[2::2]]
    for label, url in zip(labels, images, strict=True):
        seconds = float(label.split()[2])
        camera = label.split("'")[1]
        t = round(seconds * 30)
        assert (decode_data_url(url) == frame_image(t, camera)).all()
    (meta,) = sample.trial_metadata
    judged = meta["robodojo_judge"]
    assert judged["version"] == JUDGE_VERSION
    assert judged["rubric_revision"] == "02bd043f5381"
    assert judged["label"] == "adapted_v2_score_0_75"
    assert judged["evidence"]["selected_indices"] == [0, 30, 60, 61]
    assert judged["evidence"]["image_count"] == 12
    assert judged["request_sha256"] == _workbench.digest(request)
    assert judged["usage"] == {"total_tokens": 42}
    assert all("url" not in frame for frame in judged["frames"])
    json.dumps(meta)


def test_the_models_claim_of_success_is_not_evidence() -> None:
    judge = Judge("Nothing was picked up.\nSCORE: 0")
    log = run(AstraGrader(post=judge), rig=ThreeCameraRig(done_after=5))
    assert log.samples[0].reduced["rubric_score"] == 0.0
    assert judge.requests[0]["messages"][0]["content"][-2]["text"].startswith("Video time 0.167 s")


def test_judge_reads_frames_from_the_frame_store(tmp_path: Path) -> None:
    judge = Judge("SCORE: 1")
    log = run(AstraGrader(post=judge), steps=40, log_dir=str(tmp_path), store_frames=True)
    assert log.samples[0].reduced["rubric_score"] == 1.0
    content = judge.requests[0]["messages"][0]["content"]
    assert [p["text"] for p in content[1::2]][
        -1
    ] == "Video time 1.333 s, final frame, camera 'top_cam'"
    assert (decode_data_url(content[-1]["image_url"]["url"]) == frame_image(40, "top_cam")).all()


@pytest.mark.parametrize(
    ("answer", "rig", "why"),
    [
        (OSError("Astra API HTTP 500"), None, "Astra API HTTP 500"),
        ("SCORE: 0.3", None, "not an unambiguous rubric value"),
        ("I can't tell.", None, "exactly one rubric selection"),
        ("SCORE: 1", ThreeCameraRig(cameras=("top_cam", "left_cam")), "no right_cam image"),
    ],
)
def test_ungradable_trials_abstain(answer: str | Exception, rig: Any, why: str) -> None:
    log = run(AstraGrader(post=Judge(answer)), rig=rig)
    (sample,) = log.samples
    # Left out of the task score (never scored 0), and the run says why.
    assert sample.reduced.get("rubric_score") is None
    assert why in sample.trial_metadata[0]["grading_error"]
    assert sample.operator_judgements == (None,)
    assert ungraded_run(log)


def test_over_budget_evidence_is_left_for_a_person(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_workbench, "IMAGE_BUDGET", 100)
    log = run(AstraGrader(post=Judge()))
    assert "45 MB" in log.samples[0].trial_metadata[0]["grading_error"]


def test_a_recorded_rubric_score_is_kept() -> None:
    judge = Judge()
    record = TrialRecord(scene_id="cap_pen", epoch=0, seed=0, operator_judgement="0.5")
    AstraGrader(post=judge).grade(record, make_task(CAP_PEN).scenes[0])
    assert judge.requests == [] and record.operator_judgement == "0.5"


@pytest.mark.parametrize("verdict", ["y", "n", "partial", "0.3"])
def test_a_console_verdict_does_not_stop_the_judge(verdict: str) -> None:
    judge = Judge()
    log_records: list[TrialRecord] = []

    class Console(AstraGrader):
        def grade(self, record: TrialRecord, scene: Scene) -> None:
            record.operator_judgement = verdict  # what /y, /n or /p leaves on the record
            super().grade(record, scene)
            log_records.append(record)

    log = run(Console(post=judge))
    assert len(judge.requests) == 1
    assert log.samples[0].reduced["rubric_score"] == 0.75
    assert log_records[0].metadata["console_verdict"] == verdict


def test_judge_failure_after_a_console_verdict_is_still_flagged() -> None:
    class Console(AstraGrader):
        def grade(self, record: TrialRecord, scene: Scene) -> None:
            record.operator_judgement = "y"
            super().grade(record, scene)

    log = run(Console(post=Judge(OSError("Astra API HTTP 503"))))
    (sample,) = log.samples
    assert sample.operator_judgements == (None,)
    assert "HTTP 503" in sample.trial_metadata[0]["grading_error"]
    assert ungraded_run(log)


def test_an_ungraded_trial_is_left_out_of_the_mean_not_scored_zero() -> None:
    judge = Judge("SCORE: 1", OSError("Astra API HTTP 500"), "SCORE: 0.5")
    log = run(AstraGrader(post=judge), steps=4, trials=3)
    (sample,) = log.samples
    assert len(judge.requests) == 3
    assert sample.operator_judgements == ("1", None, "0.5")
    assert sample.reduced["rubric_score"] == 0.75  # (1 + 0.5) / 2, not (1 + 0 + 0.5) / 3
    assert ungraded_run(log)


def test_a_scene_without_a_rubric_is_not_graded(capsys: pytest.CaptureFixture[str]) -> None:
    record = TrialRecord(scene_id="x", epoch=0, seed=0)
    AstraGrader(post=Judge()).grade(record, Scene(id="x", instruction="Do it."))
    assert "is it a robodojo-rc task?" in record.metadata["grading_error"]
    assert "a person scores this trial" in capsys.readouterr().err


def test_no_steps_means_nothing_to_judge() -> None:
    record = TrialRecord(scene_id="cap_pen", epoch=0, seed=0)
    assert frame_count(record) == 0
    with pytest.raises(ValueError, match="no steps"):
        record_evidence(record)


def test_preflight_and_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("FINAL_JUDGE_ENV_FILE", raising=False)
    # Built from the registry (as --grader does), it refuses before any trial runs.
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        resolve("grader", "robodojo_astra")
    grader = AstraGrader()
    assert grader.name == "robodojo_astra"
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        grader.preflight()
    monkeypatch.setenv("FINAL_JUDGE_ENV_FILE", "/somewhere/keys.env")
    grader.preflight()
    monkeypatch.delenv("FINAL_JUDGE_ENV_FILE")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    grader.preflight()
    assert isinstance(resolve("grader", "robodojo_astra"), AstraGrader)
    AstraGrader(post=Judge()).preflight()  # an injected transport needs no key
    assert grader.config() == {"judge": JUDGE_VERSION, **_workbench.SETTINGS}


def test_published_trial_sampling() -> None:
    # A published Stack Bowls trial: 278 frames, judged at these indices (its audit record).
    assert _workbench.evidence_indices(278, 30.0) == [*range(0, 271, 30), 277]
    # The longest LLM trial, 900 steps: 31 time points, 93 images.
    assert len(_workbench.evidence_indices(901, 30.0)) * len(CAMERAS) == 93


@pytest.mark.parametrize("shape", [(5, 7), (5, 7, 1), (5, 7, 3), (5, 7, 4)])
def test_png_roundtrip(shape: tuple[int, ...]) -> None:
    image = np.arange(np.prod(shape), dtype=np.uint8).reshape(shape)
    decoded = decode_png(png_bytes(image))
    assert (decoded.reshape(image.shape) == image).all()


@pytest.mark.parametrize(
    ("image", "match"),
    [
        (np.zeros((4, 4, 3), dtype=np.float32), "uint8"),
        (np.zeros((4, 4, 2), dtype=np.uint8), "HxW"),
        (np.zeros(4, dtype=np.uint8), "HxW"),
    ],
)
def test_png_rejects(image: np.ndarray[Any, Any], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        png_bytes(image)


def test_frame_at_reads_inline_images() -> None:
    log_record: list[TrialRecord] = []

    class Keep(AstraGrader):
        def grade(self, record: TrialRecord, scene: Scene) -> None:
            log_record.append(record)

    run(Keep(post=Judge()), steps=3)
    (record,) = log_record
    assert frame_count(record) == 4
    assert (frame_at(record, 3)["left_cam"] == frame_image(3, "left_cam")).all()
    assert (frame_at(record, 0)["top_cam"] == frame_image(0, "top_cam")).all()
    assert scene_rubric(make_task(CAP_PEN).scenes[0])["revision"] == "02bd043f5381"


class Session:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.statuses: list[str | None] = []

    def write_line(self, text: str) -> None:
        self.lines.append(text)

    def status(self, line: str | None) -> None:
        self.statuses.append(line)


def answers(*replies: str | type[EOFError]) -> Any:
    queue = list(replies)

    def ask(prompt: str) -> str:
        item = queue.pop(0)
        if item is EOFError:
            raise EOFError
        assert isinstance(item, str)
        return item

    return ask


def test_operator_scores_through_eval() -> None:
    grader = OperatorGrader(input_fn=answers("0.3", "most", "0.5", "  both held  "))
    session = Session()
    grader.connect_session(session)  # type: ignore[arg-type]
    log = run(grader)
    (sample,) = log.samples
    assert sample.reduced["rubric_score"] == 0.5
    assert sample.operator_notes == ("both held",)
    assert sample.trial_metadata[0]["robodojo_rubric_revision"] == "02bd043f5381"
    assert session.statuses == [None]
    assert session.lines[0] == "rubric: Cap Pen (revision 02bd043f5381)"
    # The guidance decides between levels, so the person sees it, word for word.
    guidance = CAP_PEN.rubric.guidance.splitlines()
    assert session.lines[1 : 1 + len(guidance)] == [f"  {line}" for line in guidance]
    assert (
        "  0.75: Pen and cap touch while both are held in the air. No alignment requirement."
        in (session.lines)
    )
    assert "note: this trial hit the step limit" in session.lines
    assert session.lines.count("not one of this rubric's scores: '0.3'") == 1
    assert "not one of this rubric's scores: 'most'" in session.lines


@pytest.mark.parametrize(
    ("replies", "judgement", "note", "error"),
    [
        (("skip",), None, None, "scoring skipped at the terminal"),
        ((EOFError,), None, None, "no score given at the terminal (input closed)"),
        (("1", EOFError), "1", None, None),
        (("0", ""), "0", None, None),
    ],
)
def test_operator_answers(
    replies: tuple[Any, ...],
    judgement: str | None,
    note: str | None,
    error: str | None,
    capsys: Any,
) -> None:
    record = TrialRecord(scene_id="cap_pen", epoch=0, seed=0)
    OperatorGrader(input_fn=answers(*replies)).grade(record, make_task(CAP_PEN).scenes[0])
    assert record.operator_judgement == judgement
    assert record.operator_note == note
    assert record.metadata.get("grading_error") == error
    assert "rubric: Cap Pen" in capsys.readouterr().out


def test_operator_skip_is_flagged_not_averaged_away() -> None:
    log = run(OperatorGrader(input_fn=answers("1", "", "skip")), steps=4, trials=2)
    (sample,) = log.samples
    assert sample.operator_judgements == ("1", None)
    assert sample.reduced["rubric_score"] == 1.0
    assert ungraded_run(log)


def test_operator_keeps_a_rubric_score_and_needs_a_rubric(capsys: Any) -> None:
    record = TrialRecord(scene_id="cap_pen", epoch=0, seed=0, operator_judgement="1")
    OperatorGrader(input_fn=answers()).grade(record, make_task(CAP_PEN).scenes[0])
    assert record.operator_judgement == "1"
    record = TrialRecord(scene_id="cap_pen", epoch=0, seed=0, operator_judgement="y")
    OperatorGrader(input_fn=answers("0.2", "")).grade(record, make_task(CAP_PEN).scenes[0])
    assert record.operator_judgement == "0.2"
    assert record.metadata["console_verdict"] == "y"
    record = TrialRecord(scene_id="x", epoch=0, seed=0)
    OperatorGrader(input_fn=answers()).grade(record, Scene(id="x", instruction="Do it."))
    assert "no RoboDojo-RC rubric" in record.metadata["grading_error"]
    assert "robodojo_operator:" in capsys.readouterr().out
    assert isinstance(resolve("grader", "robodojo_operator"), OperatorGrader)
