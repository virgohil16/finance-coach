"""Boundary tests for the visa hours tracker."""
from datetime import date

import pandas as pd

from src.visa_tracker import check_windows, window_status

IN_SESSION = date(2026, 5, 20)
IN_BREAK = date(2026, 7, 1)


def test_exactly_48_is_allowed_but_warns():
    assert window_status(48, IN_SESSION) == "WARNING"


def test_just_over_48_is_a_breach():
    assert window_status(48.5, IN_SESSION) == "BREACH"


def test_normal_hours_are_ok():
    assert window_status(40, IN_SESSION) == "OK"


def test_no_limit_during_course_break():
    assert window_status(70, IN_BREAK) == "BREAK"


def test_skipped_week_not_counted_in_window():
    # pay on 6 May and 20 May - nothing on 13 May, so they're not back-to-back
    weeks = pd.DataFrame({
        "Date": pd.to_datetime(["2026-05-06", "2026-05-20"]),
        "Hours": [30, 30],
    })
    assert check_windows(weeks).iloc[0]["Hours"] == 30