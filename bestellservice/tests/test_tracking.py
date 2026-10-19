import pytest

from bestellservice import tracking
from bestellservice.errors import ValidationFailed


def test_format():
    number = tracking.make_tracking_number(1)
    assert len(number) == 13
    assert number.startswith("340000000001")


def test_roundtrip():
    for serial in (1, 42, 99999, 1234567890):
        number = tracking.make_tracking_number(serial)
        assert tracking.is_valid(number)


def test_wrong_digit_is_invalid():
    number = tracking.make_tracking_number(42)
    last = (int(number[-1]) + 1) % 10
    assert not tracking.is_valid(number[:-1] + str(last))


def test_invalid_shapes():
    assert not tracking.is_valid("123")
    assert not tracking.is_valid("34000000000AB")


def test_spaces_are_ignored():
    number = tracking.make_tracking_number(7)
    assert tracking.is_valid(tracking.pretty(number))


def test_serial_out_of_range():
    with pytest.raises(ValidationFailed):
        tracking.make_tracking_number(-1)


def test_pretty():
    assert tracking.pretty("3400000000017") == (
        "3400 0000 0001 7"
    )
