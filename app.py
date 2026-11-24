"""finance-coach dashboard.

Run locally:  streamlit run app.py
Uploaded files are only processed in memory - nothing gets saved.
"""
import logging

import altair as alt
import streamlit as st

from src.categorise import add_categories
from src.config import NIGHT_RATE
from src.data_loader import DEFAULT_CSV, load_transactions
from src.visa_tracker import check_windows, weekly_hours
from src.subscriptions import find_subscriptions
from src.anomalies import find_anomalies
from src.ask import ask
from src.llm_categorise import fill_uncategorised, make_client

st.set_page_config(page_title="finance-coach", page_icon="💸", layout="wide")

st.title("finance-coach")
st.caption("Spending insights for international students in Australia. "
           "Not financial advice. Visa hours are estimates, check VEVO for your real conditions.")

# --- sidebar: data + settings ---
with st.sidebar:
    st.header("Your data")
    upload = st.file_uploader("Upload a bank CSV", type="csv")
    st.caption("Needs columns: Date, Description, Amount, Balance. "
               "Your file is processed in memory and never stored. "
               "Merchant names the rules can't recognise are sent to an AI model "
               "to categorise. Amounts are only sent if you use the chat.")
    rate = st.number_input(
        "Your hourly pay rate ($)", min_value=1.0, value=NIGHT_RATE, step=0.5,
        help="Used to estimate hours worked from your pay deposits.",
    )

# --- load ---
try:
    df = load_transactions(upload if upload else DEFAULT_CSV)
except ValueError as e:
    st.error(f"Couldn't read that file: {e}")
    st.stop()

if not upload:
    st.info("Showing sample data. Upload your own CSV in the sidebar.")

# --- categorise: rules first, then LLM for whatever's left ---
df = add_categories(df)

# per-visitor cache in memory, so reruns don't hit the API again
if "llm_cache" not in st.session_state:
    st.session_state.llm_cache = {}
try:
    df = fill_uncategorised(df, cache_path=None, cache=st.session_state.llm_cache)
except Exception:
    # full error goes to the terminal / Cloud logs, user just sees a friendly note
    logging.exception("LLM categorisation failed")
    st.warning("AI categorisation is unavailable right now, "
               "so some transactions are left as Uncategorised.")

spend = df[df["Amount"] < 0]

# --- headline numbers ---
money_in = df[df["Amount"] > 0]["Amount"].sum()
money_out = -spend["Amount"].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Money in", f"${money_in:,.0f}")
c2.metric("Money out", f"${money_out:,.0f}")
c3.metric("Net", f"${money_in - money_out:,.0f}")

# --- spending ---
left, right = st.columns(2)

with left:
    st.subheader("Where the money went")
    by_cat = (-spend.groupby("Category")["Amount"].sum()).reset_index(name="Spent")
    cat_chart = alt.Chart(by_cat).mark_bar().encode(
        x=alt.X("Spent:Q", title="$ spent"),
        y=alt.Y("Category:N", sort="-x", title=None),  # biggest spend at the top
        tooltip=["Category", alt.Tooltip("Spent:Q", format="$,.0f")],
    )
    st.altair_chart(cat_chart)

with right:
    st.subheader("Spending per month")
    months = spend["Date"].dt.to_period("M").astype(str).rename("Month")
    monthly = (-spend.groupby(months)["Amount"].sum()).reset_index(name="Spent")
    month_chart = alt.Chart(monthly).mark_bar().encode(
        x=alt.X("Month:N", title=None, axis=alt.Axis(labelAngle=0)),  # flat labels
        y=alt.Y("Spent:Q", title="$ spent"),
        tooltip=["Month", alt.Tooltip("Spent:Q", format="$,.0f")],
    )
    st.altair_chart(month_chart)

# --- subscriptions ---
st.subheader("Subscriptions")
subs = find_subscriptions(df)

if subs.empty:
    st.write("No recurring monthly charges found.")
else:
    total = subs["Monthly cost"].sum()
    # \$ because streamlit treats $...$ as a maths formula
    st.write(f"Found **{len(subs)}** charges that repeat every month: "
             f"**\\${total:,.2f}/month**, or **\\${total * 12:,.2f}/year**.")
    st.dataframe(
        subs.style.format({"Monthly cost": "${:.2f}", "Yearly cost": "${:.2f}"}),
        hide_index=True,
    )

# --- unusual spending ---
st.subheader("Unusual spending")
anomalies = find_anomalies(df)

if anomalies.empty:
    st.write("Nothing out of the ordinary.")
else:
    st.write(f"**{len(anomalies)}** transaction(s) well above what you usually "
             "spend in that category.")
    st.dataframe(
        anomalies.style.format({"Amount": "${:.2f}", "Usual": "${:.2f}"}),
        hide_index=True,
    )

# --- visa hours ---
st.subheader("Visa work hours (limit: 48 hrs per 2 weeks)")
windows = check_windows(weekly_hours(df, rate))

if windows.empty:
    st.write("No payroll deposits found in this data.")
else:
    colours = {
        "BREACH": "background-color: #f8d7da; color: #721c24",
        "WARNING": "background-color: #fff3cd; color: #856404",
    }
    styled = (
        windows.style
        .map(lambda s: colours.get(s, ""), subset=["Status"])
        .format({"Hours": "{:.1f}"})
    )
    st.dataframe(styled, hide_index=True)

with st.expander("All transactions"):
    st.dataframe(df, hide_index=True)

# --- ask my finances ---
st.subheader("Ask about your spending")
st.caption("Uses an AI model. Using the chat sends a summary of your spending "
           "(totals, subscriptions and unusual transactions) to the AI provider. "
           "Answers can be wrong and aren't financial advice.")


def show(text: str) -> None:
    # escape $ so streamlit doesn't render dollar amounts as maths
    st.markdown(text.replace("$", "\\$"))


if "chat" not in st.session_state:
    st.session_state.chat = []

for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        show(msg["content"])

if question := st.chat_input("e.g. How much did I spend on food delivery in May?"):
    with st.chat_message("user"):
        show(question)
    try:
        with st.spinner("Thinking..."):
            # only the last 6 messages, so long chats don't blow up the prompt
            answer = ask(question, df, make_client(), st.session_state.chat[-6:])
    except Exception:
        logging.exception("Chat failed")
        answer = "Sorry, I can't answer right now. Try again in a minute."
    with st.chat_message("assistant"):
        show(answer)
    st.session_state.chat += [{"role": "user", "content": question},
                              {"role": "assistant", "content": answer}]