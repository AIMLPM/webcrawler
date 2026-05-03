# Root-Cause Diagnosis: Global Binary Missing ~12 CLI Flags (Bug fe6f3c39)

## Problem Statement

The `markcrawl` binary at `/opt/homebrew/bin/markcrawl` exposes only the v0.4.1 flag set (no `--screenshot*`, `--seed-file`, `--max-pages-per-site`, `--smart-sample`, `--dry-run`, `--download-images`, `--screenshot-selector`, `--screenshot-format`, `--screenshot-wait-ms`, `--no-screenshot-full-page`, `--min-image-size`), even though the source repo at `/Users/paulsave/Documents/Coding/markcrawl/` has all of these flags wired through `markcrawl/cli.py`. The bug looked like a publishing failure, but the publish channel is healthy — the divergence is entirely **client-side**: the user's globally-installed wheel is six minor versions behind the latest published release.

## Evidence

- **Source `pyproject.toml` version** = `0.9.3`. Tag `v0.9.3` exists locally and `git merge-base --is-ancestor 612dd19 v0.9.3` confirms the screenshot commit (`Add page screenshot capture and multi-site discovery pipeline`) ships in that tag. `git show v0.9.3:markcrawl/cli.py | grep screenshot` lists every "missing" flag.
- **PyPI latest** = `0.9.3`, uploaded `2026-04-26T04:08:02Z` via the trusted-publisher `publish.yml` workflow on release tag. PyPI's full release history shows a steady cadence (15 releases between 2026-04-04 and 2026-04-26), so the publish pipeline is live and uncontested.
- **Locally installed version** = `0.4.1`, uploaded to PyPI `2026-04-13T09:22:57Z`. Reported by `pip3 show markcrawl`. Location: `/opt/homebrew/lib/python3.14/site-packages` (system Homebrew Python 3.14, not a project venv).
- **Symptoms match**: 0.4.1 predates the screenshot pipeline (612dd19 → v0.5.0+), the multi-site `--seed-file` work, and the image-download flag (dc54cf8 → v0.7.0+). Every "missing" flag was added between v0.5.0 and v0.9.0; none exist in v0.4.1.
- The repo's `publish.yml` is correct (`pypa/gh-action-pypi-publish` on `release: published`), so no build-artifact or setuptools-config pathology is in play.

## Root Cause

**Stale local install, not stale PyPI.** The Homebrew system Python's `/opt/homebrew/lib/python3.14/site-packages/markcrawl` is pinned at v0.4.1 from 2026-04-13 because no `pip install --upgrade markcrawl` has run since. PyPI has shipped 10 newer releases (0.5.0 through 0.9.3) that the local environment never picked up. The user (and any agent dogfooding the binary) has been testing against an artifact that's ~3 weeks behind reality.

## Fix to Apply

`pip3 install --upgrade markcrawl` against the system Python that owns `/opt/homebrew/bin/markcrawl`. This pulls 0.9.3 from PyPI and immediately exposes all 12 flags. To prevent recurrence, the `initial_build` stage should add a CI smoke step that does `pip install markcrawl==<source-version>` in a clean ephemeral env and asserts every advertised flag appears in `markcrawl --help` output — that catches the source-vs-published gap *before* it bites a downstream consumer (designlens, in this case). See `fix-plan.md` for the exact procedure.
