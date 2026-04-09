# Contributing

Thanks for your interest in improving this project.

## How to contribute

1. Fork the repository.
2. Create a branch with a clear name.
3. Make focused changes.
4. Test your changes locally.
5. Open a pull request with a clear summary.

## Contribution guidelines

- Keep changes small and easy to review.
- Prefer improving readability over adding complexity.
- Preserve the crawler's core design goal: simple, dependable extraction for AI and indexing workflows.
- Add or update documentation when behavior changes.
- Avoid breaking the CLI without documenting it clearly.

## AI-assisted contributions

We welcome AI-assisted contributions. If you used an LLM (Claude, ChatGPT, Copilot, etc.) to generate or modify code, **include the prompt you used** in your pull request. This helps maintainers:

- understand the intent behind the change
- reproduce and refine the result
- evaluate prompt quality as part of the review

Paste the prompt in the **"AI prompt"** section of the pull request template. If you iterated through multiple prompts, include the key ones that shaped the final result. If no AI was used, just write "N/A".

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Benchmarks are maintained in a separate repository: [AIMLPM/llm-crawler-bench](https://github.com/AIMLPM/llm-crawler-bench).

## Suggested checks before opening a PR

- Run the crawler against a small public test site.
- Confirm the generated files still include page content and `pages.jsonl`.
- Verify both `markdown` and `text` output modes.
- Verify `--show-progress` works as expected.

## Areas where help is especially useful

- tests
- CI setup
- duplicate-content detection
- canonical URL handling
- browser-rendered page support
- documentation and examples

## Pull request checklist

- [ ] I tested my changes locally
- [ ] I updated relevant docs
- [ ] I kept the change focused and reviewable
- [ ] I avoided unrelated refactors
- [ ] I included the AI prompt(s) used, or marked "N/A"
