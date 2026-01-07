import html
import os

import requests

API_BASE = "https://wakatime.com/api"


def fetch_stats(api_key: str) -> dict:
    url = f"{API_BASE}/v1/users/current/stats/last_7_days"
    r = requests.get(url, headers={"Authorization": f"Basic {api_key}"}, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


def fetch_languages(api_key: str) -> dict:
    url = f"{API_BASE}/v1/program_languages"
    r = requests.get(url, headers={"Authorization": f"Basic {api_key}"}, timeout=30)
    r.raise_for_status()

    lang_colors: dict[str, str] = {}
    for lang in r.json().get("data", []):
        name = (lang.get("name") or "").strip()
        color = (lang.get("color") or "").strip()
        if name:
            lang_colors[name] = color or "#d0d7de"
    return lang_colors


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def clamp_pct(p: float) -> float:
    try:
        p = float(p)
    except Exception:
        return 0.0
    if p != p:  # NaN
        return 0.0
    return max(0.0, min(100.0, p))


def main():
    api_key = os.environ["WAKATIME_API_KEY"]

    data = fetch_stats(api_key)
    languages = (data.get("languages") or [])[:5]  # top 5
    language_colors = fetch_languages(api_key)

    total_text = esc(data.get("human_readable_total_including_other_language", ""))
    title = f"WakaTime (last 7 days) · {total_text}"

    # ---- layout: card-like ----
    width = 720
    padding = 16
    header_h = 28  # h2 line-height-ish
    gap_after_header = 10
    row_h = 26
    rows = len(languages)
    height = padding * 2 + header_h + gap_after_header + rows * row_h + 10

    # ---- rows HTML ----
    rows_html = []
    for i, l in enumerate(languages):
        raw_name = (l.get("name") or "").strip()
        name = esc(raw_name)

        time_text = esc(l.get("text") or "")
        pct = clamp_pct(l.get("percent") or 0.0)
        pct_text = f"{pct:.2f}%"

        # color lookup uses raw_name (not escaped)
        color = esc(language_colors.get(raw_name, "#d0d7de"))

        rows_html.append(
            f"""
            <li class="row" style="animation-delay:{i * 90}ms;">
              <span class="dot" style="background:{color};"></span>
              <span class="lang" title="{name}">{name}</span>
              <span class="time" title="{time_text}">{time_text}</span>
              <span class="bar">
                <span class="barBg">
                  <span class="barFill" style="width:{pct:.4f}%; background:{color};"></span>
                </span>
              </span>
              <span class="pct">{pct_text}</span>
            </li>
            """.strip()
        )

    list_html = "\n".join(rows_html)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    svg {{
      font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji;
    }}

    #background {{
      fill: #00000000;
      stroke: #8B8B8B22;
      stroke-width: 1px;
      rx: 10px;
      ry: 10px;
    }}

    foreignObject {{
      width: {width - padding * 2}px;
      height: {height - padding * 2}px;
    }}

    .wrap {{
      width: 100%;
      height: 100%;
      overflow: hidden;
    }}

    h2 {{
      margin: 0 0 {gap_after_header}px 0;
      line-height: {header_h}px;
      font-size: 16px;
      font-weight: 650;
      color: rgb(72, 148, 224);
    }}

    ul {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}

    /*
       5컬럼:
       [color] [lang] [time] [bar] [percent]
    */
    .row {{
      display: grid;
      grid-template-columns: 10px 140px 150px 1fr 64px;
      gap: 10px;
      align-items: center;
      height: {row_h}px;

      transform: translateX(-12px);
      opacity: 0;
      animation: slideIn 420ms ease-out forwards;
    }}

    @keyframes slideIn {{
      to {{
        transform: translateX(0);
        opacity: 1;
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
      font-weight: 650;
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

    .pct {{
      font-size: 12px;
      color: rgb(150, 150, 150);
      text-align: right;
      font-variant-numeric: tabular-nums;
    }}

    .barBg {{
      display: block;
      height: 8px;
      border-radius: 999px;
      background: #8B8B8B22;
      overflow: hidden;
    }}

    .barFill {{
      display: block;
      height: 100%;
      border-radius: 999px;
      opacity: 0.9;
    }}
  </style>

  <rect x="6" y="6" width="{width - 12}" height="{height - 12}" id="background" />

  <foreignObject x="{padding}" y="{padding}">
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <h2>{esc(title)}</h2>
      <ul>
        {list_html}
      </ul>
    </div>
  </foreignObject>
</svg>
"""
    print(svg)


if __name__ == "__main__":
    main()
