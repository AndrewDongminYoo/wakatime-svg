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
PROJECTS_SVG_NAME = "projects.svg"
UNKNOWN_PROJECT_PLACEHOLDER = "Unknown Project"
DEFAULT_UNKNOWN_PROJECT_LABEL = "Private project"

DEFAULT_OUTPUT_DIR = "generated"
DEFAULT_TOP_N_COUNT = 5
DEFAULT_CHART_WIDTH = 360
DEFAULT_HEADER_HEIGHT = 28
DEFAULT_ROW_HEIGHT = 26
DEFAULT_RECT_RADIUS = 6
DEFAULT_OUTER_PADDING = 12
DEFAULT_PADDING_X = 16
DEFAULT_PADDING_Y = 12
DEFAULT_GAP_AFTER_HEADER = 10
DEFAULT_DOT_COL_WIDTH = 5
DEFAULT_PERCENT_COL_WIDTH = 42
DEFAULT_NAME_COL_WIDTH = 75
DEFAULT_DURATION_COL_WIDTH = 70
DEFAULT_PROJECT_NAME_COL_WIDTH = 120
DEFAULT_PROJECT_DURATION_COL_WIDTH = 54
DEFAULT_BAR_HEIGHT = 8


def env_str(name: str, default: str) -> str:
    """Read a string environment variable with fallback."""
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def env_int(name: str, default: int, minimum: int | None = None) -> int:
    """Read an integer environment variable with optional minimum clamp."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        parsed = max(minimum, parsed)
    return parsed


def env_has_value(name: str) -> bool:
    """Return True if the environment variable is set to a non-empty value."""
    value = os.getenv(name)
    return value is not None and value.strip() != ""


def env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def load_chart_config() -> dict[str, int | bool]:
    """Load chart layout settings from environment variables."""
    row_height = env_int("WAKATIME_CHART_ROW_HEIGHT", DEFAULT_ROW_HEIGHT, minimum=16)
    if not env_has_value("WAKATIME_CHART_ROW_HEIGHT") and env_has_value(
        "WAKATIME_CHART_BAR_HEIGHT"
    ):
        # Backward-compat: bar height used to control row height as well.
        row_height = env_int(
            "WAKATIME_CHART_BAR_HEIGHT", DEFAULT_ROW_HEIGHT, minimum=16
        )
    name_width = env_int(
        "WAKATIME_CHART_COL_NAME_WIDTH", DEFAULT_NAME_COL_WIDTH, minimum=40
    )
    duration_width = env_int(
        "WAKATIME_CHART_COL_DURATION_WIDTH", DEFAULT_DURATION_COL_WIDTH, minimum=32
    )
    percent_width = env_int(
        "WAKATIME_CHART_COL_PERCENT_WIDTH", DEFAULT_PERCENT_COL_WIDTH, minimum=24
    )
    project_name_width = DEFAULT_PROJECT_NAME_COL_WIDTH
    project_duration_width = DEFAULT_PROJECT_DURATION_COL_WIDTH
    if env_has_value("WAKATIME_CHART_COL_NAME_WIDTH"):
        project_name_width = name_width
    if env_has_value("WAKATIME_CHART_COL_DURATION_WIDTH"):
        project_duration_width = duration_width

    return {
        "width": env_int("WAKATIME_CHART_WIDTH", DEFAULT_CHART_WIDTH, minimum=120),
        "height": env_int("WAKATIME_CHART_HEIGHT", 0, minimum=0),
        "row_height": row_height,
        "bar_height": env_int(
            "WAKATIME_CHART_BAR_HEIGHT", DEFAULT_BAR_HEIGHT, minimum=4
        ),
        "outer_padding": env_int(
            "WAKATIME_CHART_PADDING", DEFAULT_OUTER_PADDING, minimum=0
        ),
        "padding_x": env_int("WAKATIME_CHART_MARGIN_X", DEFAULT_PADDING_X, minimum=0),
        "padding_y": env_int("WAKATIME_CHART_MARGIN_Y", DEFAULT_PADDING_Y, minimum=0),
        "rect_radius": DEFAULT_RECT_RADIUS,
        "header_height": DEFAULT_HEADER_HEIGHT,
        "gap_after_header": DEFAULT_GAP_AFTER_HEADER,
        "col_dot_width": DEFAULT_DOT_COL_WIDTH,
        "col_percent_width": percent_width,
        "col_name_width": name_width,
        "col_duration_width": duration_width,
        "project_name_width": project_name_width,
        "project_duration_width": project_duration_width,
        "dynamic_height": env_bool("WAKATIME_CHART_DYNAMIC_HEIGHT", True),
    }


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


def parse_total_seconds(item: dict) -> float:
    """Return a numeric total_seconds value from an item."""
    try:
        return float(item.get("total_seconds") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def normalize_language_percent(items: list[dict]) -> list[dict]:
    """Normalize language percentages based on total_seconds across items."""
    total_seconds = sum(parse_total_seconds(item) for item in items)
    if total_seconds <= 0:
        return items

    normalized = []
    for item in items:
        seconds = parse_total_seconds(item)
        percent = clamp_pct(seconds / total_seconds * 100.0)
        updated = dict(item)
        updated["percent"] = percent
        normalized.append(updated)
    return normalized


def prepare_language_items(items: list[dict], limit: int) -> list[dict]:
    """Return top N languages (excluding Other), normalized to 100%."""
    if not items:
        return []

    safe_limit = max(1, int(limit))
    language_items = [
        item for item in items if (item.get("name") or "").strip().lower() != "other"
    ]
    if not language_items:
        return []

    top_items = []
    for item in language_items[:safe_limit]:
        updated = dict(item)
        updated["percent_raw"] = item.get("percent", 0.0)
        top_items.append(updated)
    return normalize_language_percent(top_items)


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


def is_unknown_project_name(raw_name: str) -> bool:
    """Return True if the project name resembles WakaTime's Unknown Project placeholder."""
    safe_name = (raw_name or "").strip()
    if not safe_name:
        return True
    return safe_name.lower() == UNKNOWN_PROJECT_PLACEHOLDER.lower()


