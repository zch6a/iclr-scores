---
name: iclr-scores
description: How often ICLR papers with given review scores were accepted (2017-2025), where the acceptance line was each year, and how disagreement, withdrawals and topics played in, with iclr-scores. Use when the user asks what their ICLR scores mean, their chances after the reviews, or about ICLR's acceptance statistics.
license: MIT
compatibility: Needs Python 3.10+ and uv. Runs iclr-scores with uvx from GitHub (git+https://github.com/zch6a/iclr-scores). odds and years fetch a 23 KB statistics file from the project's site; nothing else.
metadata:
  homepage: https://github.com/zch6a/iclr-scores
---

# ICLR's review scores and acceptance, with iclr-scores

For people, the site is the quickest: https://zch6a.github.io/iclr-scores/ (charts and a calculator).

For an answer here:

```bash
uvx --from git+https://github.com/zch6a/iclr-scores iclr-scores odds 6 6 8 5 --year 2025 --json
uvx --from git+https://github.com/zch6a/iclr-scores iclr-scores years
```

- Use the year the user's scores are from (or the latest, 2025, for a new submission) and say which; scales changed
  (`years` lists them), and a score off the year's scale is flagged in `off_scale`.
- Report the rate with its number of papers and its interval (`papers`, `accepted`, `interval`), and `model` as a
  second view. Say plainly that it is a rate of past papers with similar scores, not a prediction: the decision also
  rests on the reviews' text, the discussion and the area chair. Be careful with someone anxious about a result.
- There are no confidence values, pre-rebuttal scores or review texts in the data; do not guess them.
