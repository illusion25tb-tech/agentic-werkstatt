from bestellservice.shipping_costs import (
    missing_for_free_shipping,
    shipping_cost,
)


def test_below_threshold():
    assert shipping_cost(29.90) == 4.95


def test_clearly_above_threshold():
    assert shipping_cost(75.00) == 0.0


def test_just_above_threshold():
    assert shipping_cost(50.01) == 0.0


def test_missing_amount():
    assert missing_for_free_shipping(42.50) == 7.50


def test_nothing_missing_above():
    assert missing_for_free_shipping(80.0) == 0.0


def test_no_free_shipping_abroad():
    assert missing_for_free_shipping(80.0, "AT") is None
