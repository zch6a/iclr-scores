"""The site's data (data/iclr.json: every year's statistics and the topics) and the page next to it."""

from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path
from typing import Any

from .data import CITATION, DATASET, Submission
from .stats import topic_stats, year_stats

FORMAT = "iclr-scores/1"
PAGE = ("index.html", "app.js", "odds.js", "style.css")


def make(subs: list[Submission]) -> dict[str, Any]:
    years = sorted({s.year for s in subs})
    return {
        "format": FORMAT,
        "built": datetime.date.today().isoformat(),
        "source": {
            "name": f"ICLR dataset {DATASET.name}",
            "url": DATASET.page,
            "commit": DATASET.commit,
            "license": "MIT",
            "cite": CITATION,
            "origin": "OpenReview",
        },
        "years": {str(y): year_stats([s for s in subs if s.year == y]) for y in years},
        "topics": topic_stats(subs),
    }


def page_folder() -> Path | None:
    """The page files: in the installed package (the wheel carries them), or the repository's site/ in a checkout."""
    for folder in (Path(__file__).with_name("site"), Path(__file__).resolve().parents[2] / "site"):
        if all((folder / name).is_file() for name in PAGE):
            return folder
    return None


def write(doc: dict[str, Any], out: Path) -> bool:
    """out/data/iclr.json, and the page beside it (not when out/ is where the page comes from). False when this
    installation has no page files."""
    (out / "data").mkdir(parents=True, exist_ok=True)
    (out / "data" / "iclr.json").write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
    folder = page_folder()
    if folder is None:
        return False
    if folder.resolve() != out.resolve():
        for name in PAGE:
            shutil.copyfile(folder / name, out / name)
    return True
