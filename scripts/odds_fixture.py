"""Writes tests/fixtures/odds.json: a made-up year's statistics, sets of scores, and the odds Python gives them. The
site's calculator (site/odds.js) is tested against it (test/odds.test.js), and a Python test checks that it is what
this script would write now. Run it when the odds or the statistics change:

    uv run python scripts/odds_fixture.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

root = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(root / "src"), str(root / "tests")]
from helpers import fake_year  # noqa: E402

from iclr_scores.odds import odds  # noqa: E402
from iclr_scores.stats import year_stats  # noqa: E402

PATH = root / "tests" / "fixtures" / "odds.json"
CASES = [[6, 6, 8, 5], [8, 8, 8, 6], [3, 5, 5], [1, 1, 1], [10, 10, 10, 10], [6], [5, 6], [3, 6, 8], [7, 6, 6],
         [0, 3, 10], [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5], [6, 8], [2, 9, 4, 6, 1]]  # fmt: skip


def fixture() -> dict[str, Any]:
    year = year_stats(fake_year(n=3000, seed=3))
    keep = {k: year[k] for k in ("by_mean", "scale", "model")}
    return {"year": keep, "cases": [{"scores": c, "odds": odds(keep, c)} for c in CASES]}


def main() -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(fixture(), indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {PATH.relative_to(root).as_posix()}: {len(CASES)} cases")


if __name__ == "__main__":
    main()
