"""Flag spending that's way out of line with your usual pattern.

Uses median + MAD per category instead of mean + std dev, because one big
outlier drags the mean and std dev up and ends up hiding itself.
"""
import pandas as pd

from src.categorise import add_categories
from src.data_loader import load_transactions

THRESHOLD = 3.5   # robust z-score cut-off (common default for MAD)
MIN_EXTRA = 20.0  # also has to be at least $20 above usual to be worth flagging
MIN_TXNS = 5      # need enough history in a category to know what "usual" is
SKIP = {"Income", "Family Support", "Uncategorised"}
COLUMNS = ["Date", "Merchant", "Category", "Amount", "Usual"]


def find_anomalies(df: pd.DataFrame, threshold: float = THRESHOLD,
                   min_extra: float = MIN_EXTRA, min_txns: int = MIN_TXNS) -> pd.DataFrame:
    """Return transactions that are much bigger than usual for their category."""
    spend = df[(df["Amount"] < 0) & ~df["Category"].isin(SKIP)]
    rows = []

    for category, g in spend.groupby("Category"):
        if len(g) < min_txns:
            continue
        amounts = -g["Amount"]
        median = amounts.median()
        mad = (amounts - median).abs().median()
        if mad == 0:  # every amount the same (e.g. rent) - nothing to compare against
            continue

        # 1.4826 scales MAD so it lines up with a normal std dev
        z = (amounts - median) / (1.4826 * mad)
        flagged = g[(z > threshold) & (amounts - median >= min_extra)]

        for _, r in flagged.iterrows():
            rows.append({
                "Date": r["Date"].date(),
                "Merchant": r["Description"],
                "Category": category,
                "Amount": -r["Amount"],
                "Usual": median,
            })

    return pd.DataFrame(rows, columns=COLUMNS).sort_values("Date")


if __name__ == "__main__":
    anomalies = find_anomalies(add_categories(load_transactions()))
    print(f"\nFound {len(anomalies)} unusual transactions\n")
    print(anomalies.to_string(index=False))