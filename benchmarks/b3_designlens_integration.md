# B3 — designlens_no_fallback (DESIGN ONLY)

## Status

**DESIGN ONLY** — full measurement is gated on two prerequisites that are
not satisfied at the moment v3 is graduating:

1. `markcrawl==0.10.0` must be **published to PyPI** so designlens can
   `pip install --upgrade markcrawl` and pick up v3.
2. **designlens** must have an active corpus-capture configuration that
   exercises markcrawl's HTTP fetch path against a JS-rendered site (the
   only path that historically fell back to `playwright.async_api`).

This benchmark documents the methodology and the operator procedure to
verify post-graduation. It will become an executable script (`b3_designlens_run.py`)
once both prerequisites are satisfied — see "Promotion" below.

## Why this dimension exists

The v3 root-cause diagnosis (`specs/v3-landscape/root-cause-diagnosis.md`)
identified that designlens was importing `playwright.async_api` directly
when it should have been delegating to markcrawl. That fallback meant
designlens missed every retry/throttle improvement markcrawl shipped —
the whole point of v3 was to *remove* the fallback so designlens could
benefit from the new tenacity-backed retry policy without code changes
on its end.

A passing B3 run proves: **designlens, after upgrading to markcrawl
v0.10.0, no longer imports `playwright.async_api` anywhere in its corpus
capture path.**

## Methodology

### What we measure

Static **and** dynamic absence of the fallback symbol in designlens's
corpus-capture process:

* **Static**: grep the active designlens code tree for any
  `from playwright.async_api import …` or `import playwright.async_api`.
  These are zero-tolerance — the spec calls for *no* fallback path, not
  "fallback only when X."
* **Dynamic**: run a designlens corpus capture against a known
  JS-heavy fixture site, capturing `sys.modules` after the run. Assert
  `playwright.async_api` is not in `sys.modules`. (A pure-static check
  could miss a dynamic `importlib` call; a pure-dynamic check could miss
  an unused import that hasn't been triggered yet. We want both.)

### Pass criteria

| Check | Threshold |
|---|---|
| Static grep hits in designlens source for `playwright.async_api` | **0** |
| `playwright.async_api in sys.modules` after a corpus capture run | **False** |
| Markcrawl version reported by designlens runtime | **≥ 0.10.0** |
| Corpus capture **completes** (we don't want a green B3 just because the run crashed before reaching the import) | **True** |

All four must hold for the benchmark to PASS.

### Why this isn't a simple unit test

The fallback path is (by design) only triggered at the *integration boundary*
between designlens and markcrawl. A pytest in either repo would have to
mock the boundary — which is what allowed the bug to slip through in the
first place. The benchmark must run real designlens against real markcrawl
on a real site.

## 2-step manual verification procedure (operator-facing)

Run these on the operator's machine **after v3 is published**.

```bash
# Step 1 — upgrade markcrawl to the published v3 wheel
python -m pip install --upgrade markcrawl
markcrawl --help | head -1                       # sanity check
python -c "import markcrawl, sys; print(markcrawl.__version__)"
# expected: 0.10.0 (or higher)

# Step 2 — re-run a designlens corpus capture and assert
cd ~/Documents/Coding/designlens                  # operator's local clone
# (a) static check first (cheap):
grep -RIn 'playwright\.async_api' designlens/ \
    && echo 'FAIL: static fallback still present' \
    || echo 'OK: no static fallback'
# (b) dynamic check via corpus capture:
python -m designlens.corpus_capture \
    --target https://react.dev \
    --trace-imports /tmp/designlens-imports.json \
    --out /tmp/designlens-corpus
python - <<'PY'
import json, sys
mods = set(json.load(open('/tmp/designlens-imports.json'))['imported_modules'])
ok = 'playwright.async_api' not in mods
print('PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
PY
```

Both echoes should print `OK` / `PASS` for B3 to be considered satisfied.
The exact `--trace-imports` flag does not yet exist in designlens — the
promotion step (below) is to add it during the designlens-side integration
work.

## Promotion to executable

When both prerequisites land, replace this doc with `b3_designlens_run.py`
implementing the procedure above. The script should:

1. Verify `markcrawl.__version__ >= 0.10.0` (skip if the pinned PyPI
   release is still behind; emit `SKIP` not `FAIL`).
2. `subprocess.run(["grep", "-RIn", "playwright.async_api",
   "<designlens_src>"])` — assert exit code 1 (no matches).
3. Spawn a designlens corpus capture as a subprocess against a fixture
   site with the import-trace flag.
4. Parse the trace JSON; assert `playwright.async_api` not in the set.
5. Emit the same JSON envelope shape as B1/B2 with
   `result ∈ {PASS, FAIL, SKIP}`.

Wire the new script into `run-all.sh` after the B2 invocation.

## Why we ship v3 without B3 executing

* B1 + B2 cover the *directly testable* surface inside this repo (CLI
  parity, retry timing) — both pass against v0.10.0 source.
* B3's failure mode would be **on the designlens side**, not markcrawl —
  if designlens still has a fallback, that's a designlens bug to fix in
  the next designlens iteration, not a markcrawl regression.
* Gating v3 graduation on a designlens-side change would create a circular
  dependency: designlens can't upgrade until markcrawl publishes; we can't
  measure until designlens upgrades.

The executable B3 lands as part of the *next* designlens improvement run,
which can also write the `--trace-imports` flag this procedure needs.
