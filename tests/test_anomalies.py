"""Tests for the anomaly detector."""
import pandas as pd

from src.anomalies import find_anomalies


def make_df(amounts, category="Food Delivery"):
    dates = pd.date_range("2026-04-01", periods=len(amounts), freq="3D")
    return pd.DataFrame({
        "Date": dates,
        "Description": "UBER EATS",
        "Amount": [-a for a in amounts],
        "Category": category,
    })


def test_big_spike_is_flagged():
    result = find_anomalies(make_df([25, 30, 28, 32, 27, 31, 29, 26, 90]))
    assert list(result["Amount"]) == [90]


def test_normal_spending_is_not_flagged():
    assert find_anomalies(make_df([25, 30, 28, 32, 27, 31, 29, 26])).empty


def test_small_dollar_outlier_is_ignored():
    # $18 burger is way above $5 coffees, but only $13 more - not worth flagging
    df = make_df([5, 5.5, 4.8, 5.2, 5, 18], category="Coffee & Eating Out")
    assert find_anomalies(df).empty


def test_identical_amounts_dont_crash():
    # rent is the same every week, so MAD is 0 - must not divide by zero
    assert find_anomalies(make_df([290] * 10, category="Rent")).empty


def test_needs_enough_history():
    assert find_anomalies(make_df([25, 30, 90])).empty