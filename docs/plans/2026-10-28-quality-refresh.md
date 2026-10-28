# Quality Tooling Refresh Plan

## Work

1. Verify repository identity, instructions, current changes and Oracle precedent → verify: exact Git root, personal origin, branch and preserved inherited index patch.
2. Refresh the Requests minimum and three outdated enabled linter pins → verify: public package metadata, `uv lock --upgrade` and `uv tree --locked`.
3. Install the locked dependency graph and exercise synthetic project-row fixtures → verify: `uv sync --frozen` and `uv run --frozen python tests/test_project_rows.py`.
4. Scan the actual resolved dependencies and validate coverage → verify: OSV Scanner `2.7.0` with `--all-packages`, then a validator that rejects an omitted-package negative control.
5. Confirm TruffleHog candidate detection without live verification → verify: the resolved command and existing JSON-to-SARIF reader distinguish clean and synthetic fake-canary fixtures.
6. Check all repository files without fixes after the shared scan slot is granted → verify: `trunk check --all --no-fix --jobs=2` and a scoped repair only for evidenced failures.
7. Audit affected documentation and the final candidate → verify: internal links, documented commands, runtime selection, action defaults, `git diff --check` and the preserved staged patch.
8. Return evidence to the root agent for local commits and the publication decision.

## Declared Gates

- `uv sync --frozen`
- `uv run --frozen python tests/test_project_rows.py`
- `.trunk/tools/osv-scanner scan source --lockfile=uv.lock --format=json --all-packages --all-vulns`
- `trunk check --all --no-fix --jobs=2`
- `git diff --check`

## Evidence

Keep command logs, exit codes, package metadata and coverage validation in the visible review directory outside the repository.
Preserve the original author-unknown staged Trunk patch without changing the index.
Publication remains a separate operator decision.
