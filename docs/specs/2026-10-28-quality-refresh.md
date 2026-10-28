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
Override only TruffleHog's scan command to use `--no-verification` instead of `--only-verified`.
Preserve its JSON output, failure exit behavior and existing JSON-to-SARIF reader.

## Acceptance

- Pinact remains locked to `4.1.1` with `lint` and `upgrade`.
- The full no-fix Trunk scan and declared project gates pass.
- Changed manifests have package-manager-generated lockfiles under repository policy.
- Advisory dispositions have specific evidence and affected knowledge claims are reconciled.
- Direct OSV scanning of `uv.lock` reports every resolved PyPI package, with package names and versions compared against the lockfile.
- Coverage validation rejects a report with an omitted package before accepting the real report.
- A synthetic fake canary reaches the configured TruffleHog JSON-to-SARIF reader without live credential verification; a clean fixture reports no finding.
- No API key, real WakaTime response or generated chart is needed for local verification.

## Verification Boundaries

Run `uv sync --frozen`, `uv run --frozen python tests/test_project_rows.py` and `trunk check --all --no-fix --jobs=2`.
Use the already installed managed Python interpreter and disable Python downloads during local uv checks.
The synthetic regression tests inspect project-row bar widths; they do not verify WakaTime network access or the publishing action.
Do not execute the live generator or the output-branch publisher.
Disable Pinact's automatic GitHub CLI credential lookup during local checks while keeping its locked `lint` and `upgrade` commands enabled.

## Sources and Precedent

The dependency review uses the public PyPI JSON metadata for [Requests](https://pypi.org/pypi/requests/json), [certifi](https://pypi.org/pypi/certifi/json), [charset-normalizer](https://pypi.org/pypi/charset-normalizer/json), [idna](https://pypi.org/pypi/idna/json) and [urllib3](https://pypi.org/pypi/urllib3/json).
Tool updates use the upstream [OSV Scanner](https://github.com/google/osv-scanner/releases/tag/v2.7.0), [oxipng](https://github.com/oxipng/oxipng/releases/tag/v10.2.1) and [TruffleHog](https://github.com/trufflesecurity/trufflehog/releases/tag/v3.99.7) release metadata supplied for this maintenance run.

The root agent supplied account-neutral precedent from `wiki/concepts/trunk-quality-gate-agent.md` and `wiki/concepts/trunk-vulnerability-triage.md` at source commit `9670d54de3076c5239713f54900c7a855bd18478`.
It confirms no-fix checks, minimal compatibility repairs and remediation through the resolved dependency graph.
Retrieval freshness is unverified and the query was partial; no direct project-specific precedent was established \[no precedent found\].

## Publication

Push and PR creation require explicit repository-specific approval.
After approval, continue the requested hosted gates, merge, cleanup and memory recording.
