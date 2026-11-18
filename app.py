"""finance-coach dashboard.

Run locally:  streamlit run app.py
Uploaded files are only processed in memory - nothing gets saved.
"""
import altair as alt
import streamlit as st

from src.categorise import add_categories
from src.data_loader import DEFAULT_CSV, load_transactions
from src.visa_tracker import check_windows, weekly_hours

st.set_page_config(page_title="finance-coach", page_icon="💸", layout="wide")

st.title("finance-coach")
st.caption("Spending insights for international students in Australia. "
           "Not financial advice. Visa hours are estimates, check VEVO for your real conditions.")

# --- data source ---
with st.sidebar:
    st.header("Your data")
    upload = st.file_uploader("Upload a bank CSV", type="csv")
    st.caption("Needs columns: Date, Description, Amount, Balance. "
               "Your file is processed in memory and never stored.")

try:
    df = load_transactions(upload if upload else DEFAULT_CSV)
except ValueError as e:
    st.error(f"Couldn't read that file: {e}")
    st.stop()

if not upload:
    st.info("Showing sample data. Upload your own CSV in the sidebar.")

df = add_categories(df)
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

# --- visa hours ---
st.subheader("Visa work hours (limit: 48 hrs per 2 weeks)")
windows = check_windows(weekly_hours(df))

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