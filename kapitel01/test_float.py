"""Die Float-Rechnung aus Kapitel 1 (Ticket NL-101), mit + statt sum().

Gleiche Reihenfolge wie cart.cart_subtotal im bestellservice:
3 x SP-120 (13,70), HL-750 (7,80), ZB-01 (1,10).
"""


def test_drei_mal_null_komma_eins():
    assert 0.1 + 0.1 + 0.1 != 0.3


def test_ticket_warenkorb():
    subtotal = 13.70 * 3 + 7.80 + 1.10
    assert repr(13.70 * 3) == "41.099999999999994"
    assert repr(subtotal) == "49.99999999999999"
    assert not subtotal > 50.0       # Basisstand
    assert not subtotal >= 50.0      # nur >= reicht nicht
    assert round(subtotal, 2) == 50.0  # Anzeige: 50,00 EUR
