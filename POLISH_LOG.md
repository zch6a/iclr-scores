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

### 2026-11-14 — polishing round 2

**An independent review** (no crash and no injection path found; 10 findings, 8 fixed, each with a test where one can
be written):
- **The odds' window edge**: `by_mean` kept means to 2 decimals while the scores' mean was exact, so of two means
  exactly 0.5 away (29/6 and 35/6 from 16/3) one was in the window and one out, and the window widened for nothing.
  Means are kept to 6 decimals and compared with a tolerance of 1e-5, in Python and in `odds.js` alike.
- **The model when the data cannot carry one**: a year whose papers share one mean got a model of `[0,0,0,0]`, shown as
  “50%” for any scores; tied features (every paper with one score: spread 0, lowest = mean) gave meaningless
  coefficients. The half-way point and the model now need 10 papers of each outcome and three distinct means, and the
  model a design of full rank. The ridge no longer pulls the intercept (separated 3s and 8s tipped over at 5.38, now
  5.50).
- **The address**: clearing the box, or typing only what is not a score, left the old scores in the address (a reload
  brought them back); an address edited in the open tab did nothing. Now the address always names what the box shows,
  and a changed hash sets the year and the scores. Checked in the browser.
- **The command** said nothing when no paper was near the mean; now it says so. A reply cut short
  (`http.client.IncompleteRead`) escaped as a traceback from the download and from reading the published statistics;
  now an error message. The download's size cap was the default dataset's, not the one given. A temporary file that
  cannot be deleted (locked on Windows) no longer hides the real error.
- **The half-way marker** is drawn only when it falls inside the chart.
- **Topics** counted decided papers without scores, unlike every other figure (2018: 917 against 916); now the same.
- Not changed: ties at the median spread go to “agree” (the page says “at most” the median, which is so); and nothing
  else in the list affects the current data.

**The README's numbers against the build**: all 22 checked by a script against `data/iclr.json` (decided papers, the
2025 rates by mean score, the half-way points, agreement, withdrawals, the four topics, the file's size, the example
odds); all the same, and checked again on the published data after this round's rebuild.

Tests: 16 Python (doctests included) and 15 JS. ruff, ruff format, mypy clean.

Next: polishing round 3 (the site at phone speed; keyboard and screen-reader use; the README's claims read again).

### 2026-11-14 — polishing round 3

**At a phone's speed** (headless Chrome over the DevTools protocol: 390×844 at 2×, the CPU slowed 4×, 150 ms and
1.6 Mb/s): the page with its charts and the calculator's answer 1.2 s after navigation, 47 KB in all; a year's
charts redrawn in 49 ms (median; 61 ms at most); four keystrokes in the calculator 12 ms together. Nothing to do.

**Keyboard and screen reader.** The page was mostly sound (named regions, charts as images with names, every
chart's numbers in a table, a labelled input, the year buttons' pressed state, 19 tab stops in reading order). Fixed:
- the numbers tables' first column was headed with the chart's caption: now “Mean score” or “Year”, with
  `scope` on headers and the caption as a `<caption>` (for screen readers only);
- the five “The numbers” toggles sounded the same: each now carries its chart's name for a screen reader;
- faint bars and greyed topic rows meant “fewer than 30 papers” without saying so: a note says it where they appear;
- contrast of the bars against the background (WCAG 1.4.11 asks 3:1 of graphics): grey 1.87 → 3.18, orange
  2.93 → 3.95, dark mode's grey 2.65 → 4.27 (measured in the page);
- at phone width a rule meant for the topics table hid the third column of every table, so the chart tables lost
  “withdrawn” and “reviewers disagree”: it applies to the topics table only.

**The README read again, its commands run as written** (from GitHub, in an empty folder with its own uv cache):
`odds`, `years`, and `build` with the build extra (42 s: the pinned 49 MB file downloaded, checked, read and
deleted; the page and its data written). The commands named `@v0`, which exists only once v0.1.0 is released, so they
name the main branch until then (README in both languages, the skill). Claims tightened: the dataset is ICLR's
submissions but the few with a placeholder abstract, not every one; “disagreed” is defined (a spread above the year's
median), as on the page; the page's description says the address keeps the year and the scores.

Tests: 16 Python (doctests included) and 15 JS. ruff, ruff format, mypy clean.

Next: polishing round 4 (engineering: a clean install from the wheel, the workflows' permissions and pins, a
dependency audit, the CLI's edge cases).

### 2026-11-14 — polishing round 4

**A clean install** (the source archive, the wheel built from it, a new Python 3.10 environment): `--version`, the
requirements (numpy; pyarrow under the `build` extra), `odds` on a built file — all fine; and `build` without pyarrow
downloaded the whole 49 MB file before saying pyarrow was needed. Now it says so first (a test checks that nothing
is fetched). Running the tests in an environment without pyarrow, as CI does, then caught a test of the download's
errors that would have failed on CI (it now stubs the pyarrow check).

**The real Parquet reader was never tested** (CI has no pyarrow): a test now writes a small file of the dataset's shape
with pyarrow, pins it, and reads it from a path and through the download-to-a-temporary-file path (skipped without
pyarrow); CI's packaging job runs the tests with the build extra.

**Workflows and dependencies**: actions pinned to commits, read-only tokens, the Pages and release jobs that can write
run nothing of the project, `--locked` everywhere, a timeout on every job; `pip-audit` on the 20 locked packages
(the build extra and the dev tools included): no known vulnerabilities.

**The command's edges**, probed one by one: statistics not shaped as this version writes them (a year without its
counts, `by_mean` of the wrong type, a model of the wrong length) gave a `KeyError` or `TypeError` traceback from `years`
and `odds`; now every year is checked on reading and the message says to build again. `--stats` naming a site folder
said “Permission denied”; now it reads the folder's `data/iclr.json`. A year with no decided papers in statistics that
have none listed “the years with them are” and nothing; now it says no year has any. `--data` naming a missing file
gave a raw `Errno 2`; now a sentence. Already fine: missing arguments, a decimal or negative score, an unknown year, a
file that is not JSON, an unreachable URL.

Tests: 19 Python (doctests included; 18 and one skipped without pyarrow) and 15 JS. ruff, ruff format, mypy clean.

Next: polishing round 5 (the documents read through; a fuzz of the statistics and the odds; the CHANGELOG as release
notes), then v0.1.0.
