# AGENTS.md für den bestellservice

## Befehle
- Tests: `python -m pytest -q`
- Lint: `ruff check .`
- Server lokal: `uvicorn bestellservice.main:app --reload`

## Aufbau
- Paketcode in `bestellservice/`, Tests in `tests/`.
- Versandkosten für Kunden: `bestellservice/shipping_costs.py`.
  Die Modultabelle der README ist veraltet (NL-109).
- PaketFix-Tarife: `bestellservice/tariffs.py`,
  Versandlabels: `bestellservice/labels.py`.
- PaketFix-Doku: `docs/paketfix/`, Version steht im Kopf.

## Regeln
- Geldbeträge in neuem Code mit `Decimal`, nicht `float`.
- Jede Verhaltensänderung braucht einen Test in `tests/`.
- Keine echten Personendaten in Tests und Beispielen,
  nur erfundene wie "Erika Musterfrau".
- `orders.py` nicht weiter vergrößern (NL-110).

## Nicht hier geregelt
- Welche Befehle ein Agent ausführen darf, legt der
  Harness fest, nicht diese Datei.
