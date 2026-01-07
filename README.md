# wakatime-svg (transparent svg image)

![Repository banner](assets/banner.png)

Generate an SVG card from WakaTime stats for the last 7 days. GitHub Actions refreshes the SVG daily and publishes the artifact to the `output` branch.

## Key Features

- Visualizes the top 5 languages by time and percentage
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
4. Generate SVG
   ```bash
   mkdir -p generated
   python scripts/generate-wakatime-svg.py > generated/wakatime.svg
   ```

## GitHub Actions Setup

1. Add `WAKATIME_API_KEY` to repository Secrets
2. Enable Actions for the repo
3. Run the `Generate WakaTime SVG` workflow manually or wait for the schedule
4. Confirm `generated/wakatime.svg` appears on the `output` branch

## Embed in README

Use the SVG published on the `output` branch.

```md
![WakaTime](https://raw.githubusercontent.com/<USER>/<REPO>/output/generated/wakatime.svg)
```

![WakaTime](https://raw.githubusercontent.com/AndrewDongminYoo/wakatime-svg/output/generated/wakatime.svg)

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
