"""Write docs/tasks/<key>.md for every task from the specs (tests fail when a page drifts).

uv run python tools/task_pages.py
"""

from __future__ import annotations

from pathlib import Path

from robodojo_rc.specs import RELEASE, SPECS, TaskSpec

ROOT = Path(__file__).resolve().parents[1]


def render(spec: TaskSpec) -> str:
    """The task's reference page: instruction, setup photo, setup, reset, equipment, rubric."""
    equipment = "\n".join(
        f"| {e.name} | {e.quantity} | [{e.product}]({e.url}) |" for e in spec.equipment
    )
    levels = "\n".join(f"| {level.score} | {level.description} |" for level in spec.rubric.levels)
    other_name = (
        f" The judge's rubric keeps RoboDojo's name, {spec.rubric.name}."
        if spec.rubric.name != spec.name
        else ""
    )
    return f"""# {spec.name}

Task `robodojo-rc/{spec.key}`, version {spec.version}, from release {RELEASE}. Adapted from
RoboDojo's real-world task [{spec.source_title}]({spec.source_url}).{other_name}

## Instruction

What the model is told, word for word:

> {spec.instruction}

## Setup

![Setup for {spec.name}, from above](../assets/{spec.key}-setup.jpg)

{spec.setup}

Between trials: {spec.reset}

## Equipment

| Object | Quantity | Product used in the published runs |
|---|--:|---|
{equipment}

## Rubric

Revision `{spec.rubric.revision}`. A trial scores one of these levels. The judge sees the
guidance and every level below, word for word.

```text
{spec.rubric.guidance}
```

| Score | Condition |
|--:|---|
{levels}
"""


def main() -> None:
    """Rewrite every task page."""
    for spec in SPECS:
        (ROOT / "docs" / "tasks" / f"{spec.key}.md").write_text(render(spec))


if __name__ == "__main__":
    main()
