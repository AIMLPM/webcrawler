# Spec 06: Resilience & Restart

**Scope:** Checkpointing, crash recovery, and data integrity across all
benchmark scripts. Evaluates what survives an interruption and what doesn't.

**When to run:** After implementing resilience improvements, before long
benchmark runs, or after an interrupted run to assess damage.

---

## Current state: what survives interruption

| Script | Checkpoint? | Granularity | What's lost on Ctrl-C |
|--------|------------|-------------|----------------------|
| `benchmark_all_tools.py` | Yes | Per tool-site pair | Current tool-site iteration (~minutes). Temp dir data if not yet copied to `runs/`. |
| `benchmark_retrieval.py` | Yes | Per tool-site pair | Current site's embedding progress. Partially embedded batches ARE cached (embed_cache saves per-batch). |
| `benchmark_answer_quality.py` | Yes | Per tool-site pair | All answers for current site (no per-query checkpoint). |
| `benchmark_quality.py` | **No** | N/A | Everything. Must restart from scratch. |
| `benchmark_markcrawl.py` | **No** | N/A | Everything. Temp dir leaks on interrupt. |
| `crawlee_worker.py` | **No** | N/A | Partial pages.jsonl (append mode, may truncate last line). |

---

## What to check

### 1. JSONL integrity

All tool runners write `pages.jsonl` in append mode. An interrupt mid-write
can truncate the last line, producing invalid JSON that crashes downstream
scripts.

```bash
# Validate all JSONL files in the latest run
for f in benchmarks/runs/run_*/*/pages.jsonl; do
  python3 -c "
import json, sys
bad = 0
with open('$f') as fh:
  for i, line in enumerate(fh, 1):
    try: json.loads(line)
    except: bad += 1; print(f'CORRUPT $f:{i}')
if bad: sys.exit(1)
" 2>/dev/null || true
done
```

- [ ] All JSONL files parse without errors
- [ ] No file has a truncated last line
- [ ] Do any scripts validate JSONL on load? (They should.)

```bash
# Check if any script has JSONL validation
grep -n "JSONDecodeError\|json.loads.*try\|load_jsonl" benchmarks/benchmark_*.py
```

### 2. Checkpoint atomicity

Checkpoint files written non-atomically can be corrupted if the process dies
mid-write (half-written JSON).

```bash
# Check checkpoint write patterns -- look for direct json.dump to file
grep -n "json.dump" benchmarks/benchmark_*.py
# Look for atomic write pattern (write to .tmp then rename)
grep -n "os.replace\|os.rename\|\.tmp" benchmarks/benchmark_*.py
```

- [ ] Checkpoint writes use atomic pattern (write to temp, then rename)
- [ ] All checkpoint files are currently valid JSON:

```bash
for f in benchmarks/retrieval_checkpoints/*.json; do
  python3 -c "import json; json.load(open('$f'))" 2>/dev/null || echo "CORRUPT: $f"
done
for f in benchmarks/answer_quality_checkpoints/*.json; do
  python3 -c "import json; json.load(open('$f'))" 2>/dev/null || echo "CORRUPT: $f"
done
```

### 3. In-place file rewrites

Some scripts modify source data files in place. If interrupted mid-rewrite,
the file is destroyed with no backup.

```bash
# Known: _fix_colly_jsonl() in benchmark_quality.py
grep -n "open.*'w'" benchmarks/benchmark_quality.py
# General check
grep -n "open.*'w'" benchmarks/benchmark_*.py | grep -v "checkpoint\|report\|\.md"
```

- [ ] No source data file (pages.jsonl) is opened in write mode
- [ ] If a file must be rewritten, the script writes to a temp file first

### 4. Embed cache health

The embed cache (`embed_cache/`) grows unboundedly. Each embedding batch is
cached by SHA256 of the input text. Changed content creates new cache entries
without evicting old ones.

```bash
# Check cache size
du -sh benchmarks/embed_cache/ 2>/dev/null || echo "No embed_cache"
# Count entries
ls benchmarks/embed_cache/ 2>/dev/null | wc -l
```

