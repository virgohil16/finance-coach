"""Tests for the chat - fake client, so no API key or internet needed."""
from types import SimpleNamespace

import pandas as pd

from src.ask import ask, build_summary


class FakeClient:
    """Pretends to be Groq and remembers what got sent to it."""
    def __init__(self, reply="ok"):
        self.reply = reply
        self.sent = None
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.sent = kwargs["messages"]
        msg = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def make_df():
    return pd.DataFrame({
        "Date": pd.to_datetime(["2026-05-01", "2026-05-08", "2026-05-14"]),
        "Description": ["UBER EATS", "MENULOG", "HUNGRY JACKS PAYROLL"],
        "Amount": [-10.0, -20.0, 500.0],
        "Category": ["Food Delivery", "Food Delivery", "Income"],
    })


def test_summary_has_precomputed_totals():
    summary = build_summary(make_df())
    assert "Food Delivery" in summary
    assert "30.0" in summary  # 10 + 20 added up by pandas, not the LLM


def test_question_and_data_are_sent():
    client = FakeClient()
    ask("How much on delivery?", make_df(), client)
    assert "DATA SUMMARY" in client.sent[0]["content"]
    assert client.sent[-1] == {"role": "user", "content": "How much on delivery?"}


def test_chat_history_is_included():
    client = FakeClient()
    history = [{"role": "user", "content": "hi"},
               {"role": "assistant", "content": "hello"}]
    ask("and in May?", make_df(), client, history)
    assert client.sent[1:3] == history


def test_returns_the_model_answer():
    assert ask("q", make_df(), FakeClient("You spent $30.")) == "You spent $30."