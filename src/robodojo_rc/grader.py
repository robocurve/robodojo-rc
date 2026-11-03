"""Graders: the judge behind every published score, and scoring by hand at the terminal.

``robodojo_astra`` grades a trial the way every published RoboDojo-RC Tier 1 trial was graded.
GPT-6 Astra (reasoning effort high) sees the three cameras at one frame per second of 30 fps
playback plus the final frame, with the task instruction and its rubric, and picks one rubric
score. The prompt, request and answer checks are the published judge's own code
(``_workbench.py``). The published grades read those frames from the H.264 clips rendered for
review; this grader reads the same frames from the trial record, before compression.

``robodojo_operator`` shows the rubric and asks the person at the terminal for a score.

Both record the score as the trial's judgement (``"0.75"``) for the ``rubric_score`` scorer. A
trial the judge cannot grade is left ungraded with ``metadata["grading_error"]`` and abstains.
"""

from __future__ import annotations

import base64
import os
import struct
import sys
import zlib
from collections.abc import Callable, Mapping
from hashlib import sha256
from typing import TYPE_CHECKING, Any

import numpy as np
from inspect_robots import grader
from inspect_robots.errors import ConfigError
from inspect_robots.transcript import operator_event

from robodojo_rc import _workbench

if TYPE_CHECKING:
    import numpy.typing as npt
    from inspect_robots import OperatorSession, Scene, TrialRecord

JUDGE_VERSION = "robodojo-workbench-astra-high-1fps-v1"
"""The published judge's version, recorded with every grade."""

PLAYBACK_FPS = 30.0
"""Playback rate of the review clips the judge's timeline counts in (one recorded frame each)."""

CAMERAS = tuple(camera + "_cam" for camera in _workbench.CAMERAS)
"""The three cameras the judge sees: ``left_cam``, ``right_cam`` and ``top_cam``."""

_NOTE_LIMIT = 2000
_ERROR_LIMIT = 500


def png_bytes(image: npt.NDArray[np.uint8]) -> bytes:
    """Encode an 8-bit grey, RGB or RGBA image as a PNG, losslessly."""
    array = np.asarray(image)
    if array.dtype != np.uint8:
        raise ValueError(f"camera frames must be uint8, got {array.dtype}")
    if array.ndim == 2:
        array = array[:, :, None]
    if array.ndim != 3 or array.shape[2] not in (1, 3, 4):
        raise ValueError(f"camera frames must be HxW, HxWx3 or HxWx4, got {array.shape}")
    height, width, channels = array.shape
    color_type = {1: 0, 3: 2, 4: 6}[channels]
    rows = array.reshape(height, width * channels)
    raw = np.concatenate([np.zeros((height, 1), dtype=np.uint8), rows], axis=1).tobytes()

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )


def frame_count(record: TrialRecord) -> int:
    """How many frames the trial's video has: one per step, plus the frame after the last step."""
    return len(record.steps) + 1 if record.steps else 0


def frame_at(record: TrialRecord, index: int) -> Mapping[str, npt.NDArray[np.uint8]]:
    """The camera images of video frame ``index``, read from the record or its frame store.

    Frame ``t`` is what the cameras saw before step ``t``; the last frame is what they saw after
    the last step. This is the order ``inspect-robots video`` plays stored frames in.
    """
    steps = record.steps
    if index < len(steps):
        inline, refs = steps[index].observation.images, steps[index].image_refs
    else:
        last = steps[-1]
        inline, refs = last.result.observation.images, last.result_image_refs
    if inline:
        return inline
    return {camera: ref.load() for camera, ref in (refs or {}).items()}


def record_evidence(record: TrialRecord) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """The judge's frames for one trial, in the published judge's format, and an audit of them.

    Samples one frame per second of 30 fps playback plus the final frame (the judge's own
    ``evidence_indices``), all three cameras at each time point, encoded as PNG.
    """
    count = frame_count(record)
    if count == 0:
        raise ValueError("the trial recorded no steps, so there is nothing to judge")
    indices = _workbench.evidence_indices(count, PLAYBACK_FPS)
    frames: list[dict[str, Any]] = []
    image_bytes = 0
    for index in indices:
        images = frame_at(record, index)
        for camera in CAMERAS:
            if camera not in images:
                raise ValueError(f"no {camera} image in frame {index}; the judge needs all three")
            raw = png_bytes(images[camera])
            image_bytes += len(raw)
            phase = "final" if index == count - 1 else "initial" if index == 0 else "sampled"
            frames.append(
                {
                    "camera": camera,
                    "index": index,
                    "video_time_s": index / PLAYBACK_FPS,
                    "phase": phase,
                    "sha256": sha256(raw).hexdigest(),
                    "url": "data:image/png;base64," + base64.b64encode(raw).decode(),
                }
            )
    if image_bytes > _workbench.IMAGE_BUDGET:
        raise ValueError("grading images exceed the judge's 45 MB budget")
    frames.sort(key=lambda frame: (frame["index"], frame["camera"]))
    audit = {
        "source": "trial_record",
        "fps": PLAYBACK_FPS,
        "frame_count": count,
        "selected_indices": indices,
        "image_count": len(frames),
        "encoding": "png",
        "image_bytes": image_bytes,
    }
    return frames, audit


