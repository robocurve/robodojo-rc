"""Registration, task shape and scene metadata."""

import json
from importlib.metadata import entry_points

import pytest
from inspect_robots import Epochs, resolve

from robodojo_rc import K_TRIALS, MAX_STEPS, SPECS, TARGET_KIND, TASK_FACTORIES, TaskSpec, make_task
from robodojo_rc.tasks import rubric_text, workbench_rubric


def test_entry_points_match_factories() -> None:
    tasks = {ep.name: ep.value for ep in entry_points(group="inspect_robots.tasks")}
    ours = {name: value for name, value in tasks.items() if name.startswith("robodojo-rc/")}
    assert ours == {f"robodojo-rc/{k}": f"robodojo_rc.tasks:{k}" for k in TASK_FACTORIES}
    graders = {ep.name: ep.value for ep in entry_points(group="inspect_robots.graders")}
    assert graders["robodojo_astra"] == "robodojo_rc.grader:astra_grader"
    assert graders["robodojo_operator"] == "robodojo_rc.grader:operator_grader"
    scorers = {ep.name: ep.value for ep in entry_points(group="inspect_robots.scorers")}
    assert scorers["rubric_score"] == "robodojo_rc.scoring:rubric_score"


@pytest.mark.parametrize("key", list(TASK_FACTORIES))
def test_registered_task(key: str) -> None:
    task = resolve("task", f"robodojo-rc/{key}")
    assert task.name == f"robodojo-rc/{key}"
    assert task.max_steps == MAX_STEPS == 900
    assert task.epoch_spec == Epochs(count=K_TRIALS, reducer="mean")
    assert [s.name for s in task.scorers] == ["rubric_score", "episode_length"]
    assert TASK_FACTORIES[key](max_steps=3600).max_steps == 3600


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.key)
def test_scene(spec: TaskSpec) -> None:
    (scene,) = make_task(spec).scenes
    assert scene.id == spec.key
    assert scene.instruction == spec.instruction
    assert scene.target is not None and scene.target.kind == TARGET_KIND
    assert scene.target.spec == {"scores": list(spec.rubric.scores)}
    json.dumps(dict(scene.metadata))  # logs need JSON-native metadata
    assert scene.metadata["rubric"] == rubric_text(spec)
    assert scene.metadata["robodojo"]["rubric"] == workbench_rubric(spec)
    assert scene.metadata["release_id"] == spec.release_id
    assert len(scene.metadata["equipment"]) == len(spec.equipment)


def test_workbench_rubric_shape() -> None:
    spec = SPECS[3]
    rubric = workbench_rubric(spec)
    assert rubric["name"] == "Cap Pen" and rubric["revision"] == "02bd043f5381"
    assert rubric["labels"][0] == {
        "value": "adapted_v2_score_0",
        "title": "0",
        "description": "Neither pen nor cap picked up.",
        "score": 0,
    }
    assert rubric_text(spec).splitlines()[-1] == (
        "1: Cap successfully placed onto the pen and remains attached at trial end."
    )
