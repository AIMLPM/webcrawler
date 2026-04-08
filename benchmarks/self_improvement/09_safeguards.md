# Spec 09: Safeguards

**Scope:** The validation process that must be followed before applying any
self-improvement changes. Prevents regressions, protects user feedback, and
ensures changes are verified.

**When to run:** Every time. This spec is not optional — it is the gate that
all other specs pass through before their changes are committed.

---

## Why this exists

Self-improvement reviews can cause regressions when:
- Content added based on user feedback gets removed because a reviewer doesn't
  know why it was there
- A "cleanup" simplifies away a feature that looks redundant but solves a real
  problem
- A code refactor breaks behavior that isn't covered by tests
- Report regeneration overwrites manual fixes with stale cached data

This spec prevents those regressions with three mechanisms:
1. **Feedback Registry** — check before removing content
2. **Invariant checks** — automated verification after changes
3. **Pre-commit validation** — the process before any commit

---

## Pre-change checklist

Before making ANY change as part of a self-improvement review:

### Step 1: Check the Feedback Registry

```bash
cat benchmarks/self_improvement/feedback_registry.md
```

- [ ] Read every entry in the registry
- [ ] If your change would modify or remove something listed in a registry
  entry, STOP. Either keep the content or document in your commit message
  why the feedback no longer applies.
- [ ] If your change is based on new user feedback, add a registry entry
  BEFORE committing

### Step 2: Run existing tests

```bash
# Core tests
python -m pytest tests/ -q

# Report linter
python benchmarks/lint_reports.py
```

- [ ] All tests pass before your change
- [ ] All tests pass after your change
- [ ] Lint passes after your change

### Step 3: Run invariant checks

```bash
python benchmarks/self_improvement/check_invariants.py
```

See [Invariant checks](#invariant-checks) below for what this validates.

- [ ] All invariants pass after your change

### Step 4: Review the diff

Before committing, review the full diff:

```bash
git diff
```

- [ ] No files were deleted that shouldn't have been
- [ ] No content was removed that exists in the feedback registry
- [ ] Changes match the scope of the review spec (don't fix unrelated things)
- [ ] No new hardcoded values introduced without documentation

---

## Invariant checks

These are conditions that must ALWAYS be true. The script
`benchmarks/self_improvement/check_invariants.py` validates them automatically.

### README invariants

| ID | Check | Why |
|----|-------|-----|
| R1 | README contains "Common Recipes" section | FR-001: LLM discoverability |
| R2 | README contains `--no-sitemap --max-pages 1` example | FR-001: single-page recipe |
| R3 | README contains `--render-js` in a recipe | FR-001: JS-rendered page recipe |
| R4 | README tagline contains "webpage" | FR-003: signals single-page support |
| R5 | README contains link to LLM_PROMPT.md before Quickstart | FR-004: LLM agent discovery |
| R6 | README contains "When NOT to use" section | Honest limitations |
| R7 | README benchmark summary exists inside `<details>` tag | CLAUDE.md: README sync rule |

### Report invariants

| ID | Check | Why |
|----|-------|-----|
| P1 | All reports have style version tag | CLAUDE.md style guide |
| P2 | All summary tables include all 8 tools | CLAUDE.md: show all tools |
| P3 | MarkCrawl row is bold in summary tables | CLAUDE.md: formatting rule |
| P4 | No emojis in reports | CLAUDE.md: formatting rule |
| P5 | Cross-references resolve to existing files | Broken links = broken trust |

### Code invariants

| ID | Check | Why |
|----|-------|-----|
| C1 | `markcrawl --help` exits 0 | CLI is not broken |
| C2 | `python -c "import markcrawl"` exits 0 | Package is importable |
| C3 | `python benchmarks/lint_reports.py` exits 0 | Linter passes |

---

## Feedback preservation process

When incorporating user feedback into the project:

1. **Make the change** — implement what the user asked for
2. **Add a registry entry** — document what, why, and what not to undo
3. **Add invariant checks** — if the change is structural (section exists,
   flag is documented), add it to `check_invariants.py`
4. **Commit together** — the change, registry entry, and invariant update
   should be in the same commit so they can't drift apart

When a future reviewer encounters a registry entry:
- If the feedback is still relevant: **keep the content, update if needed**
- If the feedback is genuinely obsolete (feature removed, tool deprecated):
  **remove the entry AND the content, document why in commit message**
- If unsure: **keep it and ask the user**

---

## What this does NOT protect against

- **Logic bugs in benchmark scripts** — invariants check that reports exist
  and have correct structure, not that the numbers are correct. Use Spec 07
  (Report Data Quality) for that.
- **Performance regressions** — no automated benchmark comparison. A change
  could make markcrawl slower without triggering any invariant.
- **External changes** — if a dependency updates or a test site goes down,
  invariants won't catch it until someone runs the benchmarks.

---

## What "good" looks like

- Every self-improvement commit passes the pre-change checklist
- The feedback registry grows over time as users provide feedback
- Invariant checks catch regressions before they're committed
- No user feedback is silently undone by a cleanup pass
- The process is lightweight enough that LLMs follow it without user prompting
