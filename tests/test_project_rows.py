"""Checks that project bars encode time, not a constant-width ratio.

Before this check existed, the bar showed additions vs deletions. WakaTime
reports no deletions, so every project rendered a full-width bar regardless of
how long it was worked on.
"""

import importlib.util
import pathlib
import re

SCRIPT = (
    pathlib.Path(__file__).resolve().parent.parent
    / "scripts"
    / "generate-wakatime-svg.py"
)

spec = importlib.util.spec_from_file_location("wakatime_svg", SCRIPT)
wakatime_svg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wakatime_svg)

# Trimmed shape of WakaTime's stats/last_7_days `projects` entries.
PROJECTS = [
    {"name": "clipboard-keyboard", "total_seconds": 68040.0, "text": "18 hrs 54 mins"},
    {"name": "party-os", "total_seconds": 39000.0, "text": "10 hrs 50 mins"},
    {"name": "piggon", "total_seconds": 31500.0, "text": "8 hrs 45 mins"},
    {"name": "llm-wiki-dongminyu", "total_seconds": 26940.0, "text": "7 hrs 29 mins"},
    {"name": "screenloom", "total_seconds": 23580.0, "text": "6 hrs 33 mins"},
]


def bar_widths(rows_html: str) -> list[float]:
    return [float(w) for w in re.findall(r"width:([\d.]+)%", rows_html)]


def test_bar_width_tracks_time() -> None:
    widths = bar_widths(wakatime_svg.build_project_rows(PROJECTS, "Private project"))
    assert len(widths) == len(PROJECTS), widths
    # The busiest project fills the track; the rest shrink in proportion.
    assert widths[0] == 100.0, widths
    assert widths == sorted(widths, reverse=True), widths
    assert len(set(widths)) == len(widths), widths
    assert round(widths[1], 1) == 57.3, widths  # 39000 / 68040


def test_untracked_projects_render_an_empty_bar() -> None:
    items = [{"name": "idle", "total_seconds": 0.0, "text": "0 secs"}]
    assert bar_widths(wakatime_svg.build_project_rows(items, None)) == [0.0]


if __name__ == "__main__":
    for name, case in sorted(globals().items()):
        if name.startswith("test_"):
            case()
            print(f"ok {name}")
