"""iclr-scores: what ICLR's review scores led to, year by year (2017-2025).

iclr-scores odds 6 6 8 5 --year 2025        how often papers with scores like these were accepted that year
iclr-scores years                           the years, their papers and the score scale each used
iclr-scores build --out site                the site (needs the build extra: pip install 'iclr-scores[build]')

odds and years read the published statistics (a small JSON file from the site) unless --stats names a built file.
The data: the ICLR dataset of González-Márquez and Kobak (MIT), from OpenReview. Only counts and rates over groups of
papers are computed and published; no paper, author or reviewer is named.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from . import __version__
from .build import FORMAT, make, write
from .data import USER_AGENT, DataError, load
from .odds import odds

SITE_STATS = "https://zch6a.github.io/iclr-scores/data/iclr.json"


def read_stats(where: str) -> dict[str, Any]:
    """The built statistics from a file, or from a URL (the published site by default)."""
    try:
        if where.startswith(("https://", "http://")):
            req = urllib.request.Request(where, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                doc = json.loads(r.read(50_000_000))
        else:
            doc = json.loads(Path(where).read_text(encoding="utf-8"))
    except (urllib.error.URLError, OSError) as e:
        raise DataError(f"could not read the statistics from {where} ({getattr(e, 'reason', None) or e})") from e
    except ValueError as e:
        raise DataError(f"{where}: not JSON ({e})") from e
    if not isinstance(doc, dict) or doc.get("format") != FORMAT or not isinstance(doc.get("years"), dict):
        raise DataError(f"{where}: not statistics this version reads (format {FORMAT})")
    return doc


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="iclr-scores", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"iclr-scores {__version__}")
    sub = ap.add_subparsers(dest="command", required=True)
    o = sub.add_parser("odds", help="how often papers with scores like these were accepted in a year")
    o.add_argument("scores", nargs="+", type=int, help="the reviewers' scores, e.g. 6 6 8 5")
    o.add_argument("--year", type=int, required=True)
    o.add_argument("--stats", default=SITE_STATS, help="a built data/iclr.json, or a URL (default: the published site)")
    o.add_argument("--json", action="store_true")
    y = sub.add_parser("years", help="the years, their papers and score scales")
    y.add_argument("--stats", default=SITE_STATS)
    b = sub.add_parser("build", help="the statistics and the page into a site folder")
    b.add_argument("--out", type=Path, default=Path("site"))
    b.add_argument("--data", type=Path, help="a copy of the pinned Parquet file (default: download it, then delete it)")
    args = ap.parse_args(argv)
    try:
        if args.command == "build":
            return _build(args)
        doc = read_stats(str(args.stats))
        if args.command == "years":
            for key, yr in doc["years"].items():
                print(f"{key}  {yr['count']:6,} submissions, {yr['decided']:6,} decided with scores, {yr['accepted']:5,} accepted"
                      f"  scale {', '.join(map(str, yr['scale'])) or '-'}")  # fmt: skip
            return 0
        return _odds(args, doc)
    except (DataError, ValueError, OSError) as e:
        print(f"iclr-scores: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("iclr-scores: stopped", file=sys.stderr)
        return 130


def _build(args: argparse.Namespace) -> int:
    if args.out.exists() and not args.out.is_dir():
        raise ValueError(f"--out {args.out}: a file, not a folder")
    subs = load(args.data)
    doc = make(subs)
    page = write(doc, args.out)
    decided = sum(int(y["decided"]) for y in doc["years"].values())
    print(f"{len(subs):,} submissions, {len(doc['years'])} years ({decided:,} decided with scores), {len(doc['topics'])} topics: "
          f"wrote {args.out.as_posix()}/data/iclr.json" + (" and the page" if page else ""))  # fmt: skip
    return 0


def _odds(args: argparse.Namespace, doc: dict[str, Any]) -> int:
    year = doc["years"].get(str(args.year))
    if not year or not year.get("by_mean"):
        known = [k for k, v in doc["years"].items() if v.get("by_mean")]
        raise ValueError(f"no decided papers with scores for {args.year}: the years with them are {', '.join(known)}")
    r = odds(year, args.scores)
    r["year"] = args.year
    if args.json:
        print(json.dumps(r, indent=2))
        return 0
    print(f"ICLR {args.year}, scores {' '.join(map(str, args.scores))} (mean {r['mean']:.2f}, spread {r['spread']:.2f}):")
    if r["papers"]:
        lo, hi = r["interval"]
        print(f"  {r['accepted']:,} of the {r['papers']:,} decided papers with a mean within {r['window']:.2f} were accepted: "
              f"{r['rate']:.0%} (95% interval {lo:.0%}-{hi:.0%})")  # fmt: skip
    if "model" in r:
        print(f"  the year's model (mean, spread, lowest score) gives {r['model']:.0%}")
    if year.get("half") is not None:
        print(f"  half the papers were accepted at a mean of about {year['half']:.2f}")
    if len(args.scores) < 3:
        print("  note: almost every ICLR paper had 3 reviews or more; this compares with papers whose full set of reviews averaged the same")
    if r["off_scale"]:
        print(f"  note: {', '.join(map(str, r['off_scale']))} is not on {args.year}'s scale ({', '.join(map(str, year['scale']))})")
    print("  a rate of the past, not a prediction: decisions also rest on the reviews' text, the discussion and the area chair")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
