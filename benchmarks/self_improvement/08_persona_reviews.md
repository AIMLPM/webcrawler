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

## Per-persona review guides

### LLM Agent reviews

**Applies to:** Specs 04 (reports), README & Docs

**When reviewing reports (Spec 04):**
- [ ] Can I extract the key finding from the first paragraph without
  understanding the methodology?
- [ ] If a user asks me "which crawler should I use?", can I answer
  from the summary table alone?
- [ ] Are acronyms (MRR, RRF, BM25) explained on first use?
- [ ] If I cite a number from this report, is there enough context
  that the citation makes sense standalone?

**When reviewing README & Docs:**
- [ ] If a user says "scrape this one page for me," can I find the
  right command within 10 seconds of reading?
- [ ] Are common flag combinations shown as recipes?
- [ ] Does `--help` output match the README documentation?
- [ ] Does the "When NOT to use" section cover the actual failure modes
  I'd encounter?
- [ ] If I try the obvious command and it fails (e.g., sitemap hijacking),
  does the output or docs tell me the fix?

**README recipe checklist** -- do these use cases have clear examples?

| Use case | Flags | Recipe exists? |
|----------|-------|---------------|
| Scrape a single page (static) | `--no-sitemap --max-pages 1` | |
| Scrape a single page (JS-rendered) | `--no-sitemap --max-pages 1 --render-js` | |
| Crawl a docs site | `--max-pages 500 --concurrency 5` | |
| Crawl only a subsection (no sitemap wandering) | `--no-sitemap --max-pages 50` | |
| Crawl a blog (newest first) | `--no-sitemap --max-pages 100` | |
| Resume an interrupted crawl | `--resume` | |
| Get clean text (no markdown) | `--format text` | |
| Crawl behind a proxy | `--proxy http://proxy:8080` | |
| Crawl a React/Vue SPA | `--render-js` | |
| Feed output into a RAG pipeline | crawl + `markcrawl-upload` | |

**Additional recipe ideas to consider:**
- Scraping a YouTube channel page (the real case study above)
- Crawling a site with an aggressive sitemap (GitHub, YouTube)
- Extracting specific fields from crawled pages (crawl + extract pipeline)
- Comparing output from two different sites (competitive analysis)
- Crawling a site and uploading to Supabase in one pipeline

---

### Junior Developer reviews

**Applies to:** Specs 01, 02, 04, 06, 07, README

**When reviewing code (Specs 01, 02):**
- [ ] Could I debug this if it broke? Are error messages clear?
- [ ] Are there comments explaining the "why" for non-obvious code?
- [ ] If I need to add a new tool to the benchmark, is the process obvious?
- [ ] Are setup instructions complete? (install, configure, run)

**When reviewing reports (Specs 04, 07):**
- [ ] Do I understand what the numbers mean without a statistics background?
- [ ] Is the scoring scale explained? (What does 3.91/5 mean -- is that good?)
- [ ] Can I reproduce the benchmark on my machine with the given instructions?
- [ ] Are tool recommendations clear? ("If you need X, use Y")

**When reviewing resilience (Spec 06):**
- [ ] If my laptop dies mid-benchmark, what do I lose?
- [ ] Is the recovery procedure documented? (Not just "re-run" -- what about
  partial data, stale checkpoints?)
- [ ] Are error messages from interrupted runs helpful?

**When reviewing README:**
- [ ] Can I go from zero to working output in under 5 minutes?
- [ ] Does the Quickstart work on a fresh machine?
- [ ] Is every CLI flag described with enough context to know when I'd use it?
- [ ] If I get an error, does the README help me fix it?

---

### Principal Engineer reviews

**Applies to:** Specs 01, 02, 03, 05, 06, 07

**When reviewing code (Specs 01, 02, 03):**
- [ ] Would I approve this PR? What would I flag?
- [ ] Are the error handling patterns consistent and appropriate?
- [ ] Is there test coverage for the critical paths?
- [ ] Are there any security concerns (injection, SSRF, path traversal)?
- [ ] Is the code maintainable by someone unfamiliar with the project?

**When reviewing data quality (Specs 05, 07):**
- [ ] Can I verify every number in the summary table from the source data?
- [ ] Are the aggregation formulas correct? (weighted vs unweighted means)
- [ ] Is the benchmark methodology fair to all tools?
- [ ] Are known limitations documented honestly, or hidden?
- [ ] Would I trust these numbers enough to present to my leadership?

**When reviewing resilience (Spec 06):**
- [ ] What's the blast radius of a crash at each point in the pipeline?
- [ ] Are writes atomic? Can corruption happen?
- [ ] Is there a disaster recovery path? (Not just "re-run everything")
- [ ] How does the system behave under resource pressure (disk full, OOM)?

---

### Product Manager reviews

**Applies to:** Specs 04, 05, 07, README

**When reviewing reports (Specs 04, 05, 07):**
- [ ] Is the value proposition clear from the summary table?
- [ ] Can I map the cost analysis to my team's scale?
  (100 pages? 10K pages? 1M pages?)
- [ ] Are the benchmark claims credible? Would a competitor poke holes?
- [ ] Is there a clear "when to use markcrawl vs alternatives" takeaway?
- [ ] Are trade-offs framed honestly? (Overclaiming kills trust)

**When reviewing README:**
- [ ] In 30 seconds, can I understand what this tool does and why I'd use it?
- [ ] Is the comparison table (in `<details>`) fair and complete?
- [ ] Does the roadmap signal active maintenance?
- [ ] Are the cost numbers realistic and up to date?
- [ ] Would I forward this README to my engineering team as-is?

**Key questions for cost/value narrative:**
- [ ] Does COST_AT_SCALE show my scenario? (startup, mid-size, enterprise)
- [ ] Are savings expressed in terms I can put in a slide?
  ("$X/year saved" not "1.21x chunk ratio")
- [ ] Is the cheapest option clearly identified with honest caveats?

---

## How to run a persona review

1. Pick the spec you want to review
2. Check the assignment matrix for which personas apply
3. For each persona, read their review guide above
4. Go through the checklist items for that persona
5. Flag findings as:
   - **PASS** -- meets the persona's expectations
   - **ISSUE** -- needs improvement (describe what and why)
   - **SUGGESTION** -- nice-to-have improvement

Example output:
```
## Spec 04 Review -- LLM Agent Persona

PASS: Summary tables have clear rankings
ISSUE: RETRIEVAL_COMPARISON uses "MRR" without explaining it until section 3
SUGGESTION: Add a "Key metrics explained" box before the first table
PASS: Cross-references link to related reports
```

---

## Maintaining this spec

When adding a new spec to the self-improvement folder:
1. Add it to the assignment matrix
2. Decide which personas should review it (minimum 2)
3. Add persona-specific checklist items to the review guides above
4. Update MASTER.md
