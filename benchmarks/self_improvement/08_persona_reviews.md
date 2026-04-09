# Spec 08: Persona-Based Reviews

**Scope:** Defines review personas and assigns them to specs. Each persona
brings a different lens -- together they catch issues no single reviewer would.

**When to run:** Use the persona assignment matrix to decide which personas
apply to the spec you're reviewing. Not all personas review every spec.

---

## Persona definitions

### LLM Agent

**Background:** An AI coding assistant (Claude, GPT, Copilot) that a user
pointed at the MarkCrawl GitHub repo and asked to use for a task. The LLM
has never seen this project before and must figure out what it does and how
to use it from the README, docs, and CLI help alone.

**What they care about:**
- Can I figure out the right flags for my task without trial and error?
- Are common use-case patterns shown as copy-paste examples?
- If I try the obvious command and it doesn't work, does the error message
  or documentation tell me what to do differently?
- Is the tool positioned clearly so I know when to reach for it vs when
  to use something else?

**What they miss:** Performance trade-offs, code quality, cost implications.
They optimize for "does it work for this task right now."

**Reference case study:**

An LLM was asked to get video titles from a YouTube channel using MarkCrawl.
It ran:
```bash
markcrawl --base "https://www.youtube.com/@MelobiesVEVO-p8q" --render-js --max-pages 1
```
This discovered YouTube's global sitemap (2,524 pages) and crawled an
irrelevant page (`/videomasthead/`). The LLM gave up on MarkCrawl and
wrote custom regex instead. It later admitted:

> "If the README had a single-page scraping recipe at the top, I would
> have reached for MarkCrawl instead of writing raw regex."

The fix would have been:
```bash
markcrawl --base "https://www.youtube.com/@MelobiesVEVO-p8q/videos" \
  --render-js --max-pages 1 --no-sitemap
```

**Lesson:** The `--no-sitemap` flag existed but was buried in a CLI table
with a one-line description. No example showed the `--no-sitemap + --max-pages 1`
combination. The LLM filed MarkCrawl as "a site crawler" and didn't consider
it for single-page scraping.

---

### Junior Developer

**Background:** A developer 0-2 years in, building their first RAG pipeline
or web scraping project. May not know what "sitemap discovery" means or why
`--render-js` matters. Learns by following examples and reading error messages.

**What they care about:**
- Is the install one command? Does it work on my machine?
- Can I copy-paste the Quickstart and get output I understand?
- When something goes wrong, do I get a helpful error or a stack trace?
- Are benchmarks explained in plain language? What does "3.91/5" mean?
- Is there a clear "which tool should I pick?" recommendation?

**What they miss:** Edge cases, architectural decisions, cost projections
at scale. They need to get something working first.

---

### Principal Engineer

**Background:** A staff/principal engineer who builds developer tools and
evaluates libraries for team adoption. Has high standards for benchmarking
methodology, code quality, and honest marketing. Will check if claims are
backed by data.

**What they care about:**
- Is the benchmark methodology sound? Can I reproduce it?
- Are the comparisons fair? Same URLs, same hardware, same settings?
- Are weaknesses acknowledged or hidden?
- Is the code production-quality? Error handling, logging, testing?
- Would I trust these numbers enough to present them to my team?

**What they miss:** First-time user experience. They skip the Quickstart
and go straight to the methodology section.

---

### Product Manager

**Background:** A PM or engineering manager evaluating whether to adopt
MarkCrawl (or switch from another tool). Reads the README, benchmark
summaries, and cost analysis. Needs to build a business case.

**What they care about:**
- Is the value proposition clear in 30 seconds?
- Can I map the cost analysis to my own scale?
- Are the benchmark claims credible? (They'll spot overclaiming.)
- Is there a clear "when to use this vs alternatives" comparison?
- Does the project look maintained? (CI badges, recent commits, roadmap)

**What they miss:** Code quality, implementation details, CLI flag behavior.
They care about outcomes, not internals.

---

## Persona assignment matrix

| Spec | LLM Agent | Junior Dev | Principal Eng | Product Manager |
|------|-----------|------------|---------------|-----------------|
| [01 MarkCrawl Code](01_markcrawl_code_review.md) | | x | x | |
| [02 Benchmark Code](02_benchmark_code_review.md) | | x | x | |
| [03 Docker Infra](03_docker_infra_review.md) | | | x | |
| [04 Report Style](04_report_style_compliance.md) | x | x | | x |
| [05 Cross-Report Consistency](05_cross_report_consistency.md) | | | x | x |
| [06 Resilience](06_resilience_restart.md) | | x | x | |
| [07 Report Data Quality](07_report_data_quality.md) | | x | x | x |
| README & Docs | x | x | | x |

---

## Zero-findings accountability

If a persona review produces **zero ISSUEs and zero SUGGESTIONs**, the reviewer
must include a brief justification explaining why nothing was found. This
prevents rubber-stamp reviews.

**Acceptable justifications:**
- "All items checked; no issues found because [specific reason]"
- "Items X and Y are now covered by automated checks (check_invariants.py,
  check_cross_report_consistency.py); remaining items verified manually"
