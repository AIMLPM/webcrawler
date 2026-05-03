# Fix Plan: Resolve Global Binary Divergence + Prevent Regression

## Part A — Operator Steps to Resolve the Live Drift

The publish pipeline is healthy and `0.9.3` is already on PyPI (published 2026-04-26). The only action needed for the immediate bug is upgrading the local install. **No republish is required for this drift.** A v0.10.0 release is the natural carrier for the v3 improvements (exponential 429 backoff with jitter, plus the CI guardrail below).

### A1. Resolve the live install drift (immediate, ~30s)

```bash
# Confirm current installed version (expect 0.4.1)
pip3 show markcrawl | grep -E "Version|Location"

# Upgrade against the same Python that owns /opt/homebrew/bin/markcrawl
pip3 install --upgrade markcrawl

# Verify
markcrawl --help | grep -E "screenshot|seed-file|smart-sample|dry-run|download-images" | wc -l
# Expect: 12+ matching lines
```

If `pip3` resolves to a different Python than the one backing `/opt/homebrew/bin/markcrawl`, run `head -1 /opt/homebrew/bin/markcrawl` to see the shebang and use that interpreter's `-m pip install --upgrade markcrawl` instead.

### A2. Cut v0.10.0 (after `initial_build` lands the v3 fixes)

1. Bump `pyproject.toml` `version = "0.10.0"`. Rationale: **minor** bump — backoff change is internal behavior, not a flag rename or API break, and `0.10-rc1` is already a tag in the repo for a parallel research track. Going from `0.9.3` to `0.10.0` honors the existing `v0.10-rc1` lineage.
2. Build locally and sanity-check before tagging:
   ```bash
   python -m build
   pip install --force-reinstall dist/markcrawl-0.10.0-py3-none-any.whl
   markcrawl --help | grep screenshot   # must show all screenshot flags
   ```
3. Tag and push:
   ```bash
   git tag v0.10.0 -m "v0.10.0: exponential 429 backoff with jitter + Retry-After honoring"
   git push origin main --tags
   ```
4. Cut a GitHub Release on the tag. The existing `publish.yml` (trusted publisher, OIDC) auto-fires on `release: published` and uploads to PyPI within ~2 minutes. No twine credentials needed.
5. Post-publish verification (the smoke job below also gates this):
   ```bash
   pip install markcrawl==0.10.0 --force-reinstall
   markcrawl --help | grep --count screenshot   # >=5
   ```

### A3. Versioning rule going forward

- **Patch** (`0.10.0 → 0.10.1`): bug fixes that don't change the `--help` flag set or change exit codes.
- **Minor** (`0.10.0 → 0.11.0`): new flags, new optional dependencies, new behaviors guarded by flags.
- **Major** (`0.x → 1.0`): removing/renaming flags, changing default behaviors, breaking the library API.

## Part B — CI Guardrail: Catch Source/Published Drift Automatically

Add a new workflow that runs on every published release **and** on a nightly cron. It installs the just-published wheel from PyPI in a fresh container and asserts the advertised flag set matches what `cli.py` expects. If `markcrawl --help` is missing flags after a publish, this fails loudly so the next release can correct it instead of waiting for a downstream consumer to file a bug.

Create `.github/workflows/published-smoke.yml`:

```yaml
name: Published Smoke Test

on:
  release:
    types: [published]
  schedule:
    - cron: "0 14 * * *"   # daily 14:00 UTC catches drift even without a release
  workflow_dispatch:

jobs:
  verify-pypi-flags:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Read source version
        id: ver
        run: |
          v=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
          echo "version=$v" >> "$GITHUB_OUTPUT"

      - name: Wait for PyPI to index the new release (release event only)
        if: github.event_name == 'release'
        run: |
          for i in {1..30}; do
            if pip index versions markcrawl 2>/dev/null | grep -q "${{ steps.ver.outputs.version }}"; then
              echo "Found ${{ steps.ver.outputs.version }} on PyPI"; exit 0
            fi
            echo "Waiting for PyPI... attempt $i"; sleep 10
          done
          echo "PyPI did not index the new version in 5 minutes"; exit 1

      - name: Install from PyPI in a clean env
        run: |
          python -m venv /tmp/smoke-venv
          /tmp/smoke-venv/bin/pip install --upgrade pip
          # On nightly cron, install whatever's latest. On release, pin to the
          # version we just cut.
          if [ "${{ github.event_name }}" = "release" ]; then
            /tmp/smoke-venv/bin/pip install "markcrawl==${{ steps.ver.outputs.version }}"
          else
            /tmp/smoke-venv/bin/pip install --upgrade markcrawl
          fi

      - name: Assert advertised flags are present
        run: |
          set -euo pipefail
          help_out=$(/tmp/smoke-venv/bin/markcrawl --help)
          required_flags=(
            --screenshot
            --screenshot-viewport
            --screenshot-selector
            --screenshot-format
            --screenshot-wait-ms
            --no-screenshot-full-page
            --download-images
            --min-image-size
            --seed-file
            --max-pages-per-site
            --smart-sample
            --dry-run
          )
          missing=()
          for f in "${required_flags[@]}"; do
            if ! grep -q -- "$f" <<<"$help_out"; then
              missing+=("$f")
            fi
          done
          if (( ${#missing[@]} > 0 )); then
            echo "FAIL: published wheel missing ${#missing[@]} flag(s):" >&2
            printf '  %s\n' "${missing[@]}" >&2
            exit 1
          fi
          echo "PASS: all ${#required_flags[@]} required flags present in published wheel"

      - name: Assert source version matches PyPI latest (cron only)
        if: github.event_name == 'schedule'
        run: |
          source_v="${{ steps.ver.outputs.version }}"
          pypi_v=$(/tmp/smoke-venv/bin/pip index versions markcrawl | head -1 | sed -E 's/.*\(([^)]+)\).*/\1/')
          if [ "$source_v" != "$pypi_v" ]; then
            echo "DRIFT: source pyproject.toml = $source_v, PyPI latest = $pypi_v" >&2
            echo "Cut a release for $source_v if the new version is intentional." >&2
            exit 1
          fi
          echo "PASS: source $source_v == PyPI $pypi_v"
```

### Why this catches the v3 bug

- **Release path**: every `git tag v… && release` triggers a fresh container that talks to PyPI exactly the way an end-user does. If `publish.yml` ever silently uploads a stale wheel, `--help` won't have the new flags and the job fails before users notice.
- **Nightly cron**: even if no one cuts a release, the cron job compares `pyproject.toml` to PyPI and yells if the source has moved forward without a publish. This is the exact failure mode that produced bug fe6f3c39 — code merged to `main` faster than releases were cut.
- **Belt + suspenders**: the daily cron also re-verifies that the *currently published* wheel still lists every flag, so a future regression in `cli.py` (e.g., a refactor that drops a flag) gets caught within 24 hours instead of via downstream consumer bug reports.

### Required-flags maintenance

Whenever `cli.py` adds a user-facing flag, append it to the `required_flags` array in `published-smoke.yml`. The `initial_build` stage should ship this CI file with the array seeded from the current `cli.py` flag inventory.
