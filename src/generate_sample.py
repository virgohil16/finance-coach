"""Generate realistic Aus international student sample transactions.

Creates ~3 months of bank transactions for a CS student in Melbourne working
casually at Hungry Jack's. Used to develop and test finance-coach without
exposing real bank data. Deterministic via fixed random seed.

Run from anywhere: `python src/generate_sample.py`
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # reproducible output

START_DATE = date(2026, 4, 1)
END_DATE = date(2026, 6, 30)
OPENING_BALANCE = 1200.00
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_transactions.csv"

txns = []  # collect as (date, description, amount); compute balance later


def add(d: date, desc: str, amt: float) -> None:
    txns.append((d, desc, round(amt, 2)))


# Fortnightly HJ pay — every other Thursday, variable casual hours
d = START_DATE
while d.weekday() != 3:  # 3 = Thursday
    d += timedelta(days=1)
while d <= END_DATE:
    hours = random.choice([16, 18, 20, 22, 24])
    add(d, "HUNGRY JACKS PAYROLL", hours * 27.00)
    d += timedelta(days=14)

# Weekly rent — Mondays
d = START_DATE
while d.weekday() != 0:
    d += timedelta(days=1)
while d <= END_DATE:
    add(d, "TRANSFER TO LANDLORD - RENT", -290.00)
    d += timedelta(days=7)

# Monthly recurring subscriptions (subscription detector will find these)
subs = [
    (3, "SPOTIFY AU PREMIUM", -8.99),
    (7, "NETFLIX.COM AU", -16.99),
    (12, "ANTHROPIC CLAUDE PRO", -29.00),
    (15, "ADOBE CC STUDENT", -23.99),
    (25, "BELONG MOBILE", -25.00),
]
for day_of_month, desc, amt in subs:
    for month in (4, 5, 6):
        add(date(2026, month, day_of_month), desc, amt)

# Daily-ish discretionary spending
d = START_DATE
while d <= END_DATE:
    # Groceries 3-4x per week
    if random.random() < 0.45:
        store = random.choice(["WOOLWORTHS CLAYTON", "COLES CAULFIELD", "ALDI HUGHESDALE"])
        add(d, store, -round(random.uniform(8, 65), 2))
    # Food delivery (Vir's weak spot — happens too often, perfect for AI advice)
    if random.random() < 0.30:
        merchant = random.choice([
            "UBER * EATS HELP.UBER.COM",
            "MENULOG MELBOURNE",
            "DOORDASH DASHPASS",
        ])
        add(d, merchant, -round(random.uniform(15, 45), 2))
    # Weekday coffee
    if random.random() < 0.40 and d.weekday() < 5:
        cafe = random.choice([
            "MONASH CAMPUS CAFE",
            "STARBUCKS CAULFIELD",
            "PETES MARKET CAFE",
        ])
        add(d, cafe, -round(random.uniform(4.5, 6.5), 2))
    # Myki auto top-up (~weekly)
    if random.random() < 0.10:
        add(d, "MYKI AUTO TOP UP PTV", -40.00)
    d += timedelta(days=1)

# One-off events
add(date(2026, 4, 12), "INTL TRANSFER FROM IN - PARENTS", 1500.00)
add(date(2026, 5, 18), "WISE TRANSFER TO INR - FAMILY", -800.00)
add(date(2026, 6, 5), "INTL TRANSFER FROM IN - PARENTS", 1200.00)

# Anomaly — a big Uber Eats charge well above normal (anomaly detection will flag)
add(date(2026, 5, 24), "UBER * EATS HELP.UBER.COM", -89.50)

# Bank fees (intl card)
add(date(2026, 4, 30), "FOREIGN TRANSACTION FEE", -3.50)
add(date(2026, 5, 31), "FOREIGN TRANSACTION FEE", -2.10)

# Sort chronologically, then compute running balance
txns.sort(key=lambda x: x[0])

rows = []
balance = OPENING_BALANCE
for d, desc, amt in txns:
    balance += amt
    rows.append({
        "Date": d.strftime("%d/%m/%Y"),
        "Description": desc,
        "Amount": amt,
        "Balance": round(balance, 2),
    })

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Date", "Description", "Amount", "Balance"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} transactions -> {OUTPUT_PATH.name}")
print(f"Date range: {START_DATE} to {END_DATE}")
print(f"Closing balance: ${balance:.2f}")
