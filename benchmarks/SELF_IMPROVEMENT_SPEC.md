# Benchmark Self-Improvement Spec

**Purpose:** Reference document for reviewing code quality, resilience, data
lineage, and improvement opportunities across the benchmark suite. Point to
this file whenever you want a full audit.

**Last reviewed:** 2026-04-08

---

## Table of Contents

1. [Data Lineage](#1-data-lineage) -- what feeds each report
2. [Resilience & Restart](#2-resilience--restart) -- what survives interruption, what doesn't
3. [Code Quality](#3-code-quality) -- issues ranked by impact
4. [Actionable Improvements](#4-actionable-improvements) -- concrete fixes
5. [Known Tool Limitations](#5-known-tool-limitations) -- gaps that aren't bugs
6. [Review Checklist](#6-review-checklist) -- quick audit procedure

---

## 1. Data Lineage

### 1.1 Report Generation Map

```
                     .url_cache.json
                           |
                           v
                 benchmark_all_tools.py
                   /         |         \
                  v          v          v
             runs/run_*/  SPEED_COMPARISON.md  QUALITY_COMPARISON.md
                  |
        +---------+---------+---------+
        v         v         v         v
  benchmark_   benchmark_  benchmark_  benchmark_
  retrieval.py answer_     quality.py  markcrawl.py
        |      quality.py      |           |
        v         v            v           v
  RETRIEVAL_   ANSWER_     (feeds into   MARKCRAWL_
  COMPARISON   QUALITY     QUALITY_      RESULTS.md
  .md          .md         COMPARISON)
        \         |
         \        v
          +-> COST_AT_SCALE.md  (hand-written, derives from above)
              METHODOLOGY.md    (hand-written reference)
```

### 1.2 Per-Report Input Table

| Report | Generator | Run Data | Checkpoints | External API | Hand-Edit |
|--------|-----------|----------|-------------|--------------|-----------|
| SPEED_COMPARISON.md | `benchmark_all_tools.py` | `runs/run_*/` timing + page counts | `.benchmark_checkpoint.json` | None | No |
| QUALITY_COMPARISON.md | `benchmark_quality.py` | `runs/run_*/pages.jsonl` | None | None | No |
| RETRIEVAL_COMPARISON.md | `benchmark_retrieval.py` | `runs/run_*/pages.jsonl` | `retrieval_checkpoints/` + `embed_cache/` | OpenAI Embeddings | No |
| RETRIEVAL_FASTAPI_200.md | `benchmark_retrieval.py --site fastapi-docs` | Same | Same | Same | No |
| RETRIEVAL_COMPARISON_CONTEXT.md | `benchmark_retrieval.py --context-headers` | Same | Same | Same | No |
| ANSWER_QUALITY.md | `benchmark_answer_quality.py` | `runs/run_*/pages.jsonl` | `answer_quality_checkpoints/` | OpenAI Chat (gpt-4o-mini) | No |
| MARKCRAWL_RESULTS.md | `benchmark_markcrawl.py` | Live crawl (no run dir) | None | None | No |
| COST_AT_SCALE.md | Manual | Derives chunk ratios from RETRIEVAL + quality scores from ANSWER_QUALITY | None | None | **Yes** |
| METHODOLOGY.md | Manual | None | None | None | **Yes** |

### 1.3 Shared Data Dependencies

**Test queries** (92 total across 8 sites) are defined in
`benchmark_retrieval.py` lines 81-280 and imported by
`benchmark_answer_quality.py`. Changing a query invalidates both retrieval
and answer quality checkpoints for that site.

**Chunking** uses `markcrawl.chunker.chunk_markdown()` with default config
(~400 words, 50-word overlap, labelled `~512tok`). All retrieval and answer
quality results depend on this chunker. A chunker change invalidates all
`retrieval_checkpoints/` and `answer_quality_checkpoints/`.

**Embedding model** is `text-embedding-3-small` (1536 dims), hardcoded in
`benchmark_retrieval.py` line 731. Changing this invalidates all
`embed_cache/` files (~20 GB).

### 1.4 Cache Locations & Sizes

| Cache | Location | Size | Key | Cleared By |
|-------|----------|------|-----|------------|
| URL discovery | `.url_cache.json` | ~110 KB | site name | `--refresh-urls` |
| Speed checkpoint | `.benchmark_checkpoint.json` | ~50 KB | run args hash | `--no-resume` or successful completion |
| Embeddings | `embed_cache/` | ~20 GB | SHA256 of text batch | `--fresh` on retrieval script |
| Retrieval results | `retrieval_checkpoints/` | ~23 MB | `run__tool__site__config` | `--fresh` or manual delete |
| Answer quality | `answer_quality_checkpoints/` | ~1 MB | `run__tool__site` | `--fresh` or manual delete |

---

## 2. Resilience & Restart

### 2.1 Current State: What Survives Interruption

| Script | Checkpoint? | Granularity | What's Lost on Interrupt |
|--------|------------|-------------|--------------------------|
| `benchmark_all_tools.py` | Yes | Per tool-site pair | Current tool-site iteration (minutes). Temp dir data if not yet copied to `runs/`. |
| `benchmark_retrieval.py` | Yes | Per tool-site pair | Current site's embedding progress. Partially embedded batches ARE cached (embed_cache saves per-batch). |
| `benchmark_answer_quality.py` | Yes | Per tool-site pair | All answers for the current site being processed (no per-query checkpoint). |
| `benchmark_quality.py` | **No** | N/A | Everything. Must restart from scratch. |
| `benchmark_markcrawl.py` | **No** | N/A | Everything. Temp dir leaks on interrupt. |
| `crawlee_worker.py` | **No** | N/A | Partial pages.jsonl (append mode, may have truncated last line). |

### 2.2 Data Loss Risks (Ranked by Impact)

**HIGH:**

1. **Partial JSONL corruption** -- `crawlee_worker.py` and all tool runners
   open `pages.jsonl` in append mode ("a") and write `json.dumps() + "\n"`.
   If interrupted between the write and newline (or mid-write), the last line
   is truncated JSON. Downstream scripts (`benchmark_retrieval.py`,
   `benchmark_quality.py`) call `json.loads()` per line and crash on the
   corrupt line. No script validates JSONL integrity before processing.

2. **Embed cache unbounded growth** -- `embed_cache/` grows to ~20 GB and
   has no eviction, size limit, or cleanup. Re-embedding with different
   chunk sizes creates new cache entries without removing old ones. Disk
   exhaustion causes silent failures (Python OSError on write).

3. **Answer quality loses entire site on interrupt** -- If `benchmark_
   answer_quality.py` is interrupted while processing site 4/8, all
   answers for site 4 are lost (checkpoint saved only after all queries
   for a site complete). With 10-15 queries per site at ~$0.002 each and
   ~30s per query, losing a site wastes ~5 min + $0.03.

**MEDIUM:**

4. **Colly URL rewriting is destructive** -- `benchmark_quality.py`
   `_fix_colly_jsonl()` rewrites `pages.jsonl` in place. If interrupted
   mid-write, the file is corrupted with no backup.

5. **Checkpoint invalidation on arg change** -- `benchmark_all_tools.py`
   discards the entire checkpoint if `--iterations` or `--concurrency`
   changes. After 6 hours of crawling 7 tools, changing `--concurrency`
   from 5 to 10 means starting over.

6. **Temp directory leaks** -- `benchmark_markcrawl.py` creates temp dirs
   (~50 MB each) and doesn't clean up on exception. Over time, `/tmp`
   fills up.

**LOW:**

7. **Speed report generated once at end** -- `benchmark_all_tools.py`
   generates the report only after all tools complete. If you want
   intermediate results, you must read the checkpoint JSON manually.

8. **No file locking** -- Multiple benchmark runs can write to the same
   checkpoint files simultaneously. Not a practical risk (users don't
   run two instances), but could cause corruption in CI.

### 2.3 Proposed Resilience Improvements

**R1. JSONL atomic writes** -- Write each page to a temp file, then
`os.replace()` into `pages.jsonl`. Or: write to `pages.jsonl.tmp` and
rename on completion. Simpler alternative: validate JSONL on load and
skip corrupt trailing lines with a warning.

**R2. Per-query answer checkpoints** -- Save after each query, not after
each site. Change checkpoint format from `List[AnswerResult]` to append
one JSON line per query to a `.jsonl` file. Resume by counting existing
lines.

**R3. Embed cache size limit** -- Add LRU eviction or a `--max-cache-size`
flag. Default to 30 GB. Delete oldest files (by mtime) when limit exceeded.

**R4. Non-destructive colly URL fix** -- Write corrected JSONL to a new
file, then `os.replace()`. Keep `.bak` if the original is modified.

**R5. Graceful checkpoint arg changes** -- Allow partial checkpoint reuse
when only concurrency changes (timing data is invalid but page data is
still valid). Separate "crawl data" from "timing data" in checkpoint.

**R6. JSONL validation on load** -- Add a `_load_jsonl_safe(path)` helper
that skips corrupt trailing lines and logs a warning. Use everywhere
JSONL is loaded.

---

## 3. Code Quality

### 3.1 Issues Ranked by Impact

**Critical (causes incorrect results or data loss):**

| ID | File | Issue | Line(s) |
|----|------|-------|---------|
| CQ1 | `crawlee_worker.py` | No error handling around `crawler.run()` -- exception kills process, partial JSONL remains | 73-76 |
| CQ2 | `benchmark_quality.py` | `_fix_colly_jsonl()` rewrites input file in place with no backup | 45-109 |
| CQ3 | `benchmark_all_tools.py` | `run_crawlee()` silently discards stderr -- failures invisible | 959 |
| CQ4 | `benchmark_retrieval.py` | Checkpoint write is not atomic (`json.dump` directly to file) | 1653-1660 |

**High (affects maintainability or reliability):**

| ID | File | Issue | Line(s) |
|----|------|-------|---------|
| CQ5 | All scripts | `print()` instead of `logging` -- no log levels, no file output, no timestamps | Everywhere |
| CQ6 | All scripts | Hardcoded model names, timeouts, limits -- no config file | See below |
| CQ7 | `benchmark_retrieval.py` | No retry/backoff for OpenAI API calls -- rate limit = crash | 785-858 |
| CQ8 | `benchmark_all_tools.py` | Generic `except Exception` in 6+ places -- hides root cause | 373, 380, 586, 609, 669 |
| CQ9 | `crawlee_worker.py` | `safeFilename()` truncates to 80 chars -- two URLs can collide | 56 |

**Medium (code smell, technical debt):**

| ID | File | Issue | Line(s) |
|----|------|-------|---------|
| CQ10 | `benchmark_all_tools.py` | Global `_checkpoint_lock`, `_rate_limit_wait` on function objects | Various |
| CQ11 | `benchmark_retrieval.py` | Modifies global `RETRIEVAL_MODES` list based on CLI args | 1883-1885 |
| CQ12 | `benchmark_answer_quality.py` | Tight coupling: imports `TEST_QUERIES` from `benchmark_retrieval` | 1 |
| CQ13 | `quality_scorer.py` | 54 hardcoded junk phrases -- not configurable | 30-54 |
| CQ14 | `lint_reports.py` | `ALL_TOOLS` set hardcoded -- must update when adding tools | 54 |
| CQ15 | All scripts | Limited type hints -- most functions lack return types | Everywhere |

### 3.2 Hardcoded Values Inventory

| Value | Location | Current | Should Be |
|-------|----------|---------|-----------|
| Embedding model | `benchmark_retrieval.py:731` | `text-embedding-3-small` | Config/env var |
| Answer model | `benchmark_answer_quality.py` | `gpt-4o-mini` | Config/env var |
| Judge model | `benchmark_answer_quality.py` | `gpt-4o-mini` | Config/env var |
| Reranker model | `benchmark_retrieval.py` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Config/env var |
| Chunk size | `benchmark_retrieval.py` | 400 words, 50 overlap | Config/env var |
| TOP_K retrieval | `benchmark_retrieval.py` | 50 | Config/env var |
| TOP_K for answers | `benchmark_answer_quality.py` | 10 | Config/env var |
| Subprocess timeout | `benchmark_all_tools.py` | 300s | Per-tool config |
| Colly parallelism | `colly_crawler/main.go` | 5 | CLI flag |
| Colly request timeout | `colly_crawler/main.go` | 30s | CLI flag |
| URL filename max | `crawlee_worker.py:56` | 80 chars | 200+ chars |
| Max runs kept | `benchmark_all_tools.py` | 10 | Config/env var |
| Junk phrases | `quality_scorer.py:30-54` | 54 phrases | External file |
| Memory sample interval | `benchmark_all_tools.py` | 0.5s | Config |

---

## 4. Actionable Improvements

### 4.1 Priority 1: Data Integrity

**A1. Add JSONL load validation**

Create a shared helper used by all scripts:

```python
# benchmarks/utils.py
def load_jsonl_safe(path: Path) -> list[dict]:
    """Load JSONL, skipping corrupt trailing lines."""
    results = []
    with open(path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"WARNING: {path}:{i} — corrupt JSON, skipping")
    return results
```

**A2. Atomic checkpoint writes**

Replace direct `json.dump()` with write-to-temp + rename:

```python
def _save_checkpoint_atomic(path: Path, data: dict):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)
```

Apply to: `benchmark_retrieval.py` checkpoints,
`benchmark_answer_quality.py` checkpoints, `benchmark_quality.py` colly
fix.

**A3. Per-query answer checkpoints**

Change `benchmark_answer_quality.py` to append one JSON line per
completed query (instead of saving all at once per site). On resume,
count lines and skip that many queries.

### 4.2 Priority 2: Observability

**A4. Replace print() with logging**

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("benchmarks/benchmark.log"),
    ],
)
log = logging.getLogger(__name__)
```

Benefits: timestamps, log levels, file output for post-mortem analysis,
`DEBUG` level for verbose mode.

**A5. Add a `--dry-run` mode to benchmark_all_tools.py**

Show what would be crawled, estimated time, and which checkpoints exist,
without actually crawling. Helps verify setup before a multi-hour run.

### 4.3 Priority 3: Configuration

**A6. Create `benchmarks/config.yaml`**

Move all hardcoded values to a single config file:

```yaml
models:
  embedding: text-embedding-3-small
  answer: gpt-4o-mini
  judge: gpt-4o-mini
  reranker: cross-encoder/ms-marco-MiniLM-L-6-v2

chunking:
  max_words: 400
  overlap_words: 50
  label: "~512tok"

retrieval:
  top_k: 50
  report_at_k: [1, 3, 5, 10, 20]
  rrf_k: 60

limits:
  subprocess_timeout_s: 300
  max_runs_kept: 10
  url_filename_max_chars: 200
  embed_cache_max_gb: 30
  memory_sample_interval_s: 0.5

tools:
  colly:
    parallelism: 5
    request_timeout_s: 30
  crawlee:
    subprocess_timeout_s: 300
  firecrawl:
    batch_size: 5
    wait_for_spa_ms: 15000
```

### 4.4 Priority 4: Resilience

**A7. API retry with exponential backoff**

Add to `benchmark_retrieval.py` and `benchmark_answer_quality.py`:

```python
import time

def _api_call_with_retry(fn, max_retries=5):
    for attempt in range(max_retries):
        try:
            return fn()
        except openai.RateLimitError:
            wait = 2 ** attempt
            log.warning(f"Rate limited, retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"API call failed after {max_retries} retries")
```

**A8. Embed cache eviction**

Add LRU cleanup to `embed_cache/`:

```python
def _evict_embed_cache(max_gb=30):
    cache_dir = EMBED_CACHE_DIR
    files = sorted(cache_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)
    total = sum(f.stat().st_size for f in files)
    while total > max_gb * 1e9 and files:
        oldest = files.pop(0)
        total -= oldest.stat().st_size
        oldest.unlink()
```

**A9. Graceful interrupt handling**

Add signal handler to long-running scripts:

```python
import signal

_interrupted = False

def _handle_sigint(sig, frame):
    global _interrupted
    _interrupted = True
    log.warning("Interrupt received — finishing current task, then saving checkpoint")

signal.signal(signal.SIGINT, _handle_sigint)
```

Check `_interrupted` in the main loop after each tool-site pair.

---

## 5. Known Tool Limitations

These are not bugs -- they are inherent to each tool's architecture and
should be documented in reports, not "fixed."

| Tool | Site | Pages | Limitation | Root Cause |
|------|------|-------|------------|------------|
| firecrawl | react-dev | 43/221 (19%) | Anti-bot detection | Self-hosted Firecrawl lacks cloud `fire-engine` anti-bot bypass. react.dev detects automated Playwright and blocks after ~5 requests. |
| firecrawl | stripe-docs | 395/402 (98%) | OOM on 7 pages | 7 large API reference pages exceed Node.js V8 heap limit. Harness kills all services on any worker OOM. |
| firecrawl | wikipedia | 1/50 (speed run) | Inconsistent | Works in retrieval run (50 pages) but failed in speed run. Likely transient Docker resource pressure. |
| crawlee | stripe-docs | 221/402 (55%) | Partial coverage | Crawlee's Playwright timed out on some stripe-docs pages. Not re-investigated. |
| scrapy+md | python-docs | 429/500 (86%) | HTTP-only | Scrapy doesn't render JS; some python-docs pages require it. |
| playwright | wikipedia | 41/50 (82%) | Minor | 9 pages timed out or returned empty content. |
| colly+md | stripe-docs | 402/402 but huge chunks | Not a gap | Colly fetches raw HTML; markdownify preserves all content including nav/footer, inflating chunk counts. |

---

## 6. Review Checklist

Use this checklist when running a full audit of the benchmark suite.

### Data Freshness

- [ ] Which `runs/run_*` directory are the reports generated from?
      Check line 2 of each report for the generation timestamp.
- [ ] Do the page counts in RETRIEVAL_COMPARISON.md match the actual
      `pages.jsonl` line counts in the run directory?
      ```bash
      for tool in markcrawl crawl4ai crawl4ai-raw scrapy+md crawlee colly+md playwright firecrawl; do
        for site in runs/run_20260408_023403/$tool/*/; do
          echo "$tool/$(basename $site): $(wc -l < $site/pages.jsonl 2>/dev/null || echo MISSING)"
        done
      done
      ```
- [ ] Are there stale retrieval checkpoints?
      Compare checkpoint mtimes to `pages.jsonl` mtimes:
      ```bash
      ls -lt retrieval_checkpoints/ | head -20
      ```
      If a checkpoint is older than its source data, delete it and re-run.

### Report Consistency

- [ ] Do all summary tables include all 8 tools?
- [ ] Are tables sorted by primary metric (descending)?
- [ ] Is markcrawl's row bold in summary tables?
- [ ] Do cross-references point to existing files?
      ```bash
      grep -rn '\[.*\](.*\.md)' benchmarks/*.md | grep -v node_modules
      ```
- [ ] Run the linter:
      ```bash
      python benchmarks/lint_reports.py
      ```

### Data Integrity

- [ ] Check for corrupt JSONL files (truncated last line):
      ```bash
      for f in runs/run_20260408_023403/*/*/pages.jsonl; do
        python3 -c "
      import json, sys
      with open('$f') as fh:
        for i, line in enumerate(fh, 1):
          try: json.loads(line)
          except: print(f'CORRUPT {f}:{i}')
      " 2>/dev/null
      done
      ```
- [ ] Check embed_cache size:
      ```bash
      du -sh benchmarks/embed_cache/
      ```
- [ ] Check for duplicate URLs in pages.jsonl:
      ```bash
      for f in runs/run_20260408_023403/*/*/pages.jsonl; do
        dupes=$(python3 -c "
      import json
      urls = [json.loads(l)['url'] for l in open('$f')]
      print(len(urls) - len(set(urls)))
      " 2>/dev/null)
        [ "$dupes" != "0" ] && echo "DUPES: $f ($dupes)"
      done
      ```

### Code Quality

- [ ] Run the linter on reports: `python benchmarks/lint_reports.py`
- [ ] Check for bare `except Exception`: `grep -rn "except Exception" benchmarks/*.py`
- [ ] Check for hardcoded models: `grep -rn "gpt-4o\|text-embedding" benchmarks/*.py`
- [ ] Check for `print(` in non-worker scripts: `grep -cn "print(" benchmarks/benchmark_*.py`

### Resilience

- [ ] Simulate interrupt: run `benchmark_retrieval.py`, Ctrl-C after 2
      sites complete, re-run. Verify it resumes correctly.
- [ ] Check checkpoint files are valid JSON:
      ```bash
      for f in benchmarks/retrieval_checkpoints/*.json; do
        python3 -c "import json; json.load(open('$f'))" 2>/dev/null || echo "CORRUPT: $f"
      done
      ```

---

## Appendix: File Inventory

```
benchmarks/
  benchmark_all_tools.py       # Speed benchmark (1943 lines)
  benchmark_retrieval.py       # Retrieval benchmark (2018 lines)
  benchmark_answer_quality.py  # Answer quality benchmark (598 lines)
  benchmark_quality.py         # Extraction quality scoring (207 lines)
  benchmark_markcrawl.py       # Markcrawl self-test (590 lines)
  quality_scorer.py            # Quality metrics library (741 lines)
  crawlee_worker.py            # Crawlee subprocess wrapper (77 lines)
  lint_reports.py              # Report style linter (245 lines)
  colly_crawler/main.go        # Go crawler source (127 lines)
  colly_benchmark              # Compiled Go binary
  .url_cache.json              # Cached discovered URLs
  .benchmark_checkpoint.json   # Speed benchmark resume state (transient)
  embed_cache/                 # Embedding vectors (~20 GB)
  retrieval_checkpoints/       # Retrieval results (~23 MB)
  answer_quality_checkpoints/  # LLM answer results (~1 MB)
  runs/                        # Raw crawl data (last 10 runs)
  firecrawl/                   # Firecrawl Docker setup (gitignored)
  SPEED_COMPARISON.md          # Auto: speed report
  QUALITY_COMPARISON.md        # Auto: extraction quality report
  RETRIEVAL_COMPARISON.md      # Auto: retrieval quality report
  RETRIEVAL_FASTAPI_200.md     # Auto: FastAPI-focused retrieval
  RETRIEVAL_COMPARISON_CONTEXT.md  # Auto: context-augmented retrieval
  ANSWER_QUALITY.md            # Auto: LLM answer quality report
  MARKCRAWL_RESULTS.md         # Auto: markcrawl self-test report
  COST_AT_SCALE.md             # Manual: cost analysis
  METHODOLOGY.md               # Manual: methodology reference
```