- "Previous audit fixed the issues this persona catches; verified they
  remain fixed"

**Not acceptable:**
- "Looks good" (no evidence of checking)
- Omitting the persona section entirely

This rule was added after the April 2026 audit, where Spec 08 predicted
2-4 suggestions but produced zero fixes. The zero-result outcome was
ambiguous: either the review wasn't thorough enough, or everything was
genuinely fine. This rule removes the ambiguity.

---

## Per-spec checklists

Items marked **(AUTO)** are now covered by `check_invariants.py`,
`lint_reports.py`, or `check_cross_report_consistency.py`. The reviewer
can skip these -- they exist here for reference only. Focus review time
on items not covered by automation.

### Spec 01: MarkCrawl Code Review

**Junior Developer:**
- [ ] Run `markcrawl --help` -- is the output clear enough to build a
  command without reading the README?
- [ ] Trigger a common error (bad URL, missing flag) -- does the error
  message tell you what to fix, or just show a traceback?
- [ ] Read `setup.py` / `pyproject.toml` -- are all dependencies pinned
  to compatible ranges?

**Principal Engineer:**
- [ ] Check `ruff` output -- are there any unresolved lint issues?
- [ ] Grep for `except Exception` and `except:` -- are they justified
  or masking bugs?
- [ ] Check test coverage for the crawl loop, sitemap discovery, and
  markdown conversion (the three critical paths)
- [ ] Grep for `subprocess`, `eval`, `exec`, `os.system` -- any
  injection risks?

---

### Spec 02: Benchmark Code Review

**Junior Developer:**
- [ ] Can you add a new tool by following the pattern of existing tools?
  Identify the specific files and functions you'd need to modify.
- [ ] Run a benchmark script with `--help` -- are the flags documented?
- [ ] Read an error message from a failed crawl -- does it identify
  which tool and site failed?

**Principal Engineer:**
- [ ] Check that all `json.loads()` on JSONL files have try/except
  JSONDecodeError **(AUTO: covered by code review in Spec 02 checklist)**
- [ ] Check that all checkpoint writes use atomic temp+replace
- [ ] Check that model names are env-configurable (grep for hardcoded
  model strings like "gpt-4o")
- [ ] Check that `print()` is not used for progress output (should be
  `logging`)

---

### Spec 03: Docker Infrastructure Review

**Principal Engineer:**
- [ ] Check base images are pinned to specific digests or versions
- [ ] Check that containers run as non-root
- [ ] Identify what happens if a container crashes mid-crawl -- is data
  lost or recoverable?
- [ ] Check resource limits (memory, CPU) are set in docker-compose

---

### Spec 04: Report Style Compliance

**LLM Agent:**
- [ ] Read only the first paragraph of each report -- can you state the
  main finding without reading further? If not, the one-line answer fails.
- [ ] Find every abbreviation (MRR, RRF, BM25, NDCG, etc.) -- is each
  one defined before or at the point of first use?
- [ ] Pick a number from a summary table and try to cite it standalone
  (e.g., "markcrawl scores 3.91/5") -- does it make sense without the
  surrounding paragraph?

**Junior Developer:**
- [ ] Read ANSWER_QUALITY.md -- do you understand what 3.91/5 means
  before seeing the summary table? Is the scale explained?
- [ ] Read COST_AT_SCALE.md -- can you find your scenario (small
  project, mid-size, large)? Are the dollar amounts believable?
- [ ] Read the methodology section of any report -- could you reproduce
  the benchmark on your machine?

**Product Manager:**
- [ ] Read the summary table of each report -- is the cheapest / best /
  fastest tool immediately obvious?
- [ ] Check COST_AT_SCALE scenarios -- are they named in terms a PM
  would use ("startup", "mid-size SaaS", "enterprise")?
- [ ] Read the "what this means" paragraph -- does it acknowledge
  trade-offs, or does it only highlight where markcrawl wins?

---

### Spec 05: Cross-Report Data Consistency

**Principal Engineer:**
- [ ] **(AUTO)** `check_cross_report_consistency.py` passes
- [ ] Verify aggregation formulas: is SPEED's overall pages/sec a
  weighted total (total_pages / total_time) or a mean of per-site rates?
- [ ] Check that COST_AT_SCALE methodology section formulas produce the
  numbers in its tables (spot-check one tool at one scale)
- [ ] Check firecrawl's page count caveat is consistent across reports
  (e.g., "70 queries on 6 sites" should appear in both AQ and COST)

**Product Manager:**
- [ ] Are savings expressed as both absolute dollars and percentages?
- [ ] Does every cost claim link to the assumptions behind it?
- [ ] Could a competitor reasonably dispute any headline claim?

---

### Spec 06: Resilience & Restart

**Junior Developer:**
- [ ] Read the benchmark README or script comments -- is there a clear
  answer to "what do I lose if I Ctrl-C mid-run?"
- [ ] After a simulated interrupt, does `--resume` work? (Check that
  checkpoint loading code handles partial files.)

