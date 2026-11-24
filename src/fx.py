"""AUD -> INR exchange rate trend. Info only, not advice on when to transfer.

Data: Frankfurter v2 API (free, no key). Fetching is kept separate from the
maths so the maths can be tested without internet.
"""
from datetime import date, timedelta

import httpx
import pandas as pd

API_URL = "https://api.frankfurter.dev/v2/rates"


def fetch_rates(days: int = 90, base: str = "AUD", quote: str = "INR") -> list[dict]:
    """Get daily rates from `days` ago up to today. Only function that hits the internet."""
    start = date.today() - timedelta(days=days)
    r = httpx.get(API_URL, params={"from": start.isoformat(), "base": base,
                                   "quotes": quote}, timeout=10)
    r.raise_for_status()
    return r.json()


def to_frame(rows: list[dict]) -> pd.DataFrame:
    """API rows -> DataFrame with date + rate, oldest first."""
    df = pd.DataFrame(rows, columns=["date", "rate"])
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def rate_stats(rates: pd.DataFrame) -> dict:
    """Latest rate plus high / low / average for the period."""
    latest = rates["rate"].iloc[-1]
    average = rates["rate"].mean()
    return {
        "latest": latest,
        "latest_date": rates["date"].iloc[-1].date(),
        "high": rates["rate"].max(),
        "low": rates["rate"].min(),
        "average": average,
        "vs_average_pct": (latest - average) / average * 100,
    }


if __name__ == "__main__":
    s = rate_stats(to_frame(fetch_rates()))
    print(f"\nAUD -> INR on {s['latest_date']}: {s['latest']:.3f}")
    print(f"90-day average {s['average']:.3f} | high {s['high']:.3f} | low {s['low']:.3f}")
    print(f"Today vs average: {s['vs_average_pct']:+.1f}%")