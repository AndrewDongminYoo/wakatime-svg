# Repository Guidelines

## Project Structure & Module Organization

- `scripts/generate-wakatime-svg.py` is the main entrypoint that fetches WakaTime stats and renders the SVG card.
- `.github/workflows/wakatime-svg.yml` runs the daily GitHub Actions job that generates and publishes the SVG.
- `templates/` is reserved for SVG/HTML snippets (currently empty).
- `generated/` is the runtime output folder created by local runs or CI and contains `generated/wakatime.svg`.

## Build, Test, and Development Commands

- `python -m pip install requests` installs the only runtime dependency.
- `WAKATIME_API_KEY=... python scripts/generate-wakatime-svg.py > generated/wakatime.svg` generates the SVG locally.
- `trunk fmt` formats code; `trunk check` runs linters (Black, isort, ruff, etc.) as configured in `.trunk/trunk.yaml`.

## Coding Style & Naming Conventions

- Python with 4-space indentation and Black-compatible formatting.
- Use `snake_case` for functions/variables and `UPPER_CASE` for module constants (e.g., `API_BASE`).
- Keep script filenames in kebab-case to match `generate-wakatime-svg.py`.

## Testing Guidelines

- No automated tests are configured. If you add tests, place them in `tests/` and name files `test_*.py`.
- Document new test commands in this file and keep them runnable from the repo root.

## Commit & Pull Request Guidelines

- Commit messages follow Conventional Commits: `type: subject` (e.g., `feat: ...`, `chore: ...`, `ci: ...`).
- PRs should describe the change, note any workflow impact, and include local reproduction steps when SVG output changes.
- Link relevant issues or discussions when available.

## Security & Configuration Notes

- Provide `WAKATIME_API_KEY` via environment variables only; never commit secrets.
- GitHub Actions expects the key in `secrets.WAKATIME_API_KEY`.
