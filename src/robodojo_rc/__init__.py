"""RoboDojo-RC Tier 1: six RoboDojo real-world tasks with pinned rubrics and the published judge.

Importing the package registers the six tasks (``robodojo-rc/<key>``), the ``robodojo_astra`` and
``robodojo_operator`` graders and the ``rubric_score`` scorer. Installed entry points make them
discoverable to Inspect Robots without importing.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from robodojo_rc.grader import AstraGrader, OperatorGrader, astra_grader, operator_grader
from robodojo_rc.scoring import TARGET_KIND, rubric_score
from robodojo_rc.specs import RELEASE, SPEC_BY_KEY, SPECS, Equipment, Level, Rubric, TaskSpec
from robodojo_rc.tasks import (
    K_TRIALS,
    MAX_STEPS,
    TASK_FACTORIES,
    cap_pen,
    make_task,
    pack_and_pour_fruit,
    sort_objects,
    stack_bowls,
    stand_up_bottles,
    store_in_safe,
)

try:
    __version__ = version("robodojo-rc")
except PackageNotFoundError:  # running from an uninstalled source tree
    __version__ = "0.0.0"

__all__ = [
    "K_TRIALS",
    "MAX_STEPS",
    "RELEASE",
    "SPECS",
    "SPEC_BY_KEY",
    "TARGET_KIND",
    "TASK_FACTORIES",
    "AstraGrader",
    "Equipment",
    "Level",
    "OperatorGrader",
    "Rubric",
    "TaskSpec",
    "__version__",
    "astra_grader",
    "cap_pen",
    "make_task",
    "operator_grader",
    "pack_and_pour_fruit",
    "rubric_score",
    "sort_objects",
    "stack_bowls",
    "stand_up_bottles",
    "store_in_safe",
]
