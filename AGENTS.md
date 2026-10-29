# Repository Guidelines

## Project Structure & Module Organization

- `scripts/generate-wakatime-svg.py` is the main entrypoint that fetches WakaTime stats and renders the SVG cards.
- `.github/workflows/wakatime-svg.yml` runs the daily GitHub Actions job that generates and publishes the SVGs.
- `templates/` is reserved for SVG/HTML snippets (currently empty).
- `generated/` is the runtime output folder created by local runs or CI and contains `generated/languages.svg` and `generated/projects.svg`.

## Build, Test, and Development Commands

- `uv sync --frozen` installs the locked runtime dependencies.
- `WAKATIME_API_KEY=... uv run --frozen python scripts/generate-wakatime-svg.py` generates the SVGs locally.
- `trunk fmt <paths>` formats explicitly selected files; `trunk check --no-fix` runs the configured linters on changed files without applying fixes.
- `trunk check --all --no-fix --jobs=2` checks the full repository during quality-tooling maintenance.

## Coding Style & Naming Conventions

- Python with 4-space indentation and Black-compatible formatting.
- Use `snake_case` for functions/variables and `UPPER_CASE` for module constants (e.g., `API_BASE`).
- Keep script filenames in kebab-case to match `generate-wakatime-svg.py`.

## Testing Guidelines

- `uv run --frozen python tests/test_project_rows.py` checks that project bars encode time share; it needs no API key.
- `python3 .trunk/configs/tests/test_trufflehog_to_sarif.py` runs the offline filesystem JSONL reader regression tests with the standard library only.
- Place application tests in `tests/` and Trunk reader tests in `.trunk/configs/tests/`; name files `test_*.py`.
- Document new test commands in this file and keep them runnable from the repo root.

## Commit & Pull Request Guidelines

- Commit messages follow Conventional Commits: `type: subject` (e.g., `feat: ...`, `chore: ...`, `ci: ...`).
- PRs should describe the change, note any workflow impact, and include local reproduction steps when SVG output changes.
- Link relevant issues or discussions when available.

## Security & Configuration Notes

- Provide `WAKATIME_API_KEY` via environment variables only; never commit secrets.
- GitHub Actions expects the key in `secrets.WAKATIME_API_KEY`.
- TruffleHog scans files with `--no-verification` so candidate credentials are not sent to verification endpoints.
- Its local JSONL reader retains decoded findings at file level when the raw value is absent from the file and omits secret values from SARIF messages.

## Offline scanner resource boundary

Run `python3 -B .trunk/configs/tests/test_trufflehog_to_sarif.py` for the 17 command-line reader regressions.
Source context is limited to 1 MiB plus a sentinel byte per read and at most eight cached files.
Oversized, unreadable, binary or decoded-only findings retain file-level diagnostics instead of disappearing.
Native Trunk paths and Unicode code-point columns are preserved.
The large-source and multi-file regressions measure traced Python allocations on ASCII fixtures; they do not establish a universal process RSS or I/O timeout bound.
Malformed scanner input fails the gate, and candidate credentials are never verified with a provider.
