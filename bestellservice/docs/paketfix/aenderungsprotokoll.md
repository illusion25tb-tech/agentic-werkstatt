# Änderungsprotokoll der PaketFix Versand-API

> Hinweis: PaketFix ist fiktiv. Dieses Dokument ist synthetisches
> Übungsmaterial.

## Version 2.3 (gültig ab 01.09.2026)

- Adresszeilen (`name`, `name2`, `strasse`, `ort`) dürfen jetzt 35 statt 30
  Zeichen lang sein. Das gedruckte Label zeigt ebenfalls 35 Zeichen je Zeile.
- Neuer Fehlercode `PF-2002` für gesperrte Schlüssel.

## Version 2.2 (gültig ab 01.04.2026)

- Neues Produkt `PF-SPG` (Sperrgut) für Sendungen über 31,5 kg bis 60 kg.
- Sendungen über 31,5 kg mit einem Standardprodukt lehnt die API ab
  (`PF-1004`). Bei der Einlieferung mit selbst gedrucktem Label wird die
  Differenz nachberechnet.
- `PF-STD-XL` gilt nur noch bis einschließlich 31,5 kg.

## Version 2.1 (gültig ab 15.01.2026)

- Beschreibung der Prüfziffer der Sendungsnummer ergänzt (Modulo 10, Gewichte 3
  und 1, beginnend rechts).
- Ankündigung: Ab 01.10.2026 prüfen die Depotscanner die Prüfziffer und weisen
  falsche Nummern mit `PF-1006` zurück.

## Version 2.0 (gültig ab 01.09.2025)

- Erste Fassung der REST-Schnittstelle, ersetzt den Dateiaustausch per CSV.
- Header `Idempotency-Key` für `POST /sendungen`.
