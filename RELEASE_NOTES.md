# Release Notes

## v1.1.0 - 2026-01-12

### Improvements

- Show only the top N languages (excluding "Other") while keeping bars normalized to the displayed items.
- Display language percentage text from the raw WakaTime API value (now with one decimal place).
- Improve bar readability with a rounded end-cap that preserves perceived progress length.
- Increase default percent column width to avoid clipping.
- Align default duration column width with the new layout.

### New Input

- `WAKATIME_CHART_COL_PERCENT_WIDTH`: Optional percent column width (px).
- `WAKATIME_CHART_ROW_HEIGHT`: Optional row height (px).

## v1.0.0 - 2026-01-08

First public release of the WakaTime SVG GitHub Action.

### Highlights

- Transparent SVGs that look good on both light and dark themes.
- Mobile-friendly default width (360px) for clean rendering in apps.
- Generates two cards: languages and projects (with additions/deletions split).
- Composite action for simple Marketplace usage with sensible defaults.
- Fully customizable layout via inputs (width, height, padding, column widths, etc.).

### Usage

```yaml:github-actions-workflow
- uses: AndrewDongminYoo/wakatime-svg@v1
  with:
    WAKATIME_API_KEY: ${{ secrets.WAKATIME_API_KEY }}
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Credits

Inspired by `athul/waka-readme` and `rahul-jha98/github-stats-transparent`.
