"""Random inputs for the statistics, the odds and the readers, with the invariants they must keep:
- random years of submissions (any outcome, 0 to 12 scores each on a random scale, labels or none) through
  year_stats, topic_stats and make: no exception; the counts add up (histograms, by_mean, agree, withdraw); every rate
  in [0, 1]; the half-way point inside the scores' range when there is one; the document is JSON;
- random scores through odds on each year: the rate inside its interval, the window at most 2, the counts possible;
- random records through from_rows, and broken statistics files through read_stats: a DataError, never another
  exception.
Nothing is downloaded.

    uv run python scripts/fuzz.py --rounds 3000
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import tempfile
import time
import traceback
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
from iclr_scores.build import make  # noqa: E402
from iclr_scores.cli import read_stats  # noqa: E402
from iclr_scores.data import OUTCOMES, DataError, Submission, from_rows  # noqa: E402
from iclr_scores.odds import MAX_SCORES, odds  # noqa: E402

SCALES = [list(range(1, 11)), [1, 3, 6, 8], [1, 3, 5, 6, 8, 10], list(range(0, 11)), [5], [1, 10]]
ODD = [None, True, -1, 1.5, "", "x", [], {}, [1, "a"], {"a": 1}, "\\ud800", 10**30, float("nan")]


def random_year(rng: random.Random, year: int) -> list[Submission]:
    scale = rng.choice(SCALES)
    out = []
    for _ in range(rng.choice([0, 1, 2, 5, 40, 400])):
        o = rng.choice(OUTCOMES)
        scores = tuple(rng.choice(scale) for _ in range(rng.choice([0, 1, 2, 3, 4, 5, 12])))
        out.append(Submission(year, o, rng.choice(["oral", "spotlight", "poster"]) if o == "accept" else "", scores, rng.choice(["", "A", "B"])))
    return out


def check_year(y: dict, key: str) -> None:
    assert y["count"] >= y["scored"] >= y["decided"] >= y["accepted"] >= 0, key
    if "by_mean" not in y:
        return
    assert sum(c[1] for c in y["by_mean"]) == y["decided"] and sum(c[2] for c in y["by_mean"]) == y["accepted"], key
    assert all(0 <= c[2] <= c[1] for c in y["by_mean"]), key
    n = len(y["edges"]) - 1
    assert all(len(y["hist"][k]) == n for k in y["hist"]) and len(y["agree"]) == n and len(y["withdraw"]) == n, key
    assert sum(y["hist"]["accept"]) == y["accepted"] and sum(y["hist"]["accept"]) + sum(y["hist"]["reject"]) == y["decided"], key
    assert sum(a + c for a, _, c, _ in y["agree"]) == y["decided"], key
    assert all(0 <= k <= m for m, k in y["withdraw"]), key
    if y.get("half") is not None:
        assert y["scale"][0] <= y["half"] <= y["scale"][-1], (key, y["half"], y["scale"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    failures: list[str] = []
    checked = {"years": 0, "odds": 0, "rows": 0, "files": 0}
    t0 = time.perf_counter()
    tmp = Path(tempfile.mkdtemp(prefix="iclr-scores-fuzz-"))
    for r in range(args.rounds):
        try:
            subs = [s for y in range(2020, 2020 + rng.randint(1, 3)) for s in random_year(rng, y)]
            doc = make(subs)
            json.dumps(doc, allow_nan=False)
            for key, y in doc["years"].items():
                check_year(y, key)
                checked["years"] += 1
                if y.get("by_mean"):
                    for _ in range(5):
                        scores = [rng.choice(y["scale"] or [5]) for _ in range(rng.randint(1, MAX_SCORES))]
                        o = odds(y, scores)
                        checked["odds"] += 1
                        assert o["window"] <= 2 and 0 <= o["accepted"] <= o["papers"]
                        if o["papers"]:
                            lo, hi = o["interval"]
                            assert 0 <= lo <= o["rate"] <= hi <= 1
                        if "model" in o:
                            assert 0 <= o["model"] <= 1
        except Exception:
            failures.append(f"statistics #{r}: {traceback.format_exc(limit=4)}")
        # records of odd types: a DataError or submissions
        rows = [{k: rng.choice(ODD + [2024, "Reject", [5, 6]]) for k in ("year", "decision", "scores", "labels") if rng.random() < 0.9}
                for _ in range(rng.randint(1, 4))]  # fmt: skip
        try:
            from_rows(rows)
        except DataError:
            pass
        except Exception:
            failures.append(f"rows #{r} {rows!r:.120}: {traceback.format_exc(limit=3)}")
        checked["rows"] += 1
        # a broken statistics file: a DataError or a document `years` and `odds` can read
        if r % 3 == 0:
            base = make(random_year(rng, 2025)) if rng.random() < 0.5 else {"format": "iclr-scores/1", "years": {}}
            for _ in range(rng.randint(1, 4)):
                if not isinstance(base["years"], dict):
                    break  # already broken at the top
                year = next(iter(base["years"].values()), None)
                if isinstance(year, dict) and year:
                    year[rng.choice(list(year))] = rng.choice(ODD)
                elif rng.random() < 0.5:
                    base["years"] = rng.choice(ODD)
            f = tmp / "stats.json"
            f.write_text(json.dumps(base, default=str), encoding="utf-8")
            try:
                got = read_stats(str(f))
                for y in got["years"].values():
                    if y.get("by_mean"):
                        odds(y, [5, 6, 6])
            except (DataError, ValueError):
                pass
            except Exception:
                failures.append(f"file #{r}: {traceback.format_exc(limit=3)}")
            checked["files"] += 1
    print(f"{args.rounds} rounds (seed {args.seed}), {time.perf_counter() - t0:.0f} s: {checked}; {len(failures)} failures")
    seen = set()
    for f in failures:
        last = f.strip().splitlines()[-1]
        if last not in seen:
            seen.add(last)
            print(f)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
