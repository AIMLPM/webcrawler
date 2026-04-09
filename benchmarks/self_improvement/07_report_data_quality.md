# Spec 07: Report Data Quality ("Does This Look Fishy?")

**Scope:** Detect suspicious patterns in benchmark reports and source data.
Includes both post-hoc checks and early-warning hooks for the benchmark code.

**When to run:** After any benchmark run, after regenerating reports, or when
a reader says "this doesn't look right."

**Personas:** [Principal Engineer](#principal-engineer-review),
[Junior Developer](#junior-developer-review),
[Product Manager](#product-manager-review)
(see [08_persona_reviews.md](08_persona_reviews.md))

---

## What to check

### 1. Page count gaps

A crawler that returns significantly fewer pages than others on the same site
is either broken, rate-limited, or hitting a real limitation. Either way, it
needs investigation.

```bash
# Compare page counts across tools for each site
echo "=== Page counts by tool and site ==="
for site_dir in benchmarks/runs/run_*/markcrawl/*/; do
  site=$(basename "$site_dir")
  echo ""
  echo "--- $site ---"
  for tool_dir in benchmarks/runs/run_*/*/"$site"/; do
    tool=$(basename $(dirname "$tool_dir"))
    count=$(wc -l < "$tool_dir/pages.jsonl" 2>/dev/null | tr -d ' ')
    echo "  $tool: ${count:-MISSING}"
  done
done
```

**Red flags:**
- [ ] Any tool has <50% of the pages that the majority have for a site
- [ ] Any tool shows 0 pages for a site where others succeed
- [ ] A tool that previously worked now shows fewer pages (regression)

**Known gaps (document, don't fix):**

| Tool | Site | Expected gap | Reason |
|------|------|-------------|--------|
| firecrawl | react-dev | 0 usable pages (43 empty-content entries) | Anti-bot detection returns empty pages |
| firecrawl | stripe-docs | ~98% of others | 7 pages OOM (V8 heap limit) |
| scrapy+md | python-docs | ~86% of others | HTTP-only, some pages need JS |
| crawlee | stripe-docs | ~55% of others | Playwright timeout on some pages |
| crawlee | react-dev | ~32% of others | Playwright partial render (70 of 221 pages) |

If a gap is NOT in this table, investigate before accepting it.

### 2. Identical figures across tools

If two different tools show the exact same numbers for a metric, something
is likely wrong -- they're using different algorithms and should produce
different results.

```bash
# Check for duplicate avg-word counts across tools within each site
python3 -c "
import re, sys

with open('benchmarks/SPEED_COMPARISON.md') as f:
    content = f.read()

# Parse tables for avg words column
for line in content.split('\n'):
    if line.startswith('|') and not line.startswith('|---') and not line.startswith('| Tool'):
        parts = [p.strip() for p in line.split('|') if p.strip()]
        if len(parts) >= 6:
            tool, pages, time, std, pps, words = parts[:6]
            if words not in ('—', 'Avg words'):
                print(f'{tool}: {words} words')
" 2>/dev/null
```

**Red flags:**
- [ ] Two or more tools have identical avg word counts for a site (likely
  copy-paste or stale cache)
- [ ] A tool shows content stats (words, KB) but 0 pages -- impossible,
  should show dashes
- [ ] Answer quality scores are identical to 2+ decimals across sites
  for the same tool (likely cached from a different run)

### 3. Outlier detection

A tool that is 10x faster or slower on one site but normal on others
suggests a measurement error, not a real difference.

```bash
# Quick outlier scan: compare per-site pages/sec to tool's overall average
python3 -c "
import re

with open('benchmarks/SPEED_COMPARISON.md') as f:
    content = f.read()

# This is a manual scan -- look for tools where one site's pages/sec
# is very different from their other sites
print('Look for tools where one site is an outlier:')
print('(e.g., tool averages 5 pps but one site shows 50 pps)')
print()

sites = content.split('### ')
for site in sites[1:]:
    name = site.split('\n')[0].split(' — ')[0].strip()
    print(f'--- {name} ---')
    for line in site.split('\n'):
        if line.startswith('|') and not line.startswith('|---') and not line.startswith('| Tool'):
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 5 and parts[4] not in ('—', 'Pages/sec'):
                print(f'  {parts[0]}: {parts[4]} pps')
" 2>/dev/null
```

**Red flags:**
- [ ] A tool is >5x faster on one site than its average across sites
- [ ] A tool shows lower std dev than expected (suggests only 1 iteration ran)
- [ ] Std dev is exactly 0.0 (likely single run, not 3 iterations)

### 4. Report-to-data consistency

Do the numbers in the reports actually match the source data?

```bash
# Verify SPEED_COMPARISON page counts match JSONL line counts
echo "=== Checking SPEED_COMPARISON pages vs actual data ==="
# (manual: compare the page column in the report to wc -l of pages.jsonl)

# Verify RETRIEVAL_COMPARISON chunk counts
echo "=== Checking chunk counts ==="
python3 -c "
import json, glob
for f in sorted(glob.glob('benchmarks/retrieval_checkpoints/*.json')):
    data = json.load(open(f))
    chunks = data.get('total_chunks', data.get('chunks', '?'))
    pages = data.get('total_pages', data.get('pages', '?'))
    name = f.split('/')[-1].replace('.json', '')
    print(f'{name}: {pages} pages, {chunks} chunks')
" 2>/dev/null | head -30
```

### 5. Stale data indicators

```bash
# Check if any reports were generated before the latest run data
echo "=== Report generation timestamps ==="
grep -n "Generated:" benchmarks/*.md 2>/dev/null

echo ""
echo "=== Latest run directory ==="
ls -dt benchmarks/runs/run_*/ 2>/dev/null | head -1

echo ""
echo "=== Checkpoint ages vs source data ==="
latest_run=$(ls -dt benchmarks/runs/run_*/ 2>/dev/null | head -1)
if [ -n "$latest_run" ]; then
  echo "Run data: $(stat -f '%Sm' "$latest_run" 2>/dev/null || stat -c '%y' "$latest_run" 2>/dev/null)"
fi
ls -lt benchmarks/retrieval_checkpoints/ 2>/dev/null | head -5
```

**Red flags:**
- [ ] Report "Generated" date is before the latest run directory date
- [ ] Checkpoints are older than their source pages.jsonl files
- [ ] Two reports show different generation timestamps but reference the same run

---

## Early detection (hooks for benchmark code)

These are checks that should run inside the benchmark scripts to catch
problems before they become stale report data.

### E1. Post-crawl page count validation

Add to `benchmark_all_tools.py` after each tool completes a site:

```python
# After crawl completes, compare to expected page count
if pages_saved < expected_pages * 0.5:
    print(f"WARNING: {tool}/{site} got {pages_saved}/{expected_pages} pages "
          f"({pages_saved/expected_pages:.0%}). Possible failure.")
```

Where `expected_pages` comes from the URL list length. A tool getting <50%
of the URLs it was given is almost certainly broken.

### E2. Content sanity check

Add to each tool runner after crawl:

```python
# Check for empty or suspiciously short pages
empty_pages = sum(1 for p in pages if len(p.get('text', '')) < 50)
if empty_pages > len(pages) * 0.2:
    print(f"WARNING: {tool}/{site} has {empty_pages}/{len(pages)} near-empty pages")
```

### E3. Cross-tool comparison at report generation time

Add to the report generator in `benchmark_all_tools.py`:

```python
# Before writing report, check for suspicious patterns
for site in sites:
    word_counts = {tool: data[tool][site]['avg_words'] for tool in tools}
    # Check for identical word counts (different tools should differ)
    values = list(word_counts.values())
    for i, (t1, v1) in enumerate(word_counts.items()):
        for t2, v2 in list(word_counts.items())[i+1:]:
            if v1 == v2 and v1 > 0:
                print(f"WARNING: {t1} and {t2} have identical avg words "
                      f"({v1}) on {site} -- possible stale data")
```

### E4. Zero-page-with-content guard

Add to report generation:

```python
# If pages == 0, all content metrics must be None/dash
if pages == 0 and (avg_words > 0 or output_kb > 0):
    print(f"WARNING: {tool}/{site} shows 0 pages but has content stats")
    avg_words = None
    output_kb = None
```

---

## Automated check script

Consider creating `benchmarks/check_data_quality.py` that runs all the
checks in this spec and produces a pass/fail report. This could be called:
- After each benchmark run
- Before committing report changes
- As part of `lint_reports.py` or as a companion script

---

## What "good" looks like

- No unexplained page count gaps (all gaps are in the known-gaps table)
- No identical figures across different tools for the same site
- No content stats on zero-page rows
- All reports generated from the same run, after the data was collected
- No checkpoints older than their source data
- Early-warning hooks catch problems during the benchmark run, not after