- [ ] Cache size is under 30 GB
- [ ] Is there an eviction mechanism? (`grep -n "evict\|cleanup\|purge" benchmarks/benchmark_retrieval.py`)

### 5. Temp directory cleanup

Scripts that create temp directories should clean them up, even on exception.

```bash
# Check for tempdir usage
grep -n "tempfile\|mkdtemp\|TemporaryDirectory" benchmarks/benchmark_*.py
# Check for cleanup in finally blocks
grep -A3 "finally:" benchmarks/benchmark_*.py
```

- [ ] Temp directories are created with context managers (`with TemporaryDirectory()`)
  or cleaned up in `finally` blocks
- [ ] No orphaned temp directories on disk:

```bash
ls -d /tmp/tmp* 2>/dev/null | head -10
```

### 6. Graceful interrupt handling

Ideally, scripts catch SIGINT and finish the current unit of work before
saving state and exiting.

```bash
# Check for signal handling
grep -n "signal\|SIGINT\|KeyboardInterrupt" benchmarks/benchmark_*.py
```

- [ ] Long-running scripts handle KeyboardInterrupt or SIGINT
- [ ] On interrupt, current checkpoint is saved before exit
- [ ] User sees a message like "Saving progress..." not just a stack trace

### 7. Restart correctness

**Note:** These are code-review checks — verify by reading the source code,
not by running the benchmark scripts. Do NOT execute benchmarks during a
self-improvement review.

Verify (by reading the code) that resuming after an interrupt produces
correct results:

- [ ] `benchmark_all_tools.py --resume` logic picks up where it left off
- [ ] `benchmark_retrieval.py` checkpoint logic skips completed tool-site pairs
- [ ] `benchmark_answer_quality.py` checkpoint logic skips completed tool-site pairs
- [ ] No duplicate entries possible in output (e.g., same query answered twice)

```bash
# Check for duplicate checkpoint entries
python3 -c "
import json, glob
for f in glob.glob('benchmarks/retrieval_checkpoints/*.json'):
  data = json.load(open(f))
  # Check for duplicate queries in results
  if 'results' in data:
    queries = [r.get('query', '') for r in data['results']]
    dupes = len(queries) - len(set(queries))
    if dupes: print(f'DUPES in {f}: {dupes}')
" 2>/dev/null
```

---

## Data loss risk matrix

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Partial JSONL corruption | HIGH -- crashes downstream scripts | Medium (any interrupt during write) | Validate on load, skip corrupt trailing lines |
| Embed cache fills disk | HIGH -- silent failures | Low (requires many re-embeddings) | Add eviction or size limit |
| Answer quality loses site | MEDIUM -- wastes ~5 min + $0.03 | Medium (any interrupt during site) | Per-query checkpoints instead of per-site |
| Colly JSONL in-place rewrite | MEDIUM -- destroys source data | Low (specific to quality scoring) | Write to temp, then rename |
| Checkpoint corruption | MEDIUM -- loses completed work | Low (interrupt during JSON write) | Atomic write pattern |
| Temp dir leaks | LOW -- fills /tmp over time | Medium (any interrupt in markcrawl bench) | Context managers |

---

## Proposed improvements (prioritized)

1. **JSONL load validation** -- skip corrupt trailing lines with warning
2. **Atomic checkpoint writes** -- write to `.tmp`, then `os.replace()`
3. **Per-query answer checkpoints** -- append JSONL instead of per-site JSON
4. **Non-destructive colly fix** -- write to temp file, then rename
5. **Embed cache size limit** -- LRU eviction at configurable threshold
6. **Signal handler** -- catch SIGINT, finish current task, save, exit cleanly

---

## What "good" looks like

- All JSONL files parse without errors
- All checkpoint files are valid JSON
- Checkpoint writes are atomic
- No in-place source data rewrites
- Embed cache has a size limit
- Scripts handle interrupts gracefully (save state, clean up, exit)
- Resuming after interrupt produces correct, duplicate-free results
