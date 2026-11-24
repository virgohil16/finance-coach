"""'Ask my finances' - answer questions about the user's own transactions.

pandas works out all the totals first and the LLM only reads them, because
LLMs are unreliable at adding up long lists of numbers.
"""
import pandas as pd

from src.anomalies import find_anomalies
from src.categorise import add_categories
from src.config import LLM_MODEL
from src.data_loader import load_transactions
from src.subscriptions import find_subscriptions

SYSTEM_PROMPT = """You answer questions about one person's bank transactions.
Only use the numbers in the data summary below. Use the pre-computed totals
instead of adding things up yourself. If the answer isn't in the summary,
say you can't tell from this data. All amounts are in AUD. Keep answers short.
You can point out spending patterns. Never recommend financial products
(investments, loans, credit cards, super, insurance or banks) and never tell
the user when or how to move money. You are not a financial adviser.

DATA SUMMARY
{summary}"""


def build_summary(df: pd.DataFrame) -> str:
    """Turn the transactions into small tables of pre-computed totals."""
    spend = df[df["Amount"] < 0].copy()
    if spend.empty:
        return "No spending in this data."
    spend["Spent"] = -spend["Amount"]
    spend["Month"] = spend["Date"].dt.strftime("%Y-%m")

    by_cat_month = spend.pivot_table(
        index="Category", columns="Month", values="Spent",
        aggfunc="sum", fill_value=0, margins=True, margins_name="Total",
    )
    by_merchant = (spend.groupby("Description")["Spent"]
                   .agg(total="sum", times="count")
                   .sort_values("total", ascending=False).head(25))

    income = df[df["Amount"] > 0].copy()
    if income.empty:
        money_in = "none"
    else:
        income["Month"] = income["Date"].dt.strftime("%Y-%m")
        money_in = (income.groupby(["Month", "Category"])["Amount"].sum()
                    .unstack(fill_value=0).round(2).to_string())

    subs = find_subscriptions(df)
    anomalies = find_anomalies(df)

    parts = [
        f"Date range: {df['Date'].min():%d %b %Y} to {df['Date'].max():%d %b %Y}",
        "Spending by category and month ($):\n" + by_cat_month.round(2).to_string(),
        "Top merchants ($ total, number of transactions):\n" + by_merchant.round(2).to_string(),
        "Money in by month and source ($):\n" + money_in,
        "Subscriptions:\n" + (subs.to_string(index=False) if not subs.empty else "none found"),
        "Unusual transactions:\n" + (anomalies.to_string(index=False)
                                     if not anomalies.empty else "none found"),
    ]
    return "\n\n".join(parts)


def ask(question: str, df: pd.DataFrame, client, history: list | None = None) -> str:
    """Answer one question. history = earlier chat messages, oldest first."""
    messages = [{"role": "system",
                 "content": SYSTEM_PROMPT.format(summary=build_summary(df))}]
    messages += history or []
    messages.append({"role": "user", "content": question})
    response = client.chat.completions.create(
        model=LLM_MODEL, messages=messages, temperature=0,
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    from src.llm_categorise import fill_uncategorised, make_client

    df = fill_uncategorised(add_categories(load_transactions()))
    print(build_summary(df))
    print("\nQ: How much did I spend on food delivery in May?")
    print("A:", ask("How much did I spend on food delivery in May?", df, make_client()))