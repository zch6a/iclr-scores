# Polish log

### 2026-11-14 — development

**The source.** OpenReview's API answers 403 “Challenge verification required” to scripts (one request each to api
and api2; not worked around), so the data is the ICLR dataset of González-Márquez and Kobak (github.com/berenslab/
iclr-dataset, MIT licensed, a scrape of OpenReview): one Parquet file of 55,906 ICLR submissions 2017–2026 with year,
decision, the reviewers' scores and a topic label. Pinned by commit, size and SHA-256; a build downloads it to a
temporary file and deletes it once read; only those four columns are read. Others were not used: nhop/OpenReview is
CC BY-NC 4.0, Review-5K has its own licence, several have none. 2026 has no scores or decisions yet; confidence,
pre-rebuttal scores and review texts are not in the data, so they are not in the project (the README says so).

**The statistics** (stats.py), counts and rates over groups of papers only: per year, the outcomes (the decisions'
15 wordings mapped to accepted as oral, spotlight or poster; rejected; invited to the workshop track; withdrawn; desk
rejected; undecided, with a new wording refused rather than guessed), the score scale, the papers' review counts,
mean scores by outcome, the accepted share by exact mean (the scales make few distinct means), the mean where half are
accepted (logistic regression by IRLS, in numpy), a logistic model from the mean, the spread and the lowest score,
agreement (in each group of means, the rate below and above the year's median spread), withdrawals by mean; and the
topic labels' decided and accepted papers by year. 28,444 decided papers with scores; the statistics file is 23 KB.

**The odds** (odds.py, and the same in the page): the share accepted among the year's decided papers with a mean
within 0.25, widened until there are 30, with a Wilson interval; the model's rate; scores off the year's scale flagged.

**The site**: year buttons; the calculator (its scores and year kept in the address); five charts drawn as SVG at their
box's width (readable on a phone: first drawn at a fixed 720 width, their text shrank to 5 px at 375), each with its
numbers in a table; a half-way marker; groups of fewer than 30 papers drawn faint; topics sorted by rate with the small
ones after; a CSP allowing only the page's own files. Checked in the browser (no console errors; the calculator gives
the command's 81% for 6 6 8 5 in 2025) and over the DevTools protocol at 390 px (no horizontal scroll).

**What it found**, for the README: at ICLR 2025, means of 5.0–5.5 accepted 10%, 5.5–6.0 32%, 6.0–6.5 77%, 6.5–7.0
94%; half accepted at about 5.8 (5.8–6.1 every year but 2020, 5.4 on its 1/3/6/8 scale); disagreement helps below the
line and hurts above it (5.0–5.5: 15% against 4%; 6.0–6.5: 68% against 90%); more than half of the papers under 4.5
withdrawn; topics from 25% (CNNs) to 62% (3D scenes) over all years.

Tests: 14 (doctests included), made-up submissions, no network and no pyarrow. ruff, ruff format, mypy clean.

Next: polishing round 1 (the published site checked; a social card; the README's screenshot).

### 2026-11-14 — polishing round 1

**One calculator, tested against the other.** The page's odds moved into `site/odds.js` (pure, imported by `app.js`);
`scripts/odds_fixture.py` writes `tests/fixtures/odds.json` — a made-up year's statistics, 13 sets of scores (one score,
twelve, all 1s, all 10s, off the scale, far apart) and Python's odds for each — and `test/odds.test.js` checks the
JavaScript against it: the window, the papers, the accepted, the rate, the interval, the model and the off-scale scores
the same in all 13 (mean and spread to the 3 decimals Python prints). A Python test fails while the fixture is out of
date; CI runs the node tests; the wheel and its check include `odds.js`.

**What is typed.** The calculator dropped what it could not read without a word (`6 x 11 8` gave the odds of 6 8);
now it says “Not read as scores: x 11” and computes from the rest; more than 12 scores is refused (no ICLR paper had
more reviews); one or two scores get a note (almost every paper had three or more, so the comparison is with papers
whose full set of reviews averaged the same — a single 8 showed “100% of 123”). The command refuses scores outside
0–10 and more than 12, and prints the same note. Checked in the browser, input by input.

**Every year on the site**, 2017–2025: each chart drawn, the half-way marker (6.12, 5.92, 5.97, 5.44, 6.03, 5.86, 5.83,
5.84, 5.81), the topics (5 labelled in 2017, 41–54 later), the calculator, no console errors.

**The social card** (`docs/social-preview.png`, from `scripts/social-card.html`): ICLR 2025's accepted share by mean
score, its numbers checked against the built statistics.

Tests: 15 Python (doctests included) and 14 JS. ruff, ruff format, mypy clean.

Next: polishing round 2 (an independent review of the code; the README's numbers against the build).
