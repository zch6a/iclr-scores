"""Made-up submissions only: no download, no network, no pyarrow."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from helpers import fake_year

from iclr_scores import cli
from iclr_scores.build import FORMAT, make, write
from iclr_scores.data import DATASET, DataError, Dataset, Submission, check, from_rows, load, outcome
from iclr_scores.odds import odds
from iclr_scores.stats import topic_stats, year_stats


def test_decisions_as_openreview_words_them() -> None:
    assert outcome("Accept (spotlight)") == ("accept", "spotlight")
    assert outcome("Accept: notable-top-25%") == ("accept", "spotlight")
    assert outcome("Desk rejected") == ("desk", "")
    assert outcome("Withdrawn") == ("withdrawn", "")
    with pytest.raises(DataError):
        outcome("Conditional accept")  # a decision this version does not know is said, not guessed


def test_rows_from_the_dataset() -> None:
    subs = from_rows([{"year": 2024, "decision": "Accept (oral)", "scores": [8, 8, 6], "labels": "LLMs"},
                      {"year": 2026, "decision": "", "scores": [], "labels": "unlabeled"}])  # fmt: skip
    assert subs[0] == Submission(2024, "accept", "oral", (8, 8, 6), "LLMs")
    assert subs[1].outcome == "undecided" and subs[1].label == "" and subs[1].scores == ()
    with pytest.raises(DataError):
        from_rows([{"decision": "Reject", "scores": [1]}])


def test_the_download_is_checked_and_not_kept(tmp_path: Path) -> None:
    with pytest.raises(DataError, match="not the pinned file"):
        load(fetcher=lambda url: b"not parquet")
    with pytest.raises(DataError, match="not the pinned file"):
        check(b"x" * 10)
    small = Dataset("t", "o/r", "c", "p", 3, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")  # sha256("abc")
    check(b"abc", small)
    (tmp_path / "copy.parquet").write_bytes(b"abc")
    with pytest.raises(DataError):  # a pinned copy that is not Parquet, or no pyarrow: an error either way, not a traceback
        load(tmp_path / "copy.parquet", dataset=small)
    assert DATASET.url.startswith("https://raw.githubusercontent.com/berenslab/iclr-dataset/") and len(DATASET.commit) == 40


def test_a_years_statistics() -> None:
    y = year_stats(fake_year())
    assert y["count"] == 2000 and y["outcomes"]["withdrawn"] > 0
    assert y["scale"] == [1, 3, 5, 6, 8, 10]
    assert y["decided"] == y["outcomes"]["accept"] + y["outcomes"]["reject"]
    assert 5.6 < y["half"] < 6.2  # the made-up papers' tipping point is near 6
    edges, hist = y["edges"], y["hist"]
    assert sum(hist["accept"]) == y["accepted"] and sum(hist["withdrawn"]) == y["outcomes"]["withdrawn"]
    assert len(hist["accept"]) == len(edges) - 1 == len(y["agree"]) == len(y["withdraw"])
    assert sum(c[1] for c in y["by_mean"]) == y["decided"] and sum(c[2] for c in y["by_mean"]) == y["accepted"]
    assert y["model"][1] > 0  # a higher mean, a higher rate
    rates = [k / n for n, k in y["withdraw"] if n >= 50]
    assert rates[0] > rates[-1]  # withdrawals are of the low scores


def test_a_year_without_decisions() -> None:
    y = year_stats([Submission(2026, "undecided", "", (), "LLMs")] * 5)
    assert y["count"] == 5 and y["decided"] == 0 and "by_mean" not in y


def test_topics() -> None:
    t = topic_stats(fake_year() + fake_year(2024, 500, seed=1))
    assert set(t) == {"graphs", "robotics"} and set(t["graphs"]) == {"2024", "2025"}
    g = sum(k for _, k in t["graphs"].values()) / sum(n for n, _ in t["graphs"].values())
    r = sum(k for _, k in t["robotics"].values()) / sum(n for n, _ in t["robotics"].values())
    assert g > r


def test_odds() -> None:
    y = year_stats(fake_year(n=4000))
    high, low = odds(y, [8, 8, 8, 6]), odds(y, [3, 5, 5])
    assert high["rate"] > 0.8 > 0.2 > low["rate"]
    assert high["papers"] >= 30 and high["interval"][0] <= high["rate"] <= high["interval"][1]
    assert odds(y, [7, 6, 6])["off_scale"] == [7]
    with pytest.raises(ValueError):
        odds(y, [])
    with pytest.raises(ValueError, match="from 0 to 10"):
        odds(y, [6, 11])
    with pytest.raises(ValueError, match="more than 12"):
        odds(y, [6] * 13)


def test_the_site_and_the_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    subs = fake_year() + fake_year(2024, 800, seed=2) + [Submission(2026, "undecided", "", (), "")]
    monkeypatch.setattr(cli, "load", lambda local=None: subs)
    out = tmp_path / "site"
    assert cli.main(["build", "--out", str(out)]) == 0
    assert "2,801 submissions, 3 years" in capsys.readouterr().out
    doc = json.loads((out / "data" / "iclr.json").read_text(encoding="utf-8"))
    assert doc["format"] == FORMAT and set(doc["years"]) == {"2024", "2025", "2026"}
    assert all((out / f).is_file() for f in ("index.html", "app.js", "odds.js", "style.css"))  # a whole site
    text = (out / "data" / "iclr.json").read_text(encoding="utf-8")
    assert "robotics" in text and "title" not in text and "author" not in text  # counts only: no paper is in it
    stats = str(out / "data" / "iclr.json")
    assert cli.main(["odds", "6", "6", "8", "5", "--year", "2025", "--stats", stats]) == 0
    printed = capsys.readouterr().out
    assert "were accepted" in printed and "not a prediction" in printed
    assert cli.main(["odds", "6", "6", "8", "--year", "2025", "--stats", stats, "--json"]) == 0
    r = json.loads(capsys.readouterr().out)
    assert r["year"] == 2025 and 0 <= r["rate"] <= 1
    assert cli.main(["years", "--stats", stats]) == 0 and "2025" in capsys.readouterr().out
    # errors are said, with exit 2
    assert cli.main(["odds", "6", "--year", "2026", "--stats", stats]) == 2
    assert "the years with them are 2024, 2025" in capsys.readouterr().err
    (tmp_path / "bad.json").write_text('{"format": "other"}', encoding="utf-8")
    assert cli.main(["odds", "6", "--year", "2025", "--stats", str(tmp_path / "bad.json")]) == 2
    assert "not statistics this version reads" in capsys.readouterr().err
    assert cli.main(["odds", "6", "--year", "2025", "--stats", str(tmp_path / "missing.json")]) == 2
    (tmp_path / "file").write_text("x", encoding="utf-8")
    assert cli.main(["build", "--out", str(tmp_path / "file")]) == 2
    assert "a file, not a folder" in capsys.readouterr().err


def test_write_keeps_the_repository_page(tmp_path: Path) -> None:
    doc = make(fake_year(n=300))
    assert write(doc, tmp_path) is True
    assert json.loads((tmp_path / "data" / "iclr.json").read_text(encoding="utf-8"))["source"]["license"] == "MIT"


def test_the_calculators_fixture_is_current() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("odds_fixture", Path(__file__).parent.parent / "scripts" / "odds_fixture.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    on_disk = json.loads(mod.PATH.read_text(encoding="utf-8"))
    assert on_disk == json.loads(json.dumps(mod.fixture())), "run scripts/odds_fixture.py: the site's test fixture is out of date"
