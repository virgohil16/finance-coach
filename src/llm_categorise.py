"""LLM fallback for transactions the regex rules couldn't categorise.

Only Uncategorised rows get sent to the model, and every answer is cached
so the same merchant never costs a second API call.
"""
import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.categorise import add_categories
from src.config import LLM_MODEL
from src.data_loader import load_transactions

load_dotenv()  # reads GROQ_API_KEY from .env

CATEGORIES = [
    "Income", "Family Support", "Remittance", "Rent", "Food Delivery",
    "Groceries", "Coffee & Eating Out", "Transport", "Subscriptions", "Fees",
    "Shopping", "Entertainment", "Health", "Education",
]
CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "llm_cache.json"

PROMPT = """You categorise Australian bank transactions.
Merchant description: "{description}"
Pick exactly one category from this list: {categories}
Restaurants, cafes and takeaway chains count as Coffee & Eating Out, not Groceries.
Reply with the category name only, nothing else."""


def load_cache(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def save_cache(cache: dict, path: Path) -> None:
    path.write_text(json.dumps(cache, indent=2))


def ask_llm(description: str, client) -> str:
    """Ask the model for one category. Anything off-list becomes Uncategorised."""
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": PROMPT.format(
            description=description, categories=", ".join(CATEGORIES))}],
        temperature=0,
    )
    answer = response.choices[0].message.content.strip()
    # models sometimes go off-script, so only accept an exact category name
    return answer if answer in CATEGORIES else "Uncategorised"


def make_client():
    from groq import Groq
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set - add it to your .env file")
    return Groq(api_key=key)


def fill_uncategorised(df: pd.DataFrame, client=None,
                       cache_path: Path | None = CACHE_PATH,
                       cache: dict | None = None) -> pd.DataFrame:
    """Fill Uncategorised rows using the cache first, then the LLM.

    If cache_path is None nothing gets written to disk - the web app uses
    this so uploaded data is never stored.
    """
    df = df.copy()
    missing = df["Category"] == "Uncategorised"
    if not missing.any():
        return df

    if cache is None:
        cache = load_cache(cache_path) if cache_path else {}

    new = [d for d in df.loc[missing, "Description"].unique() if d not in cache]
    if new:
        client = client or make_client()  # tests pass in a fake client here
        for desc in new:
            cache[desc] = ask_llm(desc, client)
        if cache_path:
            save_cache(cache, cache_path)

    df.loc[missing, "Category"] = df.loc[missing, "Description"].map(cache)
    return df


if __name__ == "__main__":
    df = add_categories(load_transactions())
    was_missing = df["Category"] == "Uncategorised"
    print(f"\nRules alone: {1 - was_missing.mean():.0%} coverage")

    df = fill_uncategorised(df)
    still_missing = (df["Category"] == "Uncategorised").mean()
    print(f"Rules + LLM: {1 - still_missing:.0%} coverage\n")

    filled = df[was_missing][["Description", "Category"]].drop_duplicates()
    for _, r in filled.iterrows():
        print(f"  {r['Description']:<30} -> {r['Category']}")