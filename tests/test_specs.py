"""The six tasks as released: names, pinned revisions, rubric levels, equipment, photos."""

import math
import re
from pathlib import Path

import pytest

from robodojo_rc import RELEASE, SPEC_BY_KEY, SPECS, TaskSpec

ROOT = Path(__file__).resolve().parents[1]

# Pinned in Robocurve's benchmark release 1.0.0 (robodojo-rc/release.yaml).
REVISIONS = {
    "pack_and_pour_fruit": "79e63ce111e0",
    "stack_bowls": "e37caa41aa28",
    "store_in_safe": "ff1828950ed0",
    "cap_pen": "02bd043f5381",
    "stand_up_bottles": "3ef7c2f54948",
    "sort_objects": "b98515b26109",
}


def test_release_and_order() -> None:
    assert RELEASE == "1.0.0"
    assert [s.key for s in SPECS] == list(REVISIONS)
    assert list(SPEC_BY_KEY) == list(REVISIONS)
    assert [s.release_id for s in SPECS] == [
        "RD-pack-pour",
        "RD-stack-bowls",
        "RD-store-safe",
        "RD-cap-pen",
        "RD-bottles",
        "RD-classify",
    ]


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.key)
def test_spec(spec: TaskSpec) -> None:
    assert spec.version == 1
    assert spec.rubric.revision == REVISIONS[spec.key]
    assert spec.instruction.strip() == spec.instruction and spec.instruction
    assert spec.source_url.startswith("https://robodojo-benchmark.com/doc/real-tasks/")
    scores = spec.rubric.scores
    assert scores[0] == 0 and scores[-1] == 1
    assert list(scores) == sorted(set(scores)), "levels are distinct and lowest first"
    assert all(math.isfinite(s) and 0 <= s <= 1 for s in scores)
    assert len({level.value for level in spec.rubric.levels}) == len(scores)
    assert all(level.description for level in spec.rubric.levels)
    assert spec.equipment and all(e.url.startswith("https://") for e in spec.equipment)
    assert all(e.quantity >= 1 for e in spec.equipment)
    assert (ROOT / spec.photo).is_file()
    assert spec.photo in spec.setup and spec.photo in spec.reset
    assert "photos/setup-top.jpg" not in spec.setup + spec.reset


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.key)
def test_integer_end_scores_where_released(spec: TaskSpec) -> None:
    # The judge prompt prints "Score 0", so integer scores must stay integers.
    first, last = spec.rubric.levels[0].score, spec.rubric.levels[-1].score
    assert type(first) is int
    assert type(last) is (float if spec.key == "sort_objects" else int)


def test_sort_objects_keeps_robodojo_rubric_name() -> None:
    spec = SPEC_BY_KEY["sort_objects"]
    assert spec.name == "Sort Objects"
    assert spec.rubric.name == spec.source_title == "Classify Objects"


def test_revisions_are_short_hashes() -> None:
    assert all(re.fullmatch(r"[0-9a-f]{12}", r) for r in REVISIONS.values())


def test_version_fallback_for_uninstalled_source() -> None:
    from importlib import metadata, reload
    from unittest.mock import patch

    import robodojo_rc

    try:
        with patch.object(metadata, "version", side_effect=metadata.PackageNotFoundError):
            assert reload(robodojo_rc).__version__ == "0.0.0"
    finally:
        reload(robodojo_rc)
