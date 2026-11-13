# Contributing

```bash
uv sync
uv run pytest -q                 # made-up submissions: no network, no pyarrow (one test reads Parquet with --extra build)
node --test "test/*.test.js"     # the site's calculator against the Python odds
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run --extra build iclr-scores build --out site && python -m http.server --directory site
```

## Where things are

| Path | What it does |
| --- | --- |
| `src/iclr_scores/data.py` | the pinned dataset file: download, check, read (year, decision, scores, label only) |
| `src/iclr_scores/stats.py` | a year's statistics and the topics' counts; Wilson intervals; logistic regression |
| `src/iclr_scores/odds.py` | the odds for a set of scores, from a year's statistics |
| `src/iclr_scores/build.py` | data/iclr.json and the page beside it |
| `site/` | the static page: `app.js` draws the charts (SVG, with tables); `odds.js` is the calculator |
| `scripts/odds_fixture.py` | writes `tests/fixtures/odds.json`, the odds both calculators are tested against |
| `scripts/social-card.html` | the social preview, `docs/social-preview.png` |
| `scripts/fuzz.py` | random years, scores, records and broken statistics files against the invariants (`--rounds 5000`) |

`site/odds.js` does what `odds.py` does: after a change to either, run `scripts/odds_fixture.py`, then both test
suites (a Python test fails while the fixture is out of date).

## A new version of the dataset

When berenslab/iclr-dataset publishes a new file (for example one with ICLR 2026's scores and decisions), change
`DATASET` in `data.py`: the commit, the path, the size and the SHA-256 of the file you downloaded. A decision worded
in a new way is refused by `outcome()` until it is added there. Build, and look at the new year's charts before
merging.
