# Feedback Registry

**Purpose:** Persistent record of user and reviewer feedback that drove changes
to the project. Before removing, reorganizing, or simplifying any content, an
LLM reviewer MUST check this registry to see if that content was added for a
documented reason.

**Rule:** If a change would remove or weaken something listed here, the reviewer
must either (a) keep it, or (b) explain in the commit message why the feedback
no longer applies and remove the registry entry.

---

## How to use this file

**Before removing content:** Search this registry for the file or feature you're
about to change. If there's an entry, read the "Why it matters" field. If you
still think the removal is correct, document your reasoning in the commit message
and update this entry.

**After incorporating feedback:** Add a new entry below. Include enough context
that a future reviewer who has never seen the original conversation understands
why this content exists.

---

## Registry entries

### FR-001: README Common Recipes section

- **Date:** 2026-04-08
- **Source:** LLM reviewer (Claude, used by external project)
- **What was added:** "Common Recipes" section in README.md with 6 copy-paste
  patterns, placed between Quickstart and benchmark comparison
- **Why it matters:** An LLM was asked to scrape a YouTube channel using
  MarkCrawl. It ran `markcrawl --base <url> --render-js --max-pages 1`, which
  discovered YouTube's global sitemap (2,524 pages) and crawled an irrelevant
  page. The LLM gave up on MarkCrawl and wrote custom regex. It later said:
  "If the README had a single-page scraping recipe, I would have used MarkCrawl
  immediately." The recipes section shows flag combinations that individual CLI
  docs don't make discoverable.
- **Protected content:**
  - The single-page recipe (`--no-sitemap --max-pages 1`)
  - The JS-rendered single-page recipe (`--no-sitemap --max-pages 1 --render-js`)
  - The "subsection without sitemap wandering" recipe with explanation
- **Do NOT:** Remove the recipes section, merge it into the CLI table, or hide
  it in a `<details>` tag. It must be visible without clicking.

### FR-002: --no-sitemap CLI description expanded

- **Date:** 2026-04-08
- **Source:** Same LLM reviewer as FR-001
- **What was added:** Expanded `--no-sitemap` description in the CLI arguments
  table from "Enable/disable sitemap discovery" to include when/why to use it
  and the sitemap hijacking problem on large sites
- **Why it matters:** The original one-line description didn't explain the
  consequence of NOT using `--no-sitemap`. The LLM knew the flag existed but
  didn't know it was the fix for its problem. The expanded description connects
  the symptom ("large sites discover thousands of unrelated pages") to the fix.
- **Do NOT:** Shorten this back to a generic description.

### FR-003: Tagline broadened to "webpage or website"

- **Date:** 2026-04-08
- **Source:** Same LLM reviewer as FR-001
- **What was added:** Changed tagline from "Turn any website..." to "Turn any
  webpage or website..."
- **Why it matters:** The word "website" caused the LLM to classify MarkCrawl
  as a site crawler and dismiss it for single-page tasks. Adding "webpage"
  signals it works for both.
- **Do NOT:** Revert to "website" only.

### FR-004: LLM_PROMPT.md surfaced in README intro

- **Date:** 2026-04-08
- **Source:** LLM reviewer feedback (round 2)
- **What was added:** One-liner after intro paragraph linking to
  `docs/LLM_PROMPT.md`, before the Quickstart section
- **Why it matters:** The LLM prompt was buried in a `<details>` tag under
  Agent Integrations. Since LLMs are a primary consumer of this tool (it's
  in the tagline), the prompt reference needs to be in the first 20 lines
  so an LLM agent scanning the README finds it immediately.
- **Do NOT:** Move this back into a `<details>` tag or remove it.

### FR-005: Infinite-scroll limitation with workaround

- **Date:** 2026-04-08
- **Source:** LLM reviewer feedback (round 2)
- **What was added:** "Infinite-scroll pages" bullet in "When NOT to use"
  section, including YouTube RSS feed as complementary approach
- **Why it matters:** Documenting limitations is good; suggesting what to do
  next is better. Users hitting the infinite-scroll limit need a path forward,
  not just a dead end.
- **Do NOT:** Remove the workaround suggestion and leave only the limitation.

### FR-006: Quickstart uses real content site

- **Date:** 2026-04-08
- **Source:** LLM reviewer feedback (round 2)
- **What was added:** Changed Quickstart from httpbin.org to
  quotes.toscrape.com
- **Why it matters:** httpbin.org is a developer test endpoint with no real
  content. quotes.toscrape.com has actual content (quotes, authors, tags) that
  demonstrates the value proposition. The sample JSONL output now shows what
  a real crawl produces.
- **Do NOT:** Switch back to a content-less test endpoint.

---

## Adding new entries

Use this template:

```markdown
### FR-NNN: Short title

- **Date:** YYYY-MM-DD
- **Source:** Who gave the feedback (user, LLM reviewer, external tester)
- **What was added:** What changed and where
- **Why it matters:** The problem that prompted the change
- **Protected content:** Specific elements that must not be removed
- **Do NOT:** Specific actions that would undo this feedback
```

Increment the FR number sequentially. Use the next available number.
