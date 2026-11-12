"""Rule-based transaction categoriser.

Matches merchant descriptions against regex patterns. First match wins,
so order matters (Uber Eats has to be checked before Uber rides).
Anything that doesn't match goes to "Uncategorised" - the LLM handles those later.
"""
import re
import pandas as pd

from src.data_loader import load_transactions

# (category, pattern) - checked top to bottom, first match wins
RULES = [
    ("Income", r"PAYROLL|SALARY|WAGES"),
    ("Family Support", r"TRANSFER FROM IN\b|PARENTS"),
    ("Remittance", r"TRANSFER TO INR|WISE TRANSFER"),
    ("Rent", r"LANDLORD|\bRENT\b"),
    ("Food Delivery", r"UBER \* ?EATS|MENULOG|DOORDASH"),
    ("Groceries", r"WOOLWORTHS|COLES|ALDI|\bIGA\b"),
    ("Coffee & Eating Out", r"CAFE|STARBUCKS|COFFEE"),
    ("Transport", r"MYKI|PTV|UBER(?! \* ?EATS)|DIDI"),
    ("Subscriptions", r"SPOTIFY|NETFLIX|ANTHROPIC|ADOBE|BELONG|DISNEY|YOUTUBE"),
    ("Fees", r"\bFEE\b"),
]

# compile once instead of on every row
COMPILED = [(cat, re.compile(pat, re.IGNORECASE)) for cat, pat in RULES]


def categorise(description: str) -> str:
    """Return the first category whose pattern matches, else Uncategorised."""
    for category, pattern in COMPILED:
        if pattern.search(description):
            return category
    return "Uncategorised"


def add_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Add a Category column without changing the original DataFrame."""
    df = df.copy()
    df["Category"] = df["Description"].apply(categorise)
    return df


def coverage_report(df: pd.DataFrame) -> None:
    total = len(df)
    matched = (df["Category"] != "Uncategorised").sum()
    print(f"\nRule coverage: {matched}/{total} ({matched / total:.0%})")

    print("\nSpend by category:")
    spend = (df[df["Amount"] < 0]
             .groupby("Category")["Amount"].sum()
             .sort_values())
    for cat, amt in spend.items():
        print(f"  ${-amt:>9,.2f}  {cat}")

    leftovers = df[df["Category"] == "Uncategorised"]["Description"].unique()
    if len(leftovers):
        print(f"\nUncategorised ({len(leftovers)} unique):")
        for d in leftovers:
            print(f"  - {d}")


if __name__ == "__main__":
    df = add_categories(load_transactions())
    coverage_report(df)