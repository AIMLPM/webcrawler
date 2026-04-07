# CLAUDE.md

Project-level instructions for AI assistants working on MarkCrawl.

## Project overview

MarkCrawl is a web crawler that produces clean Markdown for LLM/RAG pipelines.
The `benchmarks/` directory contains scripts that crawl sites with 7 tools,
then measure speed, extraction quality, retrieval quality, LLM answer quality,
and cost at scale. Each benchmark script generates a corresponding `.md` report.

## Benchmark report style guide

**Style guide version: v2 (2026-04-07)**

Every benchmark report must include a style guide version comment on the line
immediately after the title. Format: `<!-- style: v2, YYYY-MM-DD -->` where the
date is when the report was last reviewed against this version of the guide.
The lint script (`benchmarks/lint_reports.py`) validates this.

Follow these rules when generating or regenerating any benchmark report.

### Enforcing this style guide

Run `python benchmarks/lint_reports.py` before committing any benchmark report
changes. The linter checks: style version tag, one-line answer, cross-references,
all-tool inclusion, bold markcrawl row, no emojis, and methodology link.

When updating the style guide itself:
1. Increment the version (e.g., `v2` to `v3`) and update the date in the
   version line above.
2. Update `STYLE_VERSION` in `benchmarks/lint_reports.py` to match.
3. Run `python benchmarks/lint_reports.py --fix-tags` to stamp all reports
   with the new version.
4. Review each report against the new rules and update as needed.

### Maintaining this style guide

When the user requests changes to any benchmark report, consider whether the
feedback reflects a **reusable rule** or a **one-off fix**:

- If the feedback is about formatting, tone, unit consistency, comparison logic,
  or report structure — it's likely a rule. Update this style guide.
- If it applies to one specific report, add it under that report's page-specific
  rules section.
- If it applies to all reports, add it under the appropriate unified section
  (Tone, Formatting, or Structure).
- Before adding a new rule, check if an existing rule already covers it — update
  the existing rule instead of creating a duplicate.
- After updating CLAUDE.md, mention the change to the user so they can verify.

### Audience and narrative

Every report should **tell a story**, not just present tables. Lead with the
question the report answers, build to the conclusion, and let the data support
the narrative — not the other way around.

Write for three readers simultaneously:

- **The junior developer** choosing a crawler for their first RAG project. They
  need a clear recommendation and simple comparisons. They'll read the summary
  table and the first paragraph. If those don't make sense on their own, the
  report fails for this reader. Avoid jargon without context — if you say "MRR"
  or "RRF", explain what it means the first time.

- **The senior/principal engineer** evaluating whether to trust the results.
  They'll skip to the methodology section and check for rigor: sample sizes,
  confidence intervals, what was controlled, what wasn't. They need enough
  detail to reproduce the benchmark independently. Never hide a caveat.

- **The engineering manager or executive** deciding whether the cost difference
  justifies switching tools. They need dollar amounts, percentage savings, and
  named scenarios they can map to their own scale. They won't read formulas,
  but they need to know the formulas exist so they trust the numbers.

If a section only serves one reader, that's fine — use clear headings so the
others can skip it. The summary must serve all three.

### Tone and credibility

- **Be honest.** If markcrawl loses on a metric, say so. Readers trust reports
  that acknowledge weaknesses. See `benchmarks/METHODOLOGY.md` for pre-written
  narratives on scenarios where markcrawl loses.
- **Don't overclaim small differences.** A gap under ~2% on a 5-point scale or
  within the confidence interval is "similar" — not a win. State the exact number
  and let readers decide.
- **Compare against the strongest competitor**, not the weakest. Use the closest
  competitor for headline claims. Cherry-picking the worst tool hurts credibility.
- **Show all tools.** Summary tables must include all 7 tools, ranked. Don't omit
  tools that perform well against markcrawl.

### Formatting

