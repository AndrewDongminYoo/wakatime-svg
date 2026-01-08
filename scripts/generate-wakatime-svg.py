"""Generate WakaTime SVG cards for recent language and project stats.

Reads the WAKATIME_API_KEY environment variable, fetches last 7 days of data,
and writes SVG files into the generated/ directory.
"""

import html
import math
import os
import re

import requests

API_BASE = "https://wakatime.com/api"
ADDITIONS_BAR_COLOR = "#23d18b"
DEFAULT_BAR_COLOR = "#d0d7de"
DELETIONS_BAR_COLOR = "#f37c7c"
LANGUAGES_SVG_NAME = "languages.svg"
OUTPUT_DIR = "generated"
PROJECTS_SVG_NAME = "projects.svg"
TOP_N_COUNT = 5


def fetch_stats(api_key: str) -> dict:
    """Fetch WakaTime stats for the last 7 days using the API key."""
    url = f"{API_BASE}/v1/users/current/stats/last_7_days"
    r = requests.get(url, headers={"Authorization": f"Basic {api_key}"}, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


def fetch_languages(api_key: str) -> dict:
    """Fetch language color metadata and return a name->color mapping."""
    url = f"{API_BASE}/v1/program_languages"
    r = requests.get(url, headers={"Authorization": f"Basic {api_key}"}, timeout=30)
    r.raise_for_status()

    lang_colors: dict[str, str] = {}
    for lang in r.json().get("data", []):
        name = (lang.get("name") or "").strip()
        color = (lang.get("color") or "").strip()
        if name:
            lang_colors[name] = color or DEFAULT_BAR_COLOR
    return lang_colors


def esc(s: str) -> str:
    """Escape text for safe inclusion in HTML/SVG attributes."""
    return html.escape(s or "", quote=True)


def clamp_pct(p: float) -> float:
    """Coerce a percentage to a finite float in the [0.0, 100.0] range."""
    try:
        p = float(p)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    if math.isnan(p):
        return 0.0
    return max(0.0, min(100.0, p))


def shorten_time_label(text: str) -> str:
    """Shorten WakaTime duration labels for compact headings."""
    return re.sub(r"([a-z])\w+", r"\g<1>", text or "", flags=re.IGNORECASE)


def compact_time_text(text: str) -> str:
    """Shorten and escape WakaTime duration labels for the compact layout."""
    return esc(shorten_time_label(text))


def additions_deletions_ratio(item: dict) -> tuple[float, float]:
    """Return additions vs deletions percentages based on change totals."""
    ai_additions = float(item.get("ai_additions") or 0)
    ai_deletions = float(item.get("ai_deletions") or 0)
    human_additions = float(item.get("human_additions") or 0)
    human_deletions = float(item.get("human_deletions") or 0)

    additions = max(0.0, human_additions + ai_additions)
    deletions = max(0.0, human_deletions + ai_deletions)
    total = additions + deletions
    if total <= 0:
        return 0.0, 0.0

    additions_pct = clamp_pct(additions / total * 100.0)
    deletions_pct = clamp_pct(100.0 - additions_pct)
    return additions_pct, deletions_pct


def build_language_rows(items: list[dict], colors: dict[str, str]) -> str:
    """Build the HTML list items for the language stats."""
    rows_html = []
    for i, item in enumerate(items):
        raw_name = (item.get("name") or "").strip()
        name = esc(raw_name)

        time_text = compact_time_text(item.get("text") or "")
        percent = clamp_pct(item.get("percent") or 0.0)
        percent_text = f"{percent:.0f}%"

        color = esc(colors.get(raw_name, DEFAULT_BAR_COLOR))

        rows_html.append(
            f"""
        <li class="row language" style="animation-delay:{i * 150}ms;">
          <span class="dot" style="background:{color};"/>
          <span class="lang" title="{name}">{name}</span>
          <span class="time" title="{time_text}">{time_text}</span>
          <span class="bar">
            <span class="bar-background">
              <span class="bar-fill" style="width:{percent:.4f}%; background:{color};"/>
            </span>
          </span>
          <span class="percent">{percent_text}</span>
        </li>""".strip()
        )

    return "\n        ".join(rows_html)


def build_project_rows(items: list[dict]) -> str:
    """Build the HTML list items for the project stats."""
    rows_html = []
    for i, item in enumerate(items):
        raw_name = (item.get("name") or "").strip()
        name = esc(raw_name)

        time_text = compact_time_text(item.get("text") or "")

        additions_pct, deletions_pct = additions_deletions_ratio(item)
        bar_title = esc(f"+ {additions_pct:.0f}% / - {deletions_pct:.0f}%")

        rows_html.append(
            f"""
        <li class="row project" style="animation-delay:{i * 150}ms;">
          <span class="lang" title="{name}">{name}</span>
          <span class="bar" title="{bar_title}">
            <span class="bar-background">
              <span class="bar-additions" style="width:{additions_pct:.4f}%;"></span>
              <span class="bar-deletions" style="width:{deletions_pct:.4f}%;"></span>
            </span>
          </span>
          <span class="time project-time" title="{time_text}">{time_text}</span>
        </li>""".strip()
        )

    return "\n        ".join(rows_html)


def render_svg(title: str, rows_html: str, row_count: int) -> str:
    """Render a single SVG card with the provided rows."""
    width = 360
    header_h = 28  # h2 line-height-ish
    rect_size = 6
    w_padding = 16
    h_padding = 12
    gap_after_header = 10
    row_h = 26
    height = (
        w_padding + h_padding + header_h + gap_after_header + row_count * row_h + 10
    )

    list_html = f"""
      <ul class="rows">
        {rows_html}
      </ul>
    """.strip()

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <style>
    svg {{
      font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji;
      font-size: 14px;
      line-height: 21px;
    }}

    #background {{
      width: calc(100% - 10px);
      height: calc(100% - 10px);
      fill: #00000000;
      stroke: #8B8B8B22;
      stroke-width: 1px;
    }}

    foreignObject {{
      width: {width - w_padding * 2}px;
      height: {height - h_padding * 2}px;
    }}

    .wrap {{
      width: 100%;
      height: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    h2 {{
      margin-top: 0;
      margin-bottom: {gap_after_header}px;
      line-height: {header_h}px;
      font-size: 16px;
      font-weight: 600;
      color: rgb(72, 148, 224);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .rows {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}

    .row {{
      display: grid;
      gap: 10px;
      align-items: center;
      height: {row_h}px;

      transform: translateX(-500%);
      animation-name: slideIn;
      animation-duration: 1s;
      animation-function: ease-in-out;
      animation-fill-mode: forwards;
    }}

    .row.language {{
      grid-template-columns: 5px 70px 75px 1fr 32px;
    }}

    .row.project {{
      grid-template-columns: minmax(120px, 1.3fr) 1fr 54px;
    }}

    @keyframes slideIn {{
      to {{
        transform: translateX(0);
      }}
    }}

    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 999px;
      display: inline-block;
      box-shadow: 0 0 0 1px #00000012;
    }}

    .lang {{
      font-size: 12px;
      font-weight: 600;
      color: rgb(135, 135, 135);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .time {{
      font-size: 12px;
      color: rgb(150, 150, 150);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    .project-time {{
      text-align: right;
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.05rem;
    }}

    .percent {{
      font-size: 12px;
      color: rgb(150, 150, 150);
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}

    .bar-background {{
      display: flex;
      height: 8px;
      border-radius: 999px;
      background: #8B8B8B22;
      overflow: hidden;
    }}

    .bar-fill {{
      display: block;
      height: 100%;
      border-radius: 999px;
      opacity: 0.9;
      flex: 0 0 auto;
    }}

    .bar-additions,
    .bar-deletions {{
      display: block;
      height: 100%;
      flex: 0 0 auto;
    }}

    .bar-additions {{
      background: {ADDITIONS_BAR_COLOR};
    }}

    .bar-deletions {{
      background: {DELETIONS_BAR_COLOR};
    }}
  </style>

  <rect id="background" x="{rect_size}" y="{rect_size}" rx="{rect_size}" ry="{rect_size}" width="{width - rect_size * 2}" height="{height - rect_size * 2}" fill="none" stroke="#8B8B8B22" stroke-width="1"/>

  <foreignObject x="{w_padding}" y="{h_padding}" width="{width - w_padding * 2}" height="{height - h_padding * 2}">
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <h2>{esc(title)}</h2>
      {list_html}
    </div>
  </foreignObject>
</svg>"""
    return svg


def write_svg(path: str, content: str) -> None:
    """Write SVG content to disk, creating the parent directory."""
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def main():
    """Render the WakaTime SVG cards to disk."""
    api_key = os.environ["WAKATIME_API_KEY"]

    data = fetch_stats(api_key)
    languages = (data.get("languages") or [])[:TOP_N_COUNT]
    projects = (data.get("projects") or [])[:TOP_N_COUNT]
    language_colors = fetch_languages(api_key)

    total_text = data.get("human_readable_total_including_other_language") or ""
    total_text = total_text.replace("hr", "hour")
    total_text = total_text.replace("min", "minute")

    languages_title = f"Languages · {total_text}"
    projects_title = f"Projects (+/-) · {total_text}"

    languages_rows = build_language_rows(languages, language_colors)
    projects_rows = build_project_rows(projects)

    languages_svg = render_svg(languages_title, languages_rows, len(languages))
    projects_svg = render_svg(projects_title, projects_rows, len(projects))

    write_svg(os.path.join(OUTPUT_DIR, LANGUAGES_SVG_NAME), languages_svg)
    write_svg(os.path.join(OUTPUT_DIR, PROJECTS_SVG_NAME), projects_svg)


if __name__ == "__main__":
    main()
