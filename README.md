# wakatime-svg (transparent svg image)

![Repository banner](assets/banner.png)

Generate SVG cards from WakaTime stats for the last 7 days. GitHub Actions refreshes the SVGs daily and publishes the artifacts to the `output` branch.

## Key Features

- Visualizes the top 5 languages by time and percentage
- Visualizes the top 5 projects by time, with additions vs deletions ratios
- Language color mapping with percentage bars
- Daily scheduled refresh (00:00 UTC)

## Quick Start (Local)

1. Install Python 3.14+
2. Install dependencies
   ```bash
   python -m pip install requests
   ```
3. Set environment variable
   ```bash
   export WAKATIME_API_KEY=YOUR_KEY
   ```
4. Generate SVGs
   ```bash
   mkdir -p generated
   python scripts/generate-wakatime-svg.py
   ```
   Output: `generated/languages.svg`, `generated/projects.svg`

## GitHub Actions Setup

1. Add `WAKATIME_API_KEY` to repository Secrets
2. Enable Actions for the repo
3. Run the `Generate WakaTime SVG` workflow manually or wait for the schedule
4. Confirm `generated/languages.svg` and `generated/projects.svg` appear on the `output` branch

## GitHub Action Usage (Marketplace)

Example workflow using this repo as an action (defaults only):

```yaml
name: Waka Charts

on:
  workflow_dispatch:
  schedule:
    - cron: "0 0 * * *"

permissions:
  contents: write

jobs:
  update-charts:
    runs-on: ubuntu-latest
    steps:
      - uses: AndrewDongminYoo/wakatime-svg@v1.1.0
        with:
          WAKATIME_API_KEY: ${{ secrets.WAKATIME_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Inputs map to environment variables consumed by `scripts/generate-wakatime-svg.py`. Values are optional unless marked required.

Fully customized example (overrides every supported input):

```yaml
name: Waka Charts

on:
  workflow_dispatch:
  schedule:
    - cron: 0 0 * * *

permissions:
  contents: write

jobs:
  update-charts:
    runs-on: ubuntu-latest
    steps:
      - uses: AndrewDongminYoo/wakatime-svg@v1.1.0
        with:
          WAKATIME_API_KEY: ${{ secrets.WAKATIME_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # The values below are for customization. You may omit them if desired.
          WAKATIME_LANG_LIMIT: 7
          WAKATIME_CHART_WIDTH: 420
          WAKATIME_CHART_HEIGHT: 200
          WAKATIME_CHART_ROW_HEIGHT: 28
          WAKATIME_CHART_BAR_HEIGHT: 10
          WAKATIME_CHART_MARGIN_X: 18
          WAKATIME_CHART_MARGIN_Y: 12
          WAKATIME_CHART_PADDING: 12
          WAKATIME_CHART_COL_NAME_WIDTH: 90
          WAKATIME_CHART_COL_DURATION_WIDTH: 90
          WAKATIME_CHART_COL_PERCENT_WIDTH: 42
          WAKATIME_CHART_DYNAMIC_HEIGHT: false
          BRANCH_NAME: output
          COMMIT_MESSAGE: "chore: update wakatime svg"
          IMAGES_FOLDER: generated
```

You can also override the text shown for private repositories by setting `WAKATIME_PRIVATE_PROJECT_LABEL` (default `Private project`) when WakaTime reports `Unknown Project`.

If you'd rather remove the placeholder line entirely and keep showing the next-ranked projects, set `WAKATIME_SKIP_UNKNOWN_PROJECTS=true`. When that flag is enabled, the card skips any `Unknown Project` entries (or blank names) and continues down the ranking so you still see `WAKATIME_LANG_LIMIT` actual projects; when it is false (default), the placeholder is replaced by the private-project label instead.

## Why this action

- Transparent SVGs blend nicely on both light and dark themes.
- Mobile-friendly default width (360px) keeps cards readable in apps.
- Shows both languages and projects (with additions/deletions split for projects).
- Simple setup: defaults are sane, but layout can be fully customized.

## Inspiration

Inspired by `athul/waka-readme` and `rahul-jha98/github-stats-transparent`.

## Release Notes

See [`RELEASE_NOTES.md`](RELEASE_NOTES.md) for the full changelog.

## Embed in README

Use the SVGs published on the `output` branch.

```md
![WakaTime Languages](https://raw.githubusercontent.com/<USER>/<REPO>/output/generated/languages.svg)
![WakaTime Projects](https://raw.githubusercontent.com/<USER>/<REPO>/output/generated/projects.svg)
```

![WakaTime Languages](https://raw.githubusercontent.com/AndrewDongminYoo/wakatime-svg/output/generated/languages.svg)
![WakaTime Projects](https://raw.githubusercontent.com/AndrewDongminYoo/wakatime-svg/output/generated/projects.svg)

## Marketplace Submission Notes

- Update project metadata in `pyproject.toml` (`name`, `version`, `description`).
- Keep the repo public and preserve the license (`LICENSE`).
- Prepare marketing assets (use `assets/banner.png` and screenshots if needed).
- Verify the workflow succeeds and the `output` branch is generated.
- Create release tags in `vX.Y.Z` format if the marketplace requires versioned releases.

## Support Requests

Please open an Issue and include:

- Environment (OS, Python version)
- How you ran it (local vs Actions)
- Full error logs
- Expected vs actual behavior

Never share your `WAKATIME_API_KEY`.
