# Spec 01: MarkCrawl Code Review

**Scope:** The `markcrawl` Python package -- the core crawler, not the benchmarks.

**When to run:** After any change to the markcrawl package, or periodically
as a health check.

---

## What to check

### 1. Package structure and entry points

- [ ] Does the package install cleanly? (`pip install -e .`)
- [ ] Is the CLI entry point working? (`markcrawl --help`)
- [ ] Are all imports resolvable? No circular imports?

```bash
# Quick install + import check
pip install -e . 2>&1 | tail -5
python -c "import markcrawl; print(markcrawl.__version__)" 2>&1
```

### 2. Crawl correctness

- [ ] Does the crawler respect `max_pages` limits?
- [ ] Does it follow `robots.txt` by default?
- [ ] Does URL deduplication work? (no duplicate pages in output)
- [ ] Does it handle redirects correctly?
- [ ] Does it handle non-HTML content types gracefully (PDFs, images, etc.)?

```bash
# Smoke test: crawl a small site
markcrawl https://quotes.toscrape.com --max-pages 5 --output /tmp/test_crawl
wc -l /tmp/test_crawl/pages.jsonl  # should be 5
# Check for duplicate URLs
python3 -c "
import json
urls = [json.loads(l)['url'] for l in open('/tmp/test_crawl/pages.jsonl')]
dupes = len(urls) - len(set(urls))
print(f'Duplicates: {dupes}')
"
```

### 3. Markdown output quality

- [ ] Is the output valid Markdown?
- [ ] Are code blocks preserved with language tags?
- [ ] Are tables converted correctly?
- [ ] Is navigation/boilerplate stripped?
- [ ] Are images converted to `![alt](url)` format?

### 4. Error handling

- [ ] Does a network timeout produce a clear error (not a stack trace)?
- [ ] Does a DNS failure produce a clear error?
- [ ] Does the crawler continue after individual page failures?
- [ ] Are partial results saved if the crawl is interrupted?

```bash
# Check error handling patterns
grep -rn "except\b" markcrawl/ | grep -v "__pycache__"
# Look for bare excepts
grep -rn "except:" markcrawl/ | grep -v "__pycache__"
```

### 5. Performance

- [ ] Is concurrency configurable and working?
- [ ] Does `--delay` throttle work?
- [ ] Is memory usage bounded? (no unbounded lists of page content)

### 6. Security

- [ ] No shell injection via URLs (subprocess calls with user input)
- [ ] No SSRF risks (does it restrict to the seed domain?)
- [ ] Output file paths don't allow path traversal

```bash
# Check for subprocess usage with user input
grep -rn "subprocess" markcrawl/ | grep -v "__pycache__"
# Check for eval/exec
grep -rn "eval\|exec(" markcrawl/ | grep -v "__pycache__"
```

### 7. Code quality

- [ ] Type hints on public API functions
- [ ] Docstrings on public classes and functions
- [ ] No TODO/FIXME/HACK comments left in release code
- [ ] Consistent code style (run `ruff check markcrawl/`)

```bash
ruff check markcrawl/ 2>&1 | tail -20
grep -rn "TODO\|FIXME\|HACK\|XXX" markcrawl/ | grep -v "__pycache__"
```

---

## What "good" looks like

- Clean install, all imports work
- Crawl of 5 sites produces correct page counts with no duplicates
- No bare `except:` blocks
- No `subprocess` calls with unsanitized user input
- `ruff check` passes with zero errors
- Memory stays under 500 MB for a 100-page crawl
