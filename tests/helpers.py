"""Made-up submissions for the tests and the odds fixture."""

from __future__ import annotations

import random

from iclr_scores.data import Submission


def fake_year(year: int = 2025, n: int = 2000, seed: int = 0) -> list[Submission]:
    """Papers on the 1/3/5/6/8/10 scale; the chance of acceptance rises steeply around a mean of 6; a fifth of the
    papers below 5 withdrawn; two topics, one accepted more often."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        scores = tuple(rng.choice([1, 3, 5, 5, 6, 6, 6, 8, 8, 10]) for _ in range(rng.choice([3, 4, 4, 5])))
        m = sum(scores) / len(scores)
        label = "graphs" if i % 2 else "robotics"
        if m < 5 and rng.random() < 0.2:
            out.append(Submission(year, "withdrawn", "", scores, label))
            continue
        p = 1 / (1 + 2.718 ** (-4 * (m - 6))) + (0.1 if label == "graphs" else 0)
        acc = rng.random() < p
        out.append(Submission(year, "accept" if acc else "reject", "poster" if acc else "", scores, label))
    return out