def resolve_project_display_name(raw_name: str, private_label: str) -> str:
    """Return a display-friendly name for private/unknown projects."""
    safe_name = (raw_name or "").strip()
    if is_unknown_project_name(safe_name):
        return private_label
    return safe_name


def prepare_project_items(
    items: list[dict], limit: int, skip_unknown: bool
) -> list[dict]:
    """Return the top-N project entries, optionally skipping Unknown Project items."""
    if not items:
        return []

    safe_limit = max(1, limit)
    selected: list[dict] = []
    for item in items:
        raw_name = (item.get("name") or "").strip()
        if skip_unknown and is_unknown_project_name(raw_name):
            continue

        selected.append(item)
        if len(selected) >= safe_limit:
            break

    if not skip_unknown:
        return selected[:safe_limit]

    return selected


def build_language_rows(items: list[dict], colors: dict[str, str]) -> str:
    """Build the HTML list items for the language stats."""
    rows_html = []
    for i, item in enumerate(items):
        raw_name = (item.get("name") or "").strip()
        name = esc(raw_name)

        time_text = compact_time_text(item.get("text") or "")
        percent = clamp_pct(item.get("percent") or 0.0)
        raw_percent = clamp_pct(item.get("percent_raw", item.get("percent") or 0.0))
        percent_text = f"{raw_percent:.1f}%"
        bar_class = "bar-fill"
        if percent <= 0.0:
            bar_class += " bar-fill-empty"
        elif percent >= 99.5:
            bar_class += " bar-fill-full"

        color = esc(colors.get(raw_name, DEFAULT_BAR_COLOR))

        rows_html.append(f"""
        <li class="row language" style="animation-delay:{i * 150}ms;">
          <span class="dot" style="background:{color};"/>
          <span class="lang" title="{name}">{name}</span>
          <span class="time" title="{time_text}">{time_text}</span>
          <span class="bar">
            <span class="bar-background">
              <span class="{bar_class}" style="width:{percent:.4f}%; background:{color};"/>
            </span>
          </span>
          <span class="percent">{percent_text}</span>
        </li>""".strip())

    return "\n        ".join(rows_html)


def build_project_rows(items: list[dict], private_label: str) -> str:
    """Build the HTML list items for the project stats."""
    rows_html = []
    for i, item in enumerate(items):
        raw_name = (item.get("name") or "").strip()
        display_name = resolve_project_display_name(raw_name, private_label)
        name = esc(display_name)

        time_text = compact_time_text(item.get("text") or "")

        additions_pct, deletions_pct = additions_deletions_ratio(item)
        bar_title = esc(f"+ {additions_pct:.0f}% / - {deletions_pct:.0f}%")

        rows_html.append(f"""
        <li class="row project" style="animation-delay:{i * 150}ms;">
          <span class="lang" title="{name}">{name}</span>
          <span class="bar" title="{bar_title}">
            <span class="bar-background">
              <span class="bar-additions" style="width:{additions_pct:.4f}%;"></span>
              <span class="bar-deletions" style="width:{deletions_pct:.4f}%;"></span>
            </span>
          </span>
          <span class="time project-time" title="{time_text}">{time_text}</span>
        </li>""".strip())

    return "\n        ".join(rows_html)


