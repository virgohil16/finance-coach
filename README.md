# finance-coach

An AI-powered personal finance tool built for **international students in Australia**.

Most budgeting apps assume you're a local working adult. International students deal with stuff those apps ignore: a 48-hour fortnightly work limit on their visa, money coming in from family overseas, money going back home, and casual jobs with irregular pay. finance-coach is built around those problems.

> **Status:** in active development. Core data pipeline, categorisation and visa hours tracking are working. Dashboard and AI features are next (see [Roadmap](#roadmap)).

---

## What it does so far

- **Loads Australian bank CSV exports** and validates them, with Aussie `DD/MM/YYYY` dates handled properly
- **Categorises every transaction** using regex rules first, then an LLM fallback for the messy ones (`SQ *`, `SMP*`, `PAYPAL *` style merchant names)
  - Rules alone: **96%** coverage on the sample data
  - Rules + LLM: **100%**
- **Editable LLM cache.** Every LLM answer is saved, so the same merchant never costs a second API call, and if the model gets one wrong you can fix it in the cache and the correction sticks
- **Visa work-hours tracker.** Estimates hours worked from weekly pay deposits and checks every rolling 2-week window against the 48-hour limit (student visa condition 8105). Course breaks are skipped since there's no limit then

### Example: visa hours check

```
Visa hours check (limit: 48 hrs per 2 weeks)

  29 Apr - 06 May    40.0 hrs   OK
  06 May - 13 May    50.0 hrs   BREACH
  13 May - 20 May    52.0 hrs   BREACH
  20 May - 27 May    46.0 hrs   WARNING
  27 May - 03 Jun    42.0 hrs   OK
  17 Jun - 24 Jun    38.0 hrs   BREAK

Breaches: 2   Warnings: 1
```

One heavy week shows up as a breach in **both** windows it's part of. A tracker that only checked fixed pay fortnights would miss one of them.

---

## How it works

```
bank CSV
   │
   ▼
data_loader.py      load + validate + parse AU dates
   │
   ▼
categorise.py       regex rules (fast, free, predictable)
   │
   ▼
llm_categorise.py   LLM fallback for whatever the rules missed (+ cache)
   │
   ├──► visa_tracker.py    rolling 2-week work hours check
   └──► (next) dashboard, analysis, AI features
```

### Design decisions

- **Rules before the LLM.** Regex is free, instant and predictable, so the LLM only sees the few transactions the rules can't handle.
- **Don't trust raw LLM output.** The model's answer is only accepted if it exactly matches one of the allowed categories. Anything else stays `Uncategorised`.
- **Rolling windows, not pay periods.** The visa limit applies to any 2-week period, so every pair of back-to-back weeks gets checked. A skipped week (no pay) isn't wrongly added into the next window.
- **Hours are estimated from pay.** Bank statements show pay, not hours, so hours = pay ÷ hourly rate. The rate lives in `config.py` so it's easy to change.
- **Tests don't need an API key.** The LLM tests use a fake client, so the whole suite runs offline in under a second.
- **`dayfirst=True`.** pandas assumes US date format by default, which silently turns 01/04 into January 4th instead of April 1st.

---

## Tech stack

| Area | Tools |
|---|---|
| Language | Python 3.13 |
| Data | pandas |
| LLM | Groq API (`openai/gpt-oss-20b`) |
| Testing | pytest |
| Config | python-dotenv |
| Planned | Streamlit, Prophet |

---

## Getting started

### 1. Clone and set up

```bash
git clone https://github.com/virgohil16/finance-coach.git
cd finance-coach
python -m venv venv
```

Activate the virtual environment:

```powershell
# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

```bash
# Mac / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Add your API key

Get a free key from [console.groq.com](https://console.groq.com), then:

```powershell
# Windows
copy .env.example .env
```

```bash
# Mac / Linux
cp .env.example .env
```

Open `.env` and replace the placeholder with your key. `.env` is gitignored, so it never gets committed.

### 3. Run it

Always run from the project root using `python -m`:

```bash
python -m src.generate_sample    # create sample data
python -m src.categorise         # rule-based categories + coverage
python -m src.llm_categorise     # LLM fallback for the rest
python -m src.visa_tracker       # visa work hours check
python -m pytest -v              # run all tests
```

---

## Project structure

```
finance-coach/
├── data/
│   └── sample_transactions.csv   # synthetic data (safe to commit)
├── src/
│   ├── config.py                 # pay rates, visa limit, course breaks, LLM model
│   ├── data_loader.py            # load + validate CSVs
│   ├── categorise.py             # regex categoriser
│   ├── llm_categorise.py         # LLM fallback + cache
│   ├── visa_tracker.py           # rolling 2-week hours check
│   └── generate_sample.py        # builds realistic sample data
├── tests/                        # 14 tests, all offline
├── notebooks/
├── .env.example
└── requirements.txt
```

---

## Roadmap

- [x] Project setup, sample data generator, validated CSV loader
- [x] Rule-based categorisation + LLM fallback (96% → 100% coverage)
- [x] Visa work-hours tracker (rolling 2-week windows, condition 8105)
- [ ] Streamlit dashboard + live demo
- [ ] Subscription detector (find recurring charges you forgot about)
- [ ] Anomaly detection (spending that doesn't match your usual pattern)
- [ ] Spending forecast (Prophet)
- [ ] "Ask my finances": chat with your own transaction history
- [ ] AUD → INR exchange rate trends
- [ ] Bank PDF statement parsing

---

## Privacy

- The sample data is **completely synthetic**. No real bank data is in this repo.
- Real CSVs, PDFs, the LLM cache and `.env` are all gitignored.
- Only merchant descriptions that the rules couldn't categorise are sent to the LLM. Amounts and balances never are.

## Disclaimer

finance-coach shows insights about your own spending. It is **not financial advice**. Visa work hours are **estimates** based on pay deposits. Always check your actual visa conditions on [VEVO](https://immi.homeaffairs.gov.au/visas/already-have-a-visa/check-visa-details-and-conditions) or with the Department of Home Affairs.

---

## Author

**Vir Gohil**, Bachelor of Computer Science (AI & Data Science), Monash University

[GitHub](https://github.com/virgohil16)
