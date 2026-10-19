import pytest

from contracts import ToolError
from tools import GROUNDING


def test_route_mit_decorator_und_zeilen():
    out = GROUNDING.call("outline",
                         {"path": "bestellservice/api.py"})
    assert ("182-185 def post_label @router.post("
            "'/orders/{order_id}/label', status_code=201)"
            ) in out.splitlines()


def test_klassen_methoden_und_konstanten():
    out = GROUNDING.call("outline",
                         {"path": "bestellservice/tariffs.py"})
    assert "33 BULKY_FROM_KG" in out
    assert any(z.startswith("14-") and "class Tariff" in z
               for z in out.splitlines())


def test_nur_python():
    with pytest.raises(ToolError) as e:
        GROUNDING.call("outline", {"path": "README.md"})
    assert e.value.kind == "invalid_args"
