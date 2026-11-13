"""The submissions: ICLR's, from the ICLR dataset of González-Márquez and Kobak (github.com/berenslab/iclr-dataset, MIT
licensed; a scrape of OpenReview), one Parquet file pinned by commit, size and SHA-256. Only what the statistics
need is read (year, decision, the reviewers' scores, the topic label); titles, abstracts and authors are not read.

Reading Parquet needs pyarrow, which only a build needs (`pip install iclr-scores[build]`); the statistics and the
odds work on the built JSON without it.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

USER_AGENT = "iclr-scores (statistics of ICLR's public review scores)"


@dataclass(frozen=True)
class Dataset:
    name: str
    repo: str
    commit: str
    path: str
    size: int
    sha256: str

    @property
    def url(self) -> str:
        return f"https://raw.githubusercontent.com/{self.repo}/{self.commit}/{self.path}"

    @property
    def page(self) -> str:
        return f"https://github.com/{self.repo}"


# Version 26v1 (ICLR 2017-2026; 2026 without scores or decisions yet), checked against a download.
DATASET = Dataset("iclr26v1", "berenslab/iclr-dataset", "9f09cbbfb8ff844b7267906c8b9d9419fdad9d6c", "data/iclr26v1.parquet",
                  48_993_373, "47a04232b1c229d81109a498da32dfbe0157d35d19941561924398a9106932e2")  # fmt: skip
CITATION = (
    "Rita González-Márquez and Dmitry Kobak. Learning representations of learning representations. DMLR workshop at ICLR 2024. arXiv:2404.08403"
)

OUTCOMES = ("accept", "reject", "workshop", "withdrawn", "desk", "undecided")
DECIDED = ("accept", "reject", "workshop")  # the papers that reached a decision (a workshop invitation is not the main conference)
LEVELS = ("oral", "spotlight", "poster")


class DataError(RuntimeError):
    pass


@dataclass(frozen=True)
class Submission:
    year: int
    outcome: str  # one of OUTCOMES
    level: str  # for an accepted paper: oral, spotlight or poster; else ""
    scores: tuple[int, ...]
    label: str  # the dataset's topic label; "" when it has none


def outcome(decision: str) -> tuple[str, str]:
    """The outcome and, for an accepted paper, its level, from the decision as OpenReview words it that year.

    >>> [outcome(d) for d in ["Accept (Poster)", "Accept: notable-top-5%", "Accept (Talk)", "Reject", "Invite to Workshop Track", ""]]
    [('accept', 'poster'), ('accept', 'oral'), ('accept', 'oral'), ('reject', ''), ('workshop', ''), ('undecided', '')]
    """
    d = (decision or "").strip().lower()
    if d.startswith("accept"):
        if "oral" in d or "talk" in d or "top-5%" in d:
            return "accept", "oral"
        if "spotlight" in d or "top-25%" in d:
            return "accept", "spotlight"
        return "accept", "poster"
    if d == "reject":
        return "reject", ""
    if d.startswith("invite to workshop"):
        return "workshop", ""
    if d.startswith("withdrawn"):
        return "withdrawn", ""
    if d.startswith("desk"):
        return "desk", ""
    if not d:
        return "undecided", ""
    raise DataError(f"a decision this version does not know: {decision!r}")


def from_rows(rows: Iterable[dict[str, Any]]) -> list[Submission]:
    """Submissions from records with year, decision, scores and labels (the dataset's columns)."""
    out = []
    for r in rows:
        try:
            year = int(r["year"])
            scores = tuple(int(s) for s in (r.get("scores") or []))
        except (KeyError, TypeError, ValueError) as e:
            raise DataError(f"a record without a year or with scores that are not numbers: {e}") from e
        o, level = outcome(str(r.get("decision") or ""))
        label = str(r.get("labels") or "")
        out.append(Submission(year, o, level, scores, "" if label == "unlabeled" else label))
    return out


Fetcher = Callable[[str], bytes]


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as r:
        return bytes(r.read(DATASET.size + 1))


def check(data: bytes, dataset: Dataset = DATASET) -> None:
    if len(data) != dataset.size or hashlib.sha256(data).hexdigest() != dataset.sha256:
        raise DataError(f"{dataset.name}: not the pinned file ({len(data):,} bytes; expected {dataset.size:,} and its SHA-256)")


def read_parquet(path: Path) -> list[Submission]:
    try:
        import pyarrow.parquet as pq
    except ImportError as e:
        raise DataError("reading the dataset needs pyarrow: pip install 'iclr-scores[build]' (or uv run --extra build)") from e
    try:
        table = pq.read_table(path, columns=["year", "decision", "scores", "labels"])
    except Exception as e:  # pyarrow's errors have no common base worth naming
        raise DataError(f"{path}: not a Parquet file this version reads ({e})") from e
    return from_rows(table.to_pylist())


def load(local: Path | None = None, fetcher: Fetcher | None = None, dataset: Dataset = DATASET) -> list[Submission]:
    """The submissions: from `local` (a copy of the pinned file, checked) or downloaded to a temporary file that is
    deleted once read."""
    if local is not None:
        data = local.read_bytes()
        check(data, dataset)
        return read_parquet(local)
    try:
        data = (fetcher or _fetch)(dataset.url)
    except (urllib.error.URLError, OSError) as e:
        raise DataError(f"could not download {dataset.url} ({getattr(e, 'reason', None) or e})") from e
    check(data, dataset)
    fd, name = tempfile.mkstemp(suffix=".parquet", prefix="iclr-scores-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return read_parquet(Path(name))
    finally:
        os.unlink(name)
