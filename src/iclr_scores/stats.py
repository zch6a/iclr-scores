"""The statistics of a year's submissions, all of them counts and rates over groups of papers (nothing about any one
paper): outcomes, the score scale, mean scores by outcome, the acceptance rate by mean score, the mean score where
half the papers were accepted, how disagreement and a low score change the rate, withdrawals by score, and topics.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Sequence

import numpy as np

from .data import DECIDED, LEVELS, OUTCOMES, Submission

BIN = 0.5  # the width of the mean-score groups in charts


def mean(s: Sequence[int]) -> float:
    return sum(s) / len(s)


def spread(s: Sequence[int]) -> float:
    """The scores' standard deviation (population), 0 for one score.

    >>> spread([6, 6, 8, 8])
    1.0
    """
    m = mean(s)
    return math.sqrt(sum((x - m) ** 2 for x in s) / len(s))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """The Wilson 95% interval of a rate k/n.

    >>> [round(x, 3) for x in wilson(77, 100)]
    [0.678, 0.842]
    >>> wilson(0, 0)
    (0.0, 1.0)
    """
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def logistic(x: np.ndarray, y: np.ndarray, ridge: float = 1e-4, iterations: int = 100) -> np.ndarray:
    """Logistic regression by iteratively reweighted least squares (a column of ones is added first); a small ridge
    keeps it finite when a feature separates the outcomes.

    >>> x = np.array([[1.0], [2.0], [3.0], [4.0], [5.0], [6.0]]); y = np.array([0, 0, 1, 0, 1, 1])
    >>> b = logistic(x, y); bool(b[1] > 0), round(float(-b[0] / b[1]), 2)
    (True, 3.5)
    """
    a = np.column_stack([np.ones(len(x)), x]).astype(np.float64)
    b = np.zeros(a.shape[1])
    for _ in range(iterations):
        p = 1 / (1 + np.exp(-np.clip(a @ b, -30, 30)))
        w = p * (1 - p) + 1e-9
        h = a.T @ (a * w[:, None]) + ridge * np.eye(a.shape[1])
        step = np.linalg.solve(h, a.T @ (y - p) - ridge * b)
        b += step
        if np.max(np.abs(step)) < 1e-10:
            break
    return b


def _bins(lo: float = 1.0, hi: float = 10.0) -> list[float]:
    return [lo + i * BIN for i in range(int((hi - lo) / BIN) + 1)]


def _bin_of(m: float, edges: list[float]) -> int:
    return min(int((m - edges[0]) // BIN), len(edges) - 2)


def year_stats(subs: list[Submission]) -> dict[str, object]:
    """One year's statistics, as the site and the odds read them."""
    out: dict[str, object] = {}
    counts = Counter(s.outcome for s in subs)
    out["count"] = len(subs)
    out["outcomes"] = {o: counts.get(o, 0) for o in OUTCOMES}
    out["levels"] = {lv: sum(1 for s in subs if s.level == lv) for lv in LEVELS}
    scored = [s for s in subs if s.scores]
    out["scored"] = len(scored)
    scale = sorted({x for s in scored for x in s.scores})
    out["scale"] = scale
    reviews = Counter(len(s.scores) for s in scored)
    out["reviews"] = {str(k): v for k, v in sorted(reviews.items())}
    decided = [s for s in scored if s.outcome in DECIDED]
    out["decided"] = len(decided)
    out["accepted"] = sum(1 for s in decided if s.outcome == "accept")
    if not decided:
        return out
    edges = _bins(min(1.0, scale[0]), max(10.0, scale[-1]))
    out["edges"] = edges
    # mean scores by outcome, per group: accepted, not accepted, withdrawn
    hist = {k: [0] * (len(edges) - 1) for k in ("accept", "reject", "withdrawn")}
    for s in scored:
        key = "accept" if s.outcome == "accept" else "reject" if s.outcome in DECIDED else "withdrawn" if s.outcome == "withdrawn" else ""
        if key:
            hist[key][_bin_of(mean(s.scores), edges)] += 1
    out["hist"] = hist
    # the rate by exact mean score (the scale makes few distinct means): [mean, decided, accepted]
    by_mean: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    for s in decided:
        cell = by_mean[round(mean(s.scores), 2)]
        cell[0] += 1
        cell[1] += s.outcome == "accept"
    out["by_mean"] = [[m, n, k] for m, (n, k) in sorted(by_mean.items())]
    # the mean score where half are accepted, and a model of the rate from the mean, the spread and the lowest score
    means = np.array([mean(s.scores) for s in decided])
    spreads = np.array([spread(s.scores) for s in decided])
    lows = np.array([min(s.scores) for s in decided], dtype=float)
    y = np.array([s.outcome == "accept" for s in decided], dtype=float)
    if 0 < y.sum() < len(y):
        b = logistic(means[:, None], y)
        out["half"] = round(float(-b[0] / b[1]), 3) if b[1] > 0 else None
        out["model"] = [round(float(v), 4) for v in logistic(np.column_stack([means, spreads, lows]), y)]
    # disagreement: in each group of mean scores, the rate when the reviewers agree more or less than the year's median
    split = float(np.median(spreads))
    out["spread_split"] = round(split, 3)
    agree = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        m = (means >= lo) & (means < hi) if i < len(edges) - 2 else (means >= lo)
        low, high = m & (spreads <= split), m & (spreads > split)
        agree.append([int(low.sum()), int(y[low].sum()), int(high.sum()), int(y[high].sum())])
    out["agree"] = agree
    # withdrawals by mean score: of the papers with scores, how many were withdrawn
    withdraw = []
    for i in range(len(edges) - 1):
        group = [s for s in scored if _bin_of(mean(s.scores), edges) == i]
        withdraw.append([len(group), sum(1 for s in group if s.outcome == "withdrawn")])
    out["withdraw"] = withdraw
    return out


def topic_stats(subs: list[Submission]) -> dict[str, dict[str, list[int]]]:
    """Each topic label's decided and accepted papers by year: {label: {year: [decided, accepted]}}."""
    out: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for s in subs:
        if s.label and s.outcome in DECIDED:
            cell = out[s.label][str(s.year)]
            cell[0] += 1
            cell[1] += s.outcome == "accept"
    return {lab: dict(sorted(years.items())) for lab, years in sorted(out.items())}