**Principal Engineer:**
- [ ] Grep for file writes -- are they all using temp+replace (atomic)?
- [ ] Check embed cache eviction -- is there a size limit? What happens
  when disk fills?
- [ ] Check signal handling -- does SIGINT flush partial results or
  corrupt them?

---

### Spec 07: Report Data Quality

**Junior Developer:**
- [ ] Read the known-gaps table -- does every gap have an explanation?
- [ ] Look at a per-site breakdown -- are there any 0-page or
  suspiciously round numbers?

**Principal Engineer:**
- [ ] Spot-check page counts: pick 2 tool+site combos and verify the
  report number matches `wc -l` on the source JSONL file
- [ ] Check for identical metrics between different tools on the same
  site -- this is suspicious unless explained (e.g., same markdownify)
- [ ] Verify that firecrawl's partial coverage is flagged consistently
  (page count, query count, "not directly comparable" caveat)

**Product Manager:**
- [ ] Are known limitations presented honestly, or buried in footnotes?
- [ ] If a tool beats markcrawl on a metric, is it acknowledged
  prominently (not just in a footnote)?

---

### README & Docs

**LLM Agent:**
- [ ] Read only the README. Then write the command to scrape a single
  JS-rendered page. Did you find `--no-sitemap --max-pages 1 --render-js`
  without trial and error?
- [ ] **(AUTO)** Check that `--no-sitemap` recipe exists (R2 invariant)
- [ ] Run `markcrawl --help` and compare against the README CLI table --
  are all flags documented in both places?
- [ ] Read the "When NOT to use" section -- does it cover the actual
  failure modes (sitemap hijacking, anti-bot blocking, SPAs without
  static routes)?

**LLM Agent recipe checklist** -- do these use cases have clear examples?

| Use case | Flags | Recipe exists? |
|----------|-------|---------------|
| Scrape a single page (static) | `--no-sitemap --max-pages 1` | |
| Scrape a single page (JS-rendered) | `--no-sitemap --max-pages 1 --render-js` | |
| Crawl a docs site | `--max-pages 500 --concurrency 5` | |
| Crawl only a subsection (no sitemap wandering) | `--no-sitemap --max-pages 50` | |
| Competitive analysis (multi-site extract) | crawl N sites + `markcrawl-extract` | |
| Docs → RAG chatbot pipeline | crawl + `markcrawl-upload` | |
| API docs → code generation | crawl + feed to LLM | |
| Blog archival | `--no-sitemap --max-pages 1000` | |
| Resume an interrupted crawl | `--resume` | |
| Get clean text (no markdown) | `--format text` | |
| Crawl behind a proxy | `--proxy http://proxy:8080` | |
| Crawl a React/Vue SPA | `--render-js` | |

**Junior Developer:**
- [ ] Follow the Quickstart from scratch. Does `pip install markcrawl`
  then the example command produce output you understand?
- [ ] Read the comparison table in `<details>` -- is it clear which tool
  to pick for your use case?
- [ ] Find the benchmark results -- do the numbers make sense without
  reading the detailed reports?

**Product Manager:**
- [ ] Read the first 3 lines of the README. Can you explain what this
  tool does to a colleague?
- [ ] **(AUTO)** Benchmark summary data matches source reports
  (check_cross_report_consistency.py)
- [ ] Does the README show honest trade-offs (speed ranking where
  markcrawl is third, not first)?
- [ ] Would you forward this README to your engineering team as-is? If
  not, what would you change?

---

## How to run a persona review

1. Pick the spec you want to review
2. Find the spec's section in [Per-spec checklists](#per-spec-checklists) above
3. Skip items marked **(AUTO)** -- they are covered by automated scripts
4. Go through each remaining checklist item for each persona
5. Flag findings as:
   - **PASS** -- meets the persona's expectations
   - **ISSUE** -- needs improvement (describe what and why)
   - **SUGGESTION** -- nice-to-have improvement
6. **If zero ISSUEs and zero SUGGESTIONs:** add a justification
   (see [Zero-findings accountability](#zero-findings-accountability))

Example output:
```
## Spec 04 Review

LLM Agent:
  PASS: Summary tables have clear rankings
  ISSUE: RETRIEVAL_COMPARISON uses "MRR" without explaining it until section 3
  SUGGESTION: Add a "Key metrics explained" box before the first table

Junior Developer:
  PASS: Scoring scale explained before tables
  PASS: Reproduction instructions are complete
  Zero findings justified: Previous audit (2026-04-08) fixed the scoring
  scale issue and reproduction instructions. Verified both still present.

Product Manager:
  PASS: Trade-offs are honest
  ISSUE: COST_AT_SCALE doesn't show a "10-person startup" scenario
```

---

## Maintaining this spec

When adding a new spec to the self-improvement folder:
1. Add it to the assignment matrix
2. Decide which personas should review it (minimum 2)
3. Add a new section under [Per-spec checklists](#per-spec-checklists) with
   the relevant persona checklist items grouped together
4. Update MASTER.md

When adding a new automated check:
1. Mark the corresponding manual checklist item with **(AUTO)**
2. Note which script covers it
3. Keep the item in the checklist for reference, but reviewers can skip it
