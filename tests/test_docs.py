"""Task pages and the README stay in step with the specs."""

import sys
from pathlib import Path

import pytest

from robodojo_rc import SPECS, TaskSpec

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import task_pages  # noqa: E402


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.key)
def test_task_page_is_current(spec: TaskSpec) -> None:
    page = ROOT / "docs" / "tasks" / f"{spec.key}.md"
    assert page.read_text() == task_pages.render(spec), "run: uv run python tools/task_pages.py"


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.key)
def test_readme_lists_task(spec: TaskSpec) -> None:
    readme = (ROOT / "README.md").read_text()
    row = (
        f"| [`robodojo-rc/{spec.key}`](docs/tasks/{spec.key}.md) | "
        f"[{spec.source_title}]({spec.source_url}) | {spec.instruction} |"
    )
    assert row in readme


def test_render_writes_every_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "docs" / "tasks").mkdir(parents=True)
    monkeypatch.setattr(task_pages, "ROOT", tmp_path)
    task_pages.main()
    assert sorted(p.stem for p in (tmp_path / "docs" / "tasks").iterdir()) == sorted(
        s.key for s in SPECS
    )


def test_readme_has_no_em_dashes() -> None:
    for path in (ROOT / "README.md", *sorted((ROOT / "docs" / "tasks").glob("*.md"))):
        assert "—" not in path.read_text(), path
