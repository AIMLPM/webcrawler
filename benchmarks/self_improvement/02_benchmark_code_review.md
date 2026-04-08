# Spec 02: Benchmark Code Review (without Docker)

**Scope:** All Python benchmark scripts and supporting files. Excludes Docker
infrastructure (see [Spec 03](03_docker_infra_review.md)).

**When to run:** After modifying any benchmark script, adding a new tool, or
before a major benchmark run.

---

## Files in scope

| File | Lines | Purpose |
|------|-------|---------|
| `benchmark_all_tools.py` | ~1940 | Speed benchmark -- runs all tools, generates SPEED_COMPARISON.md |
| `benchmark_retrieval.py` | ~2020 | Retrieval benchmark -- embeds pages, evaluates hit rates |
| `benchmark_answer_quality.py` | ~600 | Answer quality -- generates answers, scores with LLM judge |
| `benchmark_quality.py` | ~210 | Extraction quality -- content signal, preamble, repeat rate |
| `benchmark_markcrawl.py` | ~590 | MarkCrawl self-test (no competitors) |
| `quality_scorer.py` | ~740 | Quality metrics library used by benchmark_quality.py |
| `crawlee_worker.py` | ~77 | Crawlee subprocess wrapper |
| `lint_reports.py` | ~245 | Report style guide linter |
| `preflight.py` | ~varies | Environment and dependency checks |
| `colly_crawler/main.go` | ~127 | Go crawler for colly+md tool |

---

## What to check

### 1. Known code quality issues

These issues were identified in a prior audit. Check if they still exist and
if any have been fixed.

**Critical (causes incorrect results or data loss):**

| ID | File | Issue | Check |
|----|------|-------|-------|
| CQ1 | `crawlee_worker.py` | No error handling around `crawler.run()` | `grep -n "crawler.run" benchmarks/crawlee_worker.py` |
| CQ2 | `benchmark_quality.py` | `_fix_colly_jsonl()` rewrites file in place, no backup | `grep -n "fix_colly" benchmarks/benchmark_quality.py` |
| CQ3 | `benchmark_all_tools.py` | Silent stderr discard in tool runners | `grep -n "stderr" benchmarks/benchmark_all_tools.py` |
| CQ4 | `benchmark_retrieval.py` | Non-atomic checkpoint writes | `grep -n "json.dump" benchmarks/benchmark_retrieval.py` |

**High (reliability/maintainability):**

| ID | File | Issue | Check |
|----|------|-------|-------|
| CQ5 | All scripts | `print()` instead of `logging` | `grep -cn "print(" benchmarks/benchmark_*.py` |
| CQ6 | All scripts | Hardcoded model names, timeouts | See hardcoded values table below |
| CQ7 | `benchmark_retrieval.py` | No retry/backoff for OpenAI API calls | `grep -n "openai\|client\." benchmarks/benchmark_retrieval.py` |
| CQ8 | `benchmark_all_tools.py` | Generic `except Exception` hides root cause | `grep -n "except Exception" benchmarks/benchmark_all_tools.py` |

### 2. Hardcoded values inventory

Verify these are still hardcoded and flag any that have been externalized:

| Value | File | Current |
|-------|------|---------|
| Embedding model | `benchmark_retrieval.py` | `text-embedding-3-small` |
| Answer/judge model | `benchmark_answer_quality.py` | `gpt-4o-mini` |
| Reranker model | `benchmark_retrieval.py` | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Chunk size | `benchmark_retrieval.py` | 400 words, 50 overlap |
| TOP_K retrieval | `benchmark_retrieval.py` | 50 |
| TOP_K for answers | `benchmark_answer_quality.py` | 10 |
| Subprocess timeout | `benchmark_all_tools.py` | 300s |
| Colly parallelism | `colly_crawler/main.go` | 5 |
| Colly request timeout | `colly_crawler/main.go` | 30s |
| URL filename max | `crawlee_worker.py` | 80 chars |
| Max runs kept | `benchmark_all_tools.py` | 10 |
| Junk phrases | `quality_scorer.py` | 54 phrases |

```bash
# Quick scan for hardcoded values
grep -n "gpt-4o\|text-embedding\|ms-marco" benchmarks/*.py
grep -n "timeout.*=.*300\|max_pages.*=\|parallelism.*=" benchmarks/*.py benchmarks/colly_crawler/main.go
```

### 3. Error handling patterns

```bash
# Bare excepts (worst)
grep -rn "except:" benchmarks/*.py
# Generic exception catches
grep -rn "except Exception" benchmarks/*.py
# Check if stderr is captured from subprocesses
grep -n "stderr" benchmarks/benchmark_all_tools.py
```

### 4. Data integrity

- [ ] All JSONL reads handle corrupt trailing lines
- [ ] Checkpoint writes are atomic (write-to-temp + rename)
- [ ] No in-place file rewrites without backup

```bash
# Check JSONL reading patterns
grep -n "json.loads\|jsonl" benchmarks/benchmark_*.py
# Check checkpoint save patterns
grep -n "json.dump\|checkpoint" benchmarks/benchmark_*.py
```

### 5. Test queries

The 92 test queries in `benchmark_retrieval.py` are shared with
`benchmark_answer_quality.py`. Check:

- [ ] Are queries well-distributed across sites?
- [ ] Do any queries assume specific page content that may change?
- [ ] Are there enough queries per site for statistical significance?

```bash
# Count queries per site
grep -c "site.*:" benchmarks/benchmark_retrieval.py | head -20
```

### 6. Tool runner correctness

For each tool runner in `benchmark_all_tools.py`, verify:

- [ ] Correct URL list is passed (from `.url_cache.json`)
- [ ] Output is written to the expected directory structure
- [ ] Timeout is enforced
- [ ] Page count matches actual JSONL line count
- [ ] Memory measurement is active

### 7. Colly Go code

```bash
# Check for error handling
grep -n "err !=" benchmarks/colly_crawler/main.go
# Check for async + timeout (fixed in recent session)
grep -n "Async\|Timeout\|Limit" benchmarks/colly_crawler/main.go
```

- [ ] Async mode enabled with timeouts
- [ ] Error callback logs failures to stderr
- [ ] URL deduplication (AllowURLRevisit = false)
- [ ] Binary is compiled and up to date

```bash
# Check if binary matches source
ls -la benchmarks/colly_benchmark
ls -la benchmarks/colly_crawler/main.go
# Recompile if source is newer than binary
```

---

## What "good" looks like

- No bare `except:` blocks
- All subprocess runs capture and log stderr
- Checkpoint writes use atomic write pattern
- JSONL reads handle corrupt lines gracefully
- All hardcoded values documented (ideally in config)
- `ruff check benchmarks/*.py` passes
- Colly binary matches source (recompile if not)
