"""Load and clean bank transaction data for finance-coach.

First stage of the pipeline: read CSV, validate schema, parse Aus-format
dates correctly, and produce a clean DataFrame the rest of the app trusts.
"""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_CSV = DATA_DIR / "sample_transactions.csv"
REQUIRED_COLUMNS = ["Date", "Description", "Amount", "Balance"]


def load_transactions(csv_path: Path = DEFAULT_CSV) -> pd.DataFrame:
    """Load and clean a transactions CSV into a tidy DataFrame."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"No CSV at {csv_path}. Run `python src/generate_sample.py` first."
        )

    df = pd.read_csv(csv_path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    # Aus banks export DD/MM/YYYY — pandas defaults to US format silently
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
    df["Description"] = df["Description"].astype(str).str.strip()
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Balance"] = pd.to_numeric(df["Balance"], errors="coerce")

    return df.sort_values("Date").reset_index(drop=True)


def summarise(df: pd.DataFrame) -> None:
    """Quick sanity-check overview of the dataset."""
    print(f"\nLoaded {len(df)} transactions")
    print(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

    income = df[df["Amount"] > 0]["Amount"].sum()
    spend = df[df["Amount"] < 0]["Amount"].sum()
    print(f"\nTotal income:  ${income:>10,.2f}")
    print(f"Total spend:   ${spend:>10,.2f}")
    print(f"Net:           ${income + spend:>10,.2f}")

    print(f"\nTop 5 merchants by spend:")
    top = (df[df["Amount"] < 0]
           .groupby("Description")["Amount"].sum()
           .sort_values().head(5))
    for desc, amt in top.items():
        print(f"  ${-amt:>8,.2f}  {desc}")


if __name__ == "__main__":
    df = load_transactions()
    summarise(df)