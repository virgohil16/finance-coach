"""Tests for the exchange rate maths - fake rows, no internet needed."""
import pytest

from src.fx import rate_stats, to_frame


def row(day, rate):
    return {"date": f"2026-11-{day:02d}", "base": "AUD", "quote": "INR", "rate": rate}


def test_rows_are_sorted_oldest_first():
    frame = to_frame([row(12, 64.0), row(10, 66.0), row(11, 62.0)])
    assert list(frame["rate"]) == [66.0, 62.0, 64.0]


def test_stats_are_correct():
    s = rate_stats(to_frame([row(10, 66.0), row(11, 62.0), row(12, 64.0)]))
    assert (s["latest"], s["high"], s["low"], s["average"]) == (64.0, 66.0, 62.0, 64.0)


def test_percent_vs_average():
    s = rate_stats(to_frame([row(10, 60.0), row(11, 60.0), row(12, 66.0)]))
    assert s["vs_average_pct"] == pytest.approx(6.4516, rel=1e-3)  # 66 vs avg of 62


def test_no_rows_gives_empty_frame():
    assert to_frame([]).empty