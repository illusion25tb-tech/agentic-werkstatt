from pathlib import Path

from report import load, report

FIX = Path(__file__).with_name("fixtures")


def test_report_wie_gespeichert():
    out = report({"A": load(FIX / "a.jsonl"),
                  "B": load(FIX / "b.jsonl")})
    want = (FIX / "report_expected.md").read_text(
        encoding="utf-8")
    assert out == want


def test_reviews_nur_wenn_feld_ueberall_da():
    out = report({"A": load(FIX / "a.jsonl")})
    assert out.splitlines()[2].endswith("| 1 | – |")
