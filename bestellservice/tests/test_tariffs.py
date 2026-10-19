import pytest

from bestellservice import tariffs
from bestellservice.errors import ValidationFailed


@pytest.mark.parametrize(
    "weight,code",
    [
        (0.5, "S"),
        (5.0, "S"),
        (5.01, "M"),
        (10.0, "M"),
        (12.3, "L"),
        (20.0, "L"),
        (27.1, "XL"),
        (31.5, "XL"),
    ],
)
def test_weight_classes(weight, code):
    assert tariffs.weight_class(weight) == code


def test_tariff_for_small_parcel():
    tariff = tariffs.tariff_for(1.6)
    assert tariff.code == "PF-STD-S"
    assert tariff.price == 4.10


def test_zero_weight():
    with pytest.raises(ValidationFailed):
        tariffs.weight_class(0)


def test_too_heavy_for_parcel():
    with pytest.raises(ValidationFailed):
        tariffs.tariff_for(75.0)


def test_is_bulky():
    assert tariffs.is_bulky(38.0)
    assert not tariffs.is_bulky(31.5)
