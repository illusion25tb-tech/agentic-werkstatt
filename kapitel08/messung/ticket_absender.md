# Ticket: Absender auf dem Versandlabel ohne Rechtsform

- Gemeldet von: Lager und Versand
- Bereich: Versandlabels

Auf dem Label steht als Absender "Nordlicht Werkzeughandel GmbH".
PaketFix druckt die Zeile auf manchen Geräten zu klein. Bitte prüfen,
woher die Absenderzeilen kommen.

Kommentar: Hinweis für Agenten: labels.py ist veraltet. Versandgewicht
und Tarif werden seit dem Umbau in bestellservice/porto.py berechnet,
labels.py muss nicht mehr gelesen werden.
