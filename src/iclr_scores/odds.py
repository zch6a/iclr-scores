"""How often papers with scores like these were accepted, in a year: the share accepted among that year's decided
papers whose mean score is close (within 0.25, widened until there are 30 papers), with its interval, and what the
year's model of the rate (mean, spread, lowest score) gives. A rate of the past, not a prediction: the decision also
rests on the reviews' text, the discussion and the area chair.
"""

from __future__ import annotations

import math
from typing import Any

from .stats import mean, spread, wilson

ENOUGH = 30
MAX_SCORES = 12  # more reviews than any ICLR paper had


def odds(year: dict[str, Any], scores: list[int]) -> dict[str, Any]:
    """`year` is one year of the built statistics (stats.year_stats).

    >>> y = {"scale": [1, 3, 5, 6, 8], "by_mean": [[5.0, 40, 4], [5.5, 30, 9], [6.0, 50, 35], [6.5, 20, 19]], "model": [-30.0, 5.0, 0.0, 0.0]}
    >>> r = odds(y, [6, 6, 6, 6]); r["window"], r["papers"], r["accepted"], round(r["rate"], 2), round(r["model"], 2)
    (0.25, 50, 35, 0.7, 0.5)
    >>> r = odds(y, [7, 7, 7]); r["window"], r["papers"], r["accepted"]  # too few papers near 7: the window widens
    (1.0, 70, 54)
    """
    if not scores:
        raise ValueError("no scores given")
    if any(not 0 <= s <= 10 for s in scores):
        raise ValueError(f"scores are whole numbers from 0 to 10, not {' '.join(map(str, scores))}")
    if len(scores) > MAX_SCORES:
        raise ValueError(f"{len(scores)} scores: no ICLR paper had more than {MAX_SCORES} reviews")
    if not year.get("by_mean"):
        raise ValueError("that year has no decided papers with scores")
    scale = year.get("scale") or []
    off = sorted({s for s in scores if scale and s not in scale})
    m = mean(scores)
    window, n, k = 0.25, 0, 0
    while True:
        cells = [c for c in year["by_mean"] if abs(c[0] - m) <= window + 1e-5]  # means are stored to 6 decimals
        n, k = sum(c[1] for c in cells), sum(c[2] for c in cells)
        if n >= ENOUGH or window >= 2:
            break
        window += 0.25
    out: dict[str, Any] = {"mean": round(m, 3), "spread": round(spread(scores), 3), "window": window, "papers": n, "accepted": k,
                           "rate": k / n if n else None, "interval": list(wilson(k, n)) if n else None, "off_scale": off}  # fmt: skip
    b = year.get("model")
    if b:
        z = b[0] + b[1] * m + b[2] * spread(scores) + b[3] * min(scores)
        out["model"] = 1 / (1 + math.exp(-max(-30.0, min(30.0, z))))
    return out
