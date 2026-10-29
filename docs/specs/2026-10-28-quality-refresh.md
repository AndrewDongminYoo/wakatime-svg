# Quality Tooling Refresh

## Approved Scope

Refresh supported dependencies and existing quality tooling.
Preserve public APIs, generated artifacts and repository-specific boundaries.

Raise the Requests minimum from `2.32.5` to the already resolved `2.34.2` release and regenerate `uv.lock` with uv.
Check Requests and each resolved transitive dependency against public PyPI metadata.
Do not add runtime dependencies or change the Python `3.14` selection.

Update the existing OSV Scanner, oxipng and TruffleHog pins to `2.7.0`, `10.2.1` and `3.99.7` respectively.
Preserve Trunk CLI `1.25.0`, plugin ref `v1.11.0`, the configured runtimes and the deliberate Grype/SVGO exclusions unless a concrete incompatibility requires a scoped repair.
Keep the Bandit test exclusion because the offline regression tests intentionally use assertions.
Use `--no-verification` instead of `--only-verified` in TruffleHog's scan command.
Preserve its JSON output, inherited SARIF handling, success codes and `copy_targets` sandbox.
Replace the inherited JSON-to-SARIF reader with the reviewed shared maintenance filesystem reader so decoded findings remain visible when the raw value does not occur literally in the file.
Use `direct_configs` to include the reader in Trunk's configuration and cache inputs.
Keep its standard-library tests in `.trunk/configs/tests/` and run them in CI before dependency installation.
Retain the existing `tests/**` Bandit exclusion; suppress only the observed subprocess import and two invocation warnings on the three test lines that exercise the reader's command-line boundary without a shell.

## Acceptance

- Pinact remains locked to `4.1.1` with `lint` and `upgrade`.
- The full no-fix Trunk scan and declared project gates pass.
- Changed manifests have package-manager-generated lockfiles under repository policy.
- Advisory dispositions have specific evidence and affected knowledge claims are reconciled.
- Direct OSV scanning of `uv.lock` reports every resolved PyPI package, with package names and versions compared against the lockfile.
- Coverage validation rejects a report with an omitted package before accepting the real report.
- A synthetic fake canary reaches the configured TruffleHog JSON-to-SARIF reader without live credential verification; a clean fixture reports no finding.
- The inherited reader fails the decoded-only regression before the local reader passes all 17 filesystem-reader tests.
- Direct cached scanner/reader controls retain encoded and literal synthetic findings, omit their values from SARIF and keep clean input empty.
- No API key, real WakaTime response or generated chart is needed for local verification.

## Verification Boundaries

Run `uv sync --frozen`, `uv run --frozen python tests/test_project_rows.py` and `trunk check --all --no-fix --jobs=2`.
Use the already installed managed Python interpreter and disable Python downloads during local uv checks.
The synthetic regression tests inspect project-row bar widths; they do not verify WakaTime network access or the publishing action.
Do not execute the live generator or the output-branch publisher.
Disable Pinact's automatic GitHub CLI credential lookup during local checks while keeping its locked `lint` and `upgrade` commands enabled.
An unauthenticated public-metadata request hit GitHub's API rate limit during the final scan.
The retry supplies the existing GitHub credential only to the child process for public Action metadata while keeping automatic lookup disabled.
No credential value is logged and no WakaTime API key or publishing path is used.
The setup-uv references in CI and the public Action use the verified `v10.3.3` commit.
The reader follow-up uses only the 17 standard-library reader tests, cached checks on the explicit changed files and offline scanner/reader controls while the shared heavy-job slot is unavailable.
The root agent runs the configured-Trunk controls, full scan and final review.

## Sources and Precedent

The dependency review uses the public PyPI JSON metadata for [Requests](https://pypi.org/pypi/requests/json), [certifi](https://pypi.org/pypi/certifi/json), [charset-normalizer](https://pypi.org/pypi/charset-normalizer/json), [idna](https://pypi.org/pypi/idna/json) and [urllib3](https://pypi.org/pypi/urllib3/json).
Tool updates use the upstream [OSV Scanner](https://github.com/google/osv-scanner/releases/tag/v2.7.0), [oxipng](https://github.com/oxipng/oxipng/releases/tag/v10.2.1) and [TruffleHog](https://github.com/trufflesecurity/trufflehog/releases/tag/v3.99.7) release metadata supplied for this maintenance run.

The root agent supplied account-neutral precedent from `wiki/concepts/trunk-quality-gate-agent.md` and `wiki/concepts/trunk-vulnerability-triage.md` at source commit `9670d54de3076c5239713f54900c7a855bd18478`.
It confirms no-fix checks, minimal compatibility repairs and remediation through the resolved dependency graph.
Retrieval freshness is unverified and the query was partial; no direct project-specific precedent was established \[no precedent found\].

## Publication

Push and PR creation require explicit repository-specific approval.
After approval, continue the requested hosted gates, merge, cleanup and memory recording.

## Offline scanner resource boundary

Run `python3 -B .trunk/configs/tests/test_trufflehog_to_sarif.py` for the 17 command-line reader regressions.
Source context is limited to 1 MiB plus a sentinel byte per read and at most eight cached files.
Oversized, unreadable, binary or decoded-only findings retain file-level diagnostics instead of disappearing.
Native Trunk paths and Unicode code-point columns are preserved.
The large-source and multi-file regressions measure traced Python allocations on ASCII fixtures; they do not establish a universal process RSS or I/O timeout bound.
Malformed scanner input fails the gate, and candidate credentials are never verified with a provider.