- **Anchor cost tables to their assumptions.** Every table showing dollar amounts
  must state (or link to) the pricing inputs used to calculate them — which
  embedding model, which vector DB pricing, which LLM. A reader seeing "$17"
  should never have to scroll to a different section to learn where that number
  came from. A one-line parenthetical with a link to the methodology section
  is sufficient (e.g., "using OpenAI text-embedding-3-small at $0.02/1M tokens
  — see [formula](#storage-cost-formula))").
- **Use consistent units within a sentence.** Don't mix "1.21x" and "1.3%" — pick
  one format. Prefer percentages ("21% more chunks, 1.3% lower quality").
- **Use percentages in "vs markcrawl" columns**, not multipliers.
- **Tables must be sorted** — by the primary metric, descending (best first).
  markcrawl should be first only if it ranks first.
- **Bold markcrawl's row** in summary tables for scannability, but only with `**`,
  not by putting it in a special position if it didn't earn it.
- **Round consistently.** Percentages to 1 decimal. Dollar amounts: no decimals
  above $10, two decimals below $1. Scores to 2 decimals.
- **No emojis** in reports unless the user explicitly requests them.

### Structure (all reports)

Every benchmark report should follow this structure:

1. **Title** — `# Report Name`
2. **One-line answer** — directly answer the question in 1-2 sentences. Don't
   describe what the report measures — state the finding. Example: "Yes, but
   modestly" not "This benchmark measures answer quality across 7 tools."
3. **Context for the numbers** — before the first table, explain what the metrics
   mean in plain language. A reader who has never seen "Hit@K" or "MRR" should
   understand the table without scrolling elsewhere.
4. **Summary table** — all tools, ranked by primary metric. This is the first
   data a reader should see.
5. **Narrative interpretation** — what do the results mean? Call out honest
   trade-offs (e.g., "less noise but lower recall"). This is where the exec
   and junior dev get their takeaway.
6. **Per-site breakdowns** — detailed results grouped by site.
7. **Methodology** — how to reproduce, what was measured, what was NOT measured.

### Cross-references

Reports should link to each other where findings connect:
- QUALITY → RETRIEVAL (noise vs recall trade-off)
- RETRIEVAL → ANSWER_QUALITY (retrieval doesn't differ, but answer quality does)
- ANSWER_QUALITY → COST_AT_SCALE (quality gap → dollar impact)
- SPEED → QUALITY (word count ≠ quality)
- All reports → METHODOLOGY for full test setup

### Page-specific rules

**SPEED_COMPARISON.md** (generated by `benchmark_all_tools.py`)
- Report median and std dev across iterations, not single runs.
- Include pages/second and total time.
- Note which tools use JS rendering vs plain HTTP — this is the biggest
  speed determinant and should be in the tools table.
- If a tool errored on all sites (e.g., firecrawl), note it once in the tools
  table and remove error rows from per-site tables. Don't repeat the same error
  8 times.
- If markcrawl is not the fastest, say so in the one-line answer. Acknowledge
  which tool wins, then state markcrawl's position.
- Call out page completeness — some tools miss pages. Note this in the summary.
- Link to METHODOLOGY.md for full test setup and QUALITY_COMPARISON.md for why
  higher word counts don't mean higher quality.

**QUALITY_COMPARISON.md** (generated by `benchmark_quality.py` + `quality_scorer.py`)
- Always show content signal %, preamble words, and repeat rate together — they
  tell different parts of the same story.
- Explain why preamble and repeat rate matter for RAG (nav chrome pollutes chunks).

**RETRIEVAL_COMPARISON.md** (generated by `benchmark_retrieval.py`)
- Show all 4 retrieval modes (embedding, BM25, hybrid, reranked).
- Include raw hit counts alongside percentages: "42% (39/92)" not just "42%".
- Include confidence intervals.
- Report chunks and pages per tool per site so readers can see the efficiency gap.
- The 28-row all-tools-all-modes table is overwhelming — precede it with a
  "best mode per tool" digest (7 rows) so most readers can stop there.
- Be upfront that tools perform similarly on retrieval — this is an honest finding
  that strengthens credibility. Explain WHY (same URLs, same embedding model).
- Redirect the reader: retrieval mode matters more than crawler choice.

**ANSWER_QUALITY.md** (generated by `benchmark_answer_quality.py`)
- Show all 4 scoring dimensions (correctness, relevance, completeness, usefulness)
  plus the overall average.
- Include per-query breakdowns in collapsible `<details>` sections.
- Show truncated answer text so readers can judge quality themselves.
- Explain the scoring scale (what does 5 mean? what does 3 mean?) before the
  summary table. A reader with no context should understand if 3.91 is good.
- Be honest that the gaps are small but consistent — frame as "real but not
  dramatic" rather than overstating or understating.
- Include a "what this means in practice" paragraph for the exec reader.

**COST_AT_SCALE.md** (hand-written, derived from benchmark data)
- **Separate storage costs from query costs.** They scale with different things
  (pages vs query volume). Combining them into one table hides the growth pattern.
- Show named scenarios (small app, mid-size, large-scale) so readers find their
  own situation.
- Include full methodology: formulas, pricing sources with links, and all measured
  values so others can replicate.
- When pricing changes, update the formulas and recalculate — don't just update
  the final numbers.

**METHODOLOGY.md** (hand-written)
- This is the source of truth for test setup, tool configurations, and fairness
  decisions. Other reports should link here, not duplicate the methodology.

**MARKCRAWL_RESULTS.md** (generated by `benchmark_markcrawl.py`)
- This is a self-benchmark (markcrawl only, no competitors). Don't mix in
  comparative claims. Link to SPEED_COMPARISON.md for head-to-head data.

### README sync

The README contains a benchmark summary inside the `<details>` "How it compares
to other crawlers" section. This summary must stay in sync with the detailed
reports. When any benchmark report changes in a way that affects headline numbers:

- Update the README summary to reflect the new findings.
- The README should cover all four dimensions: speed, output cleanliness, answer
  quality, and cost. One sentence each for speed and cleanliness, a table for
  quality/cost.
- State honest trade-offs (e.g., "markcrawl is third on speed but first on
  completeness"). Don't only show metrics where markcrawl wins.
- Link to each detailed report so readers can drill in.

## Git commits

- Do NOT add `Co-Authored-By` lines to commit messages.
