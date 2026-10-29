# Quality Tooling Refresh Plan

## Work

1. Verify repository identity, instructions, current changes and Oracle precedent → verify: exact Git root, personal origin, branch and preserved inherited index patch.
2. Refresh the Requests minimum and three outdated enabled linter pins → verify: public package metadata, `uv lock --upgrade` and `uv tree --locked`.
3. Install the locked dependency graph and exercise synthetic project-row fixtures → verify: `uv sync --frozen` and `uv run --frozen python tests/test_project_rows.py`.
4. Scan the actual resolved dependencies and validate coverage → verify: OSV Scanner `2.7.0` with `--all-packages`, then a validator that rejects an omitted-package negative control.
5. Confirm TruffleHog candidate detection without live verification → verify: the inherited reader fails the decoded-only regression, then the reviewed local filesystem reader passes all 17 standard-library tests and retains encoded/literal synthetic findings while clean input remains empty.
6. Check all repository files without fixes after the shared scan slot is granted → verify: `trunk check --all --no-fix --jobs=2` and a scoped repair only for evidenced failures.
7. Audit affected documentation and the final candidate → verify: internal links, documented commands, runtime selection, action defaults, `git diff --check` and the preserved staged patch.
8. Return evidence to the root agent for local commits and the publication decision.

## Declared Gates

- `uv sync --frozen`
- `uv run --frozen python tests/test_project_rows.py`
- `python3 .trunk/configs/tests/test_trufflehog_to_sarif.py`
- `.trunk/tools/osv-scanner scan source --lockfile=uv.lock --format=json --all-packages --all-vulns`
- `trunk check --all --no-fix --jobs=2`
- `git diff --check`

## Evidence

Keep command logs, exit codes, package metadata and coverage validation in the visible review directory outside the repository.
Preserve the original author-unknown staged Trunk patch without changing the index.
Publication remains a separate operator decision.

## Security Reader Follow-up

Copy the reviewed reader and its 17 tests from the shared maintenance implementation and record source and destination hashes.
Apply only required formatting and line-specific Bandit annotations on the new test's subprocess import and invocation.
Prove AST equality after normalizing only the initial standard-library import order.
Preserve the dependency manifest, lockfile, runtime pins, existing `tests/**` policy, offline scan flags and inherited TruffleHog SARIF settings.
Run the cheap reader tests in CI before dependency installation.

Use only cached tools on explicit paths and never-issued synthetic offline fixtures while the shared heavy-job slot is unavailable.
Keep scanner JSONL and credential-shaped fixture contents in temporary storage, persist sanitized counts and locations only, then remove the owned fixtures and diagnostics.
The root agent completes configured-Trunk controls, the full scan and final review before removing the publication blocker.

## Offline scanner resource boundary

Run `python3 -B .trunk/configs/tests/test_trufflehog_to_sarif.py` for the 17 command-line reader regressions.
Source context is limited to 1 MiB plus a sentinel byte per read and at most eight cached files.
Oversized, unreadable, binary or decoded-only findings retain file-level diagnostics instead of disappearing.
Native Trunk paths and Unicode code-point columns are preserved.
The large-source and multi-file regressions measure traced Python allocations on ASCII fixtures; they do not establish a universal process RSS or I/O timeout bound.
Malformed scanner input fails the gate, and candidate credentials are never verified with a provider.
