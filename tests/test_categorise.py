"""Tests for the rule-based categoriser - mostly the tricky edge cases."""
from src.categorise import categorise


def test_uber_eats_is_food_not_transport():
    assert categorise("UBER * EATS HELP.UBER.COM") == "Food Delivery"


def test_plain_uber_is_transport():
    assert categorise("UBER TRIP MELBOURNE") == "Transport"


def test_coffee_not_caught_by_fee_rule():
    # "COFFEE" contains "FEE" - the \b word boundary stops a false match
    assert categorise("SEVEN SEEDS COFFEE") == "Coffee & Eating Out"


def test_case_insensitive():
    assert categorise("woolworths clayton") == "Groceries"


def test_unknown_merchant_falls_through():
    assert categorise("SQ *RANDOM SHOP 0423") == "Uncategorised"