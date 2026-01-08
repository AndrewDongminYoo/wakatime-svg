import html
import math
import os
import re

import requests

API_BASE = "https://wakatime.com/api"
DEFAULT_BAR_COLOR = "#d0d7de"
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


def main():
    """Render the WakaTime SVG card to stdout."""
    api_key = os.environ["WAKATIME_API_KEY"]

    data = fetch_stats(api_key)
    languages = (data.get("languages") or [])[:TOP_N_COUNT]
    language_colors = fetch_languages(api_key)

    total_text = esc(data.get("human_readable_total_including_other_language", ""))
    total_text = total_text.replace("hr", "hour")
    total_text = total_text.replace("min", "minute")

    title = f"WakaTime (last 7 days) · {total_text}"

    # ---- layout: card-like ----
    width = 360
    header_h = 28  # h2 line-height-ish
    rect_size = 6
    w_padding = 16
    h_padding = 12
    gap_after_header = 10
    row_h = 26
    rows = len(languages)  # rows <= TOP_N_COUNT
    height = w_padding + h_padding + header_h + gap_after_header + rows * row_h + 10

    # ---- rows HTML ----
    rows_html = []
    for i, lang in enumerate(languages):
        raw_name = (lang.get("name") or "").strip()
        name = esc(raw_name)

        time_text = esc(lang.get("text") or "")
        time_text = re.sub(r"([a-z])\w+", r"\g<1>", time_text, flags=re.IGNORECASE)
        percent = clamp_pct(lang.get("percent") or 0.0)
        percent_text = f"{percent:.0f}%"

        # color lookup uses raw_name (not escaped)
        color = esc(language_colors.get(raw_name, "#d0d7de"))

        rows_html.append(
            f"""
        <li class="row" style="animation-delay:{i * 150}ms;">
          <span class="dot" style="background:{color};"/>
          <span class="lang" title="{name}">{name}</span>
          <span class="time" title="{time_text}">{time_text}</span>
          <span class="bar">
            <span class="bar-background">
              <span class="bar-fill" style="width:{percent:.4f}%; background:{color};"/>
            </span>
          </span>
          <span class="percent">{percent_text}</span>
        </li>
            """.strip()
        )

    list_html = "\n        ".join(rows_html)

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
    }}

    #rows {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}

    .row {{
      display: grid;
      grid-template-columns: 5px 70px 75px 1fr 32px;
      gap: 10px;
      align-items: center;
      height: {row_h}px;

      transform: translateX(-500%);
      animation-name: slideIn;
      animation-duration: 1s;
      animation-function: ease-in-out;
      animation-fill-mode: forwards;
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

    .percent {{
      font-size: 12px;
      color: rgb(150, 150, 150);
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}

    .bar-background {{
      display: block;
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
    }}
  </style>

  <rect id="background" x="{rect_size}" y="{rect_size}" rx="{rect_size}" ry="{rect_size}" width="{width - rect_size * 2}" height="{height - rect_size * 2}" fill="none" stroke="#8B8B8B22" stroke-width="1"/>

  <foreignObject x="{w_padding}" y="{h_padding}" width="{width - w_padding * 2}" height="{height - h_padding * 2}">
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <h2>{esc(title)}</h2>
      <ul id="rows">
        {list_html}
      </ul>
    </div>
  </foreignObject>
</svg>"""
    print(svg)


if __name__ == "__main__":
    main()
