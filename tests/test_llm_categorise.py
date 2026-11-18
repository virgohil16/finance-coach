"""Tests for the LLM fallback - uses a fake client so no API key or internet needed."""
from types import SimpleNamespace

import pandas as pd

from src.llm_categorise import ask_llm, fill_uncategorised


class FakeClient:
    """Pretends to be the Groq client. Gives a set reply and counts calls."""
    def __init__(self, reply):
        self.reply = reply
        self.calls = 0
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.calls += 1
        msg = SimpleNamespace(content=self.reply)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_valid_answer_is_accepted():
    assert ask_llm("PAYPAL *STEAMGAMES", FakeClient("Entertainment")) == "Entertainment"


def test_off_list_answer_is_rejected():
    # model makes up its own category -> don't trust it
    assert ask_llm("PAYPAL *STEAMGAMES", FakeClient("Video Games")) == "Uncategorised"


def test_cache_stops_repeat_api_calls(tmp_path):
    df = pd.DataFrame({
        "Description": ["SMP*KMART CHADSTONE", "SMP*KMART CHADSTONE"],
        "Category": ["Uncategorised", "Uncategorised"],
    })
    client = FakeClient("Shopping")
    cache = tmp_path / "cache.json"

    fill_uncategorised(df, client, cache)
    fill_uncategorised(df, client, cache)  # second run should hit the cache

    assert client.calls == 1


def test_rule_categorised_rows_are_untouched(tmp_path):
    df = pd.DataFrame({
        "Description": ["WOOLWORTHS CLAYTON", "TICKETEK AUSTRALIA"],
        "Category": ["Groceries", "Uncategorised"],
    })
    result = fill_uncategorised(df, FakeClient("Entertainment"), tmp_path / "c.json")
    assert list(result["Category"]) == ["Groceries", "Entertainment"]