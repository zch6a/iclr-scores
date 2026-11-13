# Changelog

## 0.1.0 — unreleased

First release.

- ICLR 2017–2025 from the ICLR dataset (MIT, pinned by commit, size and SHA-256): for each year, the acceptance rate
  by mean score, the mean where half the papers were accepted, mean scores by outcome, agreement between reviewers,
  withdrawals by score, topics with 95% intervals.
- `iclr-scores odds`: the share accepted among a year's papers with a mean score like yours, with an interval, and a
  logistic model's rate; `iclr-scores years`; `iclr-scores build` writes the site.
- A static site with the charts (their numbers also in tables) and the calculator; counts and rates only. What is
  not read as a score is said; fewer than three scores, or a score off the year's scale, get a note.
