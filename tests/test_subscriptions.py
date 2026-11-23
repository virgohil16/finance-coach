"""Tests for the subscription detector."""
import pandas as pd

from src.subscriptions import find_subscriptions


def make_df(rows):
    df = pd.DataFrame(rows, columns=["Date", "Description", "Amount"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def test_monthly_charge_is_found():
    df = make_df([(f"2026-0{m}-07", "NETFLIX.COM AU", -16.99) for m in (4, 5, 6)])
    assert list(find_subscriptions(df)["Merchant"]) == ["NETFLIX.COM AU"]


def test_weekly_rent_is_not_a_subscription():
    dates = pd.date_range("2026-04-06", periods=12, freq="7D")
    df = make_df([(d, "TRANSFER TO LANDLORD - RENT", -290.0) for d in dates])
    assert find_subscriptions(df).empty


def test_changing_amounts_are_not_a_subscription():
    df = make_df([("2026-04-07", "COLES", -20.0),
                  ("2026-05-07", "COLES", -65.0),
                  ("2026-06-07", "COLES", -35.0)])
    assert find_subscriptions(df).empty


def test_needs_at_least_three_charges():
    df = make_df([(f"2026-0{m}-07", "SPOTIFY", -8.99) for m in (4, 5)])
    assert find_subscriptions(df).empty


def test_small_price_rise_still_counts_and_uses_new_price():
    df = make_df([("2026-04-07", "NETFLIX", -16.99),
                  ("2026-05-07", "NETFLIX", -16.99),
                  ("2026-06-07", "NETFLIX", -18.99)])
    assert find_subscriptions(df)["Monthly cost"].iloc[0] == 18.99