def scene_rubric(scene: Scene) -> dict[str, Any]:
    """The task's rubric as the judge reads it, from the scene a RoboDojo-RC task built."""
    rubric = (scene.metadata.get("robodojo") or {}).get("rubric")
    if not isinstance(rubric, dict) or not rubric.get("labels"):
        raise ValueError(f"scene {scene.id!r} has no RoboDojo-RC rubric; is it a robodojo-rc task?")
    return rubric


def _one_line(exc: Exception) -> str:
    text = " ".join(str(exc).split()) or type(exc).__name__
    return text[:_ERROR_LIMIT]


class AstraGrader:
    """The published judge: GPT-6 Astra picks one rubric score from the trial's camera frames."""

    name = "robodojo_astra"

    def __init__(self, post: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> None:
        """Send judge requests with ``post`` (the judge's own OpenAI call by default)."""
        self._post = post or _workbench.call_astra

    def config(self) -> dict[str, Any]:
        """The judge settings recorded in the run's log."""
        return {"judge": JUDGE_VERSION, **_workbench.SETTINGS}

    def preflight(self) -> None:
        """Refuse to start a run whose trials the judge could not grade (no OpenAI key)."""
        if self._post is not _workbench.call_astra:
            return
        if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("FINAL_JUDGE_ENV_FILE")):
            raise ConfigError(
                "robodojo_astra needs OPENAI_API_KEY: the judge is OpenAI's gpt-6-astra "
                "(or grade by hand with --grader robodojo_operator)"
            )

    def grade(self, record: TrialRecord, scene: Scene) -> None:
        """Record the judge's rubric score, or leave the trial ungraded with the reason.

        A judgement already on the record (from the console) is kept. The model's own claim to
        be done is not evidence: every trial is judged from its frames.
        """
        if record.operator_judgement is not None:
            return
        try:
            rubric = scene_rubric(scene)
            frames, evidence = record_evidence(record)
            request = _workbench.build_request(scene.instruction, rubric, frames)
            response = self._post(request)
            parsed = _workbench.parse_response(response, rubric)
        except Exception as exc:  # post-rollout: an ungraded trial beats a crashed run
            reason = _one_line(exc)
            print(f"robodojo_astra: {reason}; a person scores this trial", file=sys.stderr)
            record.metadata["grading_error"] = reason
            return
        judgement = str(parsed["score"])
        note = parsed["explanation"].strip()[:_NOTE_LIMIT]
        record.operator_judgement = judgement
        record.operator_note = note
        record.metadata["robodojo_judge"] = {
            "version": JUDGE_VERSION,
            "settings": _workbench.SETTINGS,
            "rubric_revision": rubric.get("revision"),
            "label": parsed["label"],
            "request_sha256": _workbench.digest(request),
            "evidence": evidence,
            "frames": [{k: v for k, v in f.items() if k != "url"} for f in frames],
            "usage": response.get("usage"),
        }
        record.events.append(
            operator_event(t=len(record.steps), verdict=judgement, source=self.name, note=note)
        )


class OperatorGrader:
    """Score by hand: show the rubric and ask the person at the terminal for one of its scores."""

    name = "robodojo_operator"

    def __init__(
        self,
        session: OperatorSession | None = None,
        *,
        input_fn: Callable[[str], str] = input,
    ) -> None:
        """Ask through ``input_fn``, writing through the run's session when one is connected."""
        self._session = session
        self._input = input_fn

    def connect_session(self, session: OperatorSession) -> None:
        """Adopt the run's session so the prompt shares the run's terminal."""
        self._session = session

    def _say(self, line: str) -> None:
        if self._session is not None:
            self._session.write_line(line)
        else:
            print(line)

    def grade(self, record: TrialRecord, scene: Scene) -> None:
        """Record the score the person picks; ``skip`` or closed input leaves the trial ungraded."""
        if record.operator_judgement is not None:
            return
        if self._session is not None:
            self._session.status(None)
        try:
            rubric = scene_rubric(scene)
        except ValueError as exc:
            record.metadata["grading_error"] = _one_line(exc)
            self._say(f"robodojo_operator: {exc}")
            return
        self._say(f"rubric: {rubric['name']} (revision {rubric.get('revision')})")
        for label in rubric["labels"]:
            self._say(f"  {label['score']}: {label['description']}")
        if record.truncated and record.termination_reason == "max_steps":
            self._say("note: this trial hit the step limit")
        scores = [label["score"] for label in rubric["labels"]]
        prompt = f"score? [{'/'.join(str(s) for s in scores)}, or skip] "
        while True:
            try:
                answer = self._input(prompt).strip()
            except EOFError:
                return
            if answer.lower() == "skip":
                return
            try:
                chosen = [s for s in scores if s == float(answer)]
            except ValueError:
                chosen = []
            if chosen:
                break
            self._say(f"not one of this rubric's scores: {answer!r}")
        try:
            note = self._input("note (optional): ").strip() or None
        except EOFError:
            note = None
        judgement = str(chosen[0])
        record.operator_judgement = judgement
        record.operator_note = note
        record.metadata["robodojo_rubric_revision"] = rubric.get("revision")
        record.events.append(
            operator_event(t=len(record.steps), verdict=judgement, source=self.name, note=note)
        )


@grader("robodojo_astra")
def astra_grader() -> AstraGrader:
    """The published RoboDojo-RC judge (GPT-6 Astra, high); needs ``OPENAI_API_KEY``."""
    return AstraGrader()


@grader("robodojo_operator")
def operator_grader() -> OperatorGrader:
    """Score each trial by hand at the terminal, choosing one of the task's rubric scores."""
    return OperatorGrader()
