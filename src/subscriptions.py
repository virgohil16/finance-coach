"""Find recurring monthly charges - the subscriptions people forget about."""
from datetime import timedelta

import pandas as pd

from src.data_loader import load_transactions

COLUMNS = ["Merchant", "Monthly cost", "Yearly cost", "Last charged", "Next charge"]


def find_subscriptions(df: pd.DataFrame, min_charges: int = 3,
                       max_price_spread: float = 0.20) -> pd.DataFrame:
    """Return merchants that charge about the same amount about once a month."""
    spend = df[df["Amount"] < 0]
    rows = []

    for merchant, g in spend.groupby("Description"):
        if len(g) < min_charges:
            continue
        g = g.sort_values("Date")
        amounts = -g["Amount"]

        # price should barely change (groceries jump around, subs don't)
        if (amounts.max() - amounts.min()) / amounts.mean() > max_price_spread:
            continue

        # median gap, so one late charge doesn't break detection
        gap = g["Date"].diff().dt.days.median()
        if not 25 <= gap <= 35:
            continue

        latest = amounts.iloc[-1]  # use the newest price in case it went up
        last = g["Date"].iloc[-1]
        rows.append({
            "Merchant": merchant,
            "Monthly cost": latest,
            "Yearly cost": latest * 12,
            "Last charged": last.date(),
            "Next charge": (last + timedelta(days=round(gap))).date(),
        })

    return pd.DataFrame(rows, columns=COLUMNS).sort_values("Monthly cost", ascending=False)


if __name__ == "__main__":
    subs = find_subscriptions(load_transactions())
    print(f"\nFound {len(subs)} subscriptions\n")
    print(subs.to_string(index=False))
    print(f"\nTotal: ${subs['Monthly cost'].sum():.2f}/month, "
          f"${subs['Yearly cost'].sum():.2f}/year")