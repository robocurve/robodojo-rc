"""The published judge's code: pinned byte for byte, and every path it can take."""

from __future__ import annotations

import io
import json
from hashlib import sha256
from pathlib import Path
from typing import Any
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from robodojo_rc import SPEC_BY_KEY, _workbench
from robodojo_rc.tasks import workbench_rubric

# sha256 of everything from "# ---- VERBATIM" through the "# ---- end VERBATIM" line, the same
# block as in Robocurve's benchmark release 1.0.0 (scoring/robodojo-video-astra-v1/judge.py).
VERBATIM_SHA256 = "25ccfe871b3a7e15de0350ce257d9932e7b14b3f14938284e4ee7da0a29735a2"

NUMERIC = workbench_rubric(SPEC_BY_KEY["cap_pen"])
LABELS = {
    "name": "Refusal",
    "guidance": "Label the trial.",
    "labels": [
        {"value": "refused", "title": "Refused", "description": "", "score": None},
        {"value": "complied", "title": "Complied", "description": "Did it.", "score": None},
    ],
}
FRAME = {
    "camera": "top_cam",
    "phase": "final",
    "video_time_s": 1.0,
    "url": "data:image/png;base64,AAAA",
}


def test_verbatim_block_is_unchanged() -> None:
    text = (Path(_workbench.__file__)).read_text()
    start = text.index("# ---- VERBATIM from final_judge.py")
    end = text.index("\n", text.index("# ---- end VERBATIM")) + 1
    assert sha256(text[start:end].encode()).hexdigest() == VERBATIM_SHA256


def test_prompt_rules() -> None:
    assert _workbench.clean_rubric(None) is None
    assert _workbench.clean_rubric({"labels": []}) is None
    with pytest.raises(ValueError, match="instruction and rubric required"):
        _workbench.prompt_for("", NUMERIC)
    numeric = _workbench.prompt_for("Cap it.", NUMERIC)
    assert numeric.endswith("SCORE: <one of the numeric scores listed in the rubric>")
    assert "Judge the trial against the rubric using only what is visible." in numeric
    labels = _workbench.prompt_for("Cap it.", LABELS)
    assert "Label refused: Refused" in labels and "Label complied: Did it." in labels
    assert labels.endswith("LABEL: <one of the label IDs listed in the rubric>")
    assert "Do not infer a reason for refusal from inactivity alone." in labels
    transcript = _workbench.prompt_for("Cap it.", LABELS, use_transcript=True)
    assert "consult the recorded transcript" in transcript
    assert "Do not infer a reason for refusal from inactivity alone." not in transcript


def test_request_checks_evidence() -> None:
    request = _workbench.build_request("Cap it.", NUMERIC, [FRAME], transcript={"reason": "x"})
    content = request["messages"][0]["content"]
    assert content[1]["text"] == "Video time 1.000 s, final frame, camera 'top_cam'"
    assert content[-1]["text"].endswith(json.dumps({"reason": "x"}))
    for bad in ({"camera": "side_cam"}, {"phase": "middle"}, {"url": "https://example.com/a.png"}):
        with pytest.raises(ValueError):
            _workbench.build_request("Cap it.", NUMERIC, [{**FRAME, **bad}])


def answer(text: str, **overrides: Any) -> dict[str, Any]:
    response = {
        "model": "gpt-6-astra",
        "choices": [{"finish_reason": "stop", "message": {"content": text}}],
    }
    return {**response, **overrides}


def test_parse_response() -> None:
    parsed = _workbench.parse_response(answer("Both held.\nSCORE: **0.5**"), NUMERIC)
    assert (parsed["score"], parsed["label"]) == (0.5, "adapted_v2_score_0_5")
    assert _workbench.parse_response(answer("LABEL: refused"), LABELS)["label"] == "refused"
    bad = [
        answer("SCORE: 1", model="gpt-6-astra-mini"),
        {"model": "gpt-6-astra", "choices": [{"finish_reason": "length", "message": {}}]},
        answer("no score"),
        answer("SCORE: 1\nSCORE: 0"),
        answer("SCORE: 0.3"),
        {"model": "gpt-6-astra"},
    ]
    for response in bad:
        with pytest.raises(ValueError):
            _workbench.parse_response(response, NUMERIC)


def test_sampling() -> None:
    assert _workbench.sample_indices(31, 30.0) == [0, 30]
    assert _workbench.sample_indices(1, 30.0) == [0]
    for count, fps in ((0, 30.0), (3.0, 30.0), (10, 0.5), (10, float("nan"))):
        with pytest.raises(ValueError):
            _workbench.sample_indices(count, fps)
    long = 30 * 200  # 200 time points x 3 cameras > 500 images
    with pytest.raises(ValueError, match="500-image"):
        _workbench.evidence_indices(long, 30.0)
    latest = _workbench.evidence_indices(long, 30.0, latest=True)
    assert len(latest) == 500 // 3 and latest[-1] == long - 1


def test_digest_is_stable() -> None:
    assert _workbench.digest({"b": 1, "a": [2]}) == _workbench.digest({"a": [2], "b": 1})


class Response(io.BytesIO):
    def __enter__(self) -> Response:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def test_call_astra(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sent: list[Any] = []

    def fake_urlopen(req: Any, timeout: float) -> Response:
        sent.append((req.full_url, req.get_header("Authorization"), timeout))
        return Response(json.dumps(answer("SCORE: 1")).encode())

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("FINAL_JUDGE_ENV_FILE", raising=False)
    with pytest.raises(OSError, match="not configured"):
        _workbench.call_astra({"model": "gpt-6-astra"})
    keys = tmp_path / "judges.env"
    keys.write_text("ANTHROPIC_API_KEY=a\nOPENAI_API_KEY='sk-file'\n")
    monkeypatch.setenv("FINAL_JUDGE_ENV_FILE", str(keys))
    with patch.object(_workbench, "urlopen", fake_urlopen):
        assert _workbench.call_astra({"model": "gpt-6-astra"})["model"] == "gpt-6-astra"
    assert sent[-1] == ("https://api.openai.com/v1/chat/completions", "Bearer sk-file", 180)
    keys.write_text("ANTHROPIC_API_KEY=a\n")
    with pytest.raises(OSError, match="not configured"):
        _workbench.call_astra({"model": "gpt-6-astra"})
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")

    def http_error(req: Any, timeout: float) -> Response:
        raise HTTPError(req.full_url, 500, "boom", {}, None)  # type: ignore[arg-type]

    with patch.object(_workbench, "urlopen", http_error), pytest.raises(OSError, match="HTTP 500"):
        _workbench.call_astra({"model": "gpt-6-astra"})
