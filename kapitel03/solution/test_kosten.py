import pytest

from kosten import kosten


def test_rechenbeispiel():
    usage = {"prompt_tokens": 1_000, "completion_tokens": 200}
    # 1.000 x 2,00 + 200 x 10,00 pro Million = 0,004
    assert kosten(usage, 2.00, 10.00) == pytest.approx(0.004)


def test_fehlende_felder():
    assert kosten({}, 2.00, 10.00) == 0
    assert kosten({"prompt_tokens": 500_000}, 2.0, 10.0) == 1.0