def render_svg(title: str, rows_html: str, row_count: int, config: dict) -> str:
    """Render a single SVG card with the provided rows."""
    card_width = int(config["width"])
    outer_padding = int(config["outer_padding"])
    header_h = int(config["header_height"])  # h2 line-height-ish
    rect_radius = int(config["rect_radius"])
    w_padding = int(config["padding_x"])
    h_padding = int(config["padding_y"])
    gap_after_header = int(config["gap_after_header"])
    row_h = int(config["row_height"])
    bar_h = min(int(config["bar_height"]), row_h)
    bar_cap = max(2, bar_h)
    name_w = int(config["col_name_width"])
    duration_w = int(config["col_duration_width"])
    project_name_w = int(config["project_name_width"])
    project_duration_w = int(config["project_duration_width"])
    dot_w = int(config["col_dot_width"])
    percent_w = int(config["col_percent_width"])
    dynamic_height = bool(config["dynamic_height"])

    computed_height = (
        w_padding + h_padding + header_h + gap_after_header + row_count * row_h + 10
    )
    explicit_height = int(config["height"])
    card_height = (
        computed_height if dynamic_height or explicit_height <= 0 else explicit_height
    )
    svg_width = card_width + outer_padding * 2
    svg_height = card_height + outer_padding * 2
    inner_width = max(1, card_width - w_padding * 2)
    inner_height = max(1, card_height - h_padding * 2)

    list_html = f"""
      <ul class="rows">
        {rows_html}
      </ul>
    """.strip()

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}">
  <style>
    svg {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        Segoe UI,
        Helvetica,
        Arial,
        sans-serif,
        Apple Color Emoji,
        Segoe UI Emoji;
      font-size: 14px;
      line-height: 21px;
    }}

    #background {{
      fill: #00000000;
      stroke: #8B8B8B22;
      stroke-width: 1px;
    }}

    foreignObject {{
      width: {inner_width}px;
      height: {inner_height}px;
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
      grid-template-columns: {dot_w}px {name_w}px {duration_w}px 1fr {percent_w}px;
    }}

    .row.project {{
      grid-template-columns: minmax({project_name_w}px, 1.3fr) 1fr {project_duration_w}px;
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
      height: {bar_h}px;
      border-radius: 999px;
      background: #8B8B8B22;
      overflow: hidden;
    }}

    .bar-fill {{
      display: block;
      height: 100%;
      border-radius: 999px 0 0 999px;
      opacity: 0.9;
      flex: 0 0 auto;
      position: relative;
      --bar-cap-size: {bar_cap}px;
    }}

    .bar-fill::after {{
      content: "";
      position: absolute;
      right: calc(var(--bar-cap-size) / -2);
      width: var(--bar-cap-size);
      height: 100%;
      background: inherit;
      border-radius: 999px;
    }}

    .bar-fill-full {{
      border-radius: 999px;
    }}

    .bar-fill-full::after,
    .bar-fill-empty::after {{
      display: none;
    }}

    .bar-fill-empty {{
      display: none;
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

  <rect
    id="background"
    x="{outer_padding}"
    y="{outer_padding}"
    rx="{rect_radius}"
    ry="{rect_radius}"
    width="{card_width}"
    height="{card_height}"
    fill="none"
    stroke="#8B8B8B22"
    stroke-width="1"
  />

  <foreignObject
    x="{outer_padding + w_padding}"
    y="{outer_padding + h_padding}"
    width="{inner_width}"
    height="{inner_height}"
  >
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


def main() -> None:
    """Render the WakaTime SVG cards to disk."""
    api_key = os.environ["WAKATIME_API_KEY"]
    config = load_chart_config()
    lang_limit = env_int("WAKATIME_LANG_LIMIT", DEFAULT_TOP_N_COUNT, minimum=1)
    output_dir = env_str("IMAGES_FOLDER", DEFAULT_OUTPUT_DIR)
    private_project_label = env_str(
        "WAKATIME_PRIVATE_PROJECT_LABEL", DEFAULT_UNKNOWN_PROJECT_LABEL
    )
    skip_unknown_projects = env_bool("WAKATIME_SKIP_UNKNOWN_PROJECTS", False)

    data = fetch_stats(api_key)
    languages = prepare_language_items(data.get("languages") or [], lang_limit)
    projects = prepare_project_items(
        data.get("projects") or [], lang_limit, skip_unknown_projects
    )
    language_colors = fetch_languages(api_key)

    total_text = data.get("human_readable_total_including_other_language") or ""
    total_text = total_text.replace("hr", "hour")
    total_text = total_text.replace("min", "minute")

    languages_title = f"Languages · {total_text}"
    projects_title = f"Projects (+/-) · {total_text}"

    languages_rows = build_language_rows(languages, language_colors)
    projects_rows = build_project_rows(projects, private_project_label)

    languages_svg = render_svg(languages_title, languages_rows, len(languages), config)
    projects_svg = render_svg(projects_title, projects_rows, len(projects), config)

    write_svg(os.path.join(output_dir, LANGUAGES_SVG_NAME), languages_svg)
    write_svg(os.path.join(output_dir, PROJECTS_SVG_NAME), projects_svg)


if __name__ == "__main__":
    main()
