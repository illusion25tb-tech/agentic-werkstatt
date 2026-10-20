"""Grenzfälle und von Hand nachgerechnete Werte."""
from pytest import approx

from stats import pass_at_k, pass_hat_k, wilson


def test_pass_at_k():
    assert pass_at_k(3, 0, 3) == 0.0
    assert pass_at_k(3, 3, 3) == 1.0
    assert pass_at_k(3, 2, 1) == approx(2 / 3)
    assert pass_at_k(10, 3, 2) == approx(1 - 21 / 45)


def test_pass_hat_k():
    assert pass_hat_k(3, 2, 3) == 0.0
    assert pass_hat_k(3, 3, 3) == 1.0
    assert pass_hat_k(10, 3, 2) == approx(3 / 45)


def test_wilson():
    assert wilson(0, 10) == approx((0.0, 0.27754), abs=1e-5)
    assert wilson(10, 10) == approx((0.72246, 1.0), abs=1e-5)
    assert wilson(2, 3) == approx((0.20765, 0.93851),
                                  abs=1e-5)
    assert wilson(0, 0) == (0.0, 1.0)
