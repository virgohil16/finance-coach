"""Visa work-hours tracker (student visa condition 8105).

Bank statements only show pay, not hours, so hours are estimated as
pay / night rate. I'm paid weekly, so any two back-to-back pay weeks
make up one 2-week window - that's what gets checked against the limit.
"""
import pandas as pd

from src.categorise import add_categories
from src.config import COURSE_BREAKS, NIGHT_RATE, VISA_HOUR_LIMIT, WARNING_BUFFER
from src.data_loader import load_transactions


def in_course_break(day) -> bool:
    """True if the date is inside a scheduled course break (no hour limit)."""
    return any(start <= day <= end for start, end in COURSE_BREAKS)


def window_status(total_hours: float, day) -> str:
    """Label a 2-week window as OK / WARNING / BREACH / BREAK."""
    if in_course_break(day):
        return "BREAK"
    if total_hours > VISA_HOUR_LIMIT:
        return "BREACH"
    if total_hours >= VISA_HOUR_LIMIT - WARNING_BUFFER:
        return "WARNING"
    return "OK"


def weekly_hours(df: pd.DataFrame, rate: float = NIGHT_RATE) -> pd.DataFrame:
    """Estimate hours worked each pay week from payroll deposits."""
    pay = df[df["Category"] == "Income"][["Date", "Amount"]].copy()
    pay["Hours"] = (pay["Amount"] / rate).round(1)
    return pay.sort_values("Date").reset_index(drop=True)


def check_windows(weeks: pd.DataFrame) -> pd.DataFrame:
    """Check every pair of back-to-back pay weeks against the limit."""
    rows = []
    for i in range(1, len(weeks)):
        prev, curr = weeks.iloc[i - 1], weeks.iloc[i]
        # if I skipped a week there's no pay, so don't add an old week in
        back_to_back = (curr["Date"] - prev["Date"]).days == 7
        total = curr["Hours"] + (prev["Hours"] if back_to_back else 0)
        rows.append({
            "Window": f"{prev['Date']:%d %b} - {curr['Date']:%d %b}",
            "Hours": total,
            "Status": window_status(total, curr["Date"].date()),
        })
    return pd.DataFrame(rows)


def report(results: pd.DataFrame) -> None:
    print(f"\nVisa hours check (limit: {VISA_HOUR_LIMIT} hrs per 2 weeks)\n")
    for _, r in results.iterrows():
        print(f"  {r['Window']}   {r['Hours']:>5.1f} hrs   {r['Status']}")
    counts = results["Status"].value_counts()
    print(f"\nBreaches: {counts.get('BREACH', 0)}   Warnings: {counts.get('WARNING', 0)}")


if __name__ == "__main__":
    df = add_categories(load_transactions())
    report(check_windows(weekly_hours(df)))