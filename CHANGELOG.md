# Changelog

## 0.1.0 — 2026-11-14

First release: what ICLR's review scores led to, 2017–2025, as a static site (https://zch6a.github.io/iclr-scores/)
and a command.

**The data.** The ICLR dataset of Rita González-Márquez and Dmitry Kobak (MIT), a scrape of OpenReview, pinned by
commit, size and SHA-256; only the year, the decision, the reviewers' scores and the topic label are read. 28,444
papers that reached a decision with scores. Only counts and rates over groups of papers are published.

**For each year.**
- The accepted share by mean score, and the mean where half the papers were accepted.
- Mean scores by outcome (accepted, not accepted, withdrawn).
- Agreement: at the same mean, the rate when the reviewers' scores were close and when they were far apart.
- Withdrawals by mean score; topics with their 95% intervals.

**The odds for your scores.** The share accepted among the year's decided papers with a mean score within 0.25
(widened until there are 30), with its Wilson interval, and a logistic model's rate from the mean, the spread and the
lowest score. On the page (the year and scores kept in the address) and in the command:
`iclr-scores odds 6 6 8 5 --year 2025 [--json]`. What is not a score is said; fewer than three scores, or a score off
the year's scale, get a note. The page's calculator and the command give the same results (a shared test fixture).

**The command.** `odds`, `years` (read the published statistics, or a built file or site folder), and `build` (the
site; needs the `build` extra for pyarrow). numpy is the only other dependency.

**The site.** Every chart's numbers are also in a table; the keyboard reaches everything; the bars' contrast is at
least 3:1; it works at phone width.
