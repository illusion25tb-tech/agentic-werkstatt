# Datenschutzrichtlinie für Geschäftskunden der PaketFix Versand-API

- Dokumentversion: 1.4
- Stand: 01.07.2026

> Hinweis: PaketFix ist ein fiktiver Versanddienstleister. Dieses Dokument ist
> synthetisch, dient ausschließlich als Übungsmaterial und ist keine
> Rechtsberatung. Alle Namen, Anschriften und Kontaktdaten sind erfunden.

## 1. Verantwortliche Stelle

PaketFix Logistik GmbH (fiktiv)
Beispielallee 5
12345 Musterstadt
E-Mail: `datenschutz@paketfix.example`

Datenschutzbeauftragter: Max Mustermann, erreichbar unter
`dsb@paketfix.example`.

## 2. Geltungsbereich

Diese Richtlinie gilt für personenbezogene Daten, die Geschäftskunden über die
Versand-API (Version 2) an PaketFix übermitteln. Sie ergänzt den
Beförderungsvertrag und die Schnittstellenbeschreibung `paketfix_api_v2.md`.

## 3. Welche Daten verarbeitet werden

| Datenkategorie | Felder in der API | Zweck |
|---|---|---|
| Empfängername | `empfaenger.name`, `empfaenger.name2` | Zustellung |
| Lieferanschrift | `strasse`, `plz`, `ort`, `land` | Zustellung, Leitweg |
| Avis-E-Mail | `avis_email` | Ankündigung der Zustellung |
| Sendungsdaten | `gewicht_kg`, `produkt`, `referenz` | Beförderung, Abrechnung |
| Zustellnachweis | Unterschrift oder Ablageort | Nachweis gegenüber dem Absender |

Die Avis-E-Mail ist freiwillig. Geschäftskunden übermitteln sie nur, wenn der
Empfänger der Weitergabe an PaketFix zugestimmt hat. Telefonnummern werden über
die API nicht angenommen.

## 4. Grundsätze für Geschäftskunden

1. **Datenminimierung:** Übermitteln Sie nur die Felder, die für die Zustellung
   nötig sind. Das Feld `referenz` darf keine Namen, E-Mail-Adressen oder
   Kundennummern Ihrer Endkunden enthalten. Verwenden Sie eine Bestellnummer.
2. **Zweckbindung:** Sendungsdaten, die Sie über `GET /sendungen` abrufen, dürfen
   Sie nur zur Sendungsverfolgung und Kundenbetreuung verwenden.
3. **Keine Protokollierung im Klartext:** Anfragen und Antworten mit
   Empfängerdaten dürfen in Ihren Anwendungsprotokollen nur gekürzt oder
   pseudonymisiert erscheinen (zum Beispiel `E. M.`, `01xxx Dresden`).
4. **Schlüsselschutz:** Der API-Schlüssel ist ein Zugangsdatum. Er gehört in eine
   geschützte Konfiguration, nicht in Quellcode oder Tickets.

## 5. Speicherdauer bei PaketFix

| Daten | Speicherdauer |
|---|---|
| Empfängername und Anschrift | 90 Tage nach Zustellung |
| Avis-E-Mail | bis zur Zustellung, danach gelöscht |
| Zustellnachweis | 12 Monate nach Zustellung |
| Abrechnungsdaten ohne Empfängerdaten | nach den gesetzlichen Aufbewahrungsfristen |

Zurückgezogene Sendungen (`DELETE /sendungen/{sendungsnummer}`) löscht PaketFix
innerhalb von 7 Tagen vollständig.

## 6. Weitergabe

PaketFix gibt Empfängerdaten nur an Zustellpartner im Zielland weiter, soweit das
für die Zustellung nötig ist. Eine Weitergabe zu Werbezwecken findet nicht statt.

## 7. Sandbox und Testdaten

In der Sandbox (`https://sandbox.paketfix.example/v2`) sind ausschließlich
synthetische Personendaten erlaubt. Verwenden Sie offensichtlich erfundene
Namen und Anschriften, zum Beispiel:

```json
{
  "name": "Erika Musterfrau",
  "strasse": "Musterstraße 1",
  "plz": "01067",
  "ort": "Dresden",
  "land": "DE"
}
```

Echte Kundendaten, auch einzelne, dürfen nicht in die Sandbox, nicht in
Testfälle und nicht in Beispieldateien von Quellcode-Repositories gelangen.
Werden echte Daten in der Sandbox festgestellt, sperrt PaketFix den betroffenen
Sandbox-Schlüssel und löscht die Daten.

## 8. Rechte der betroffenen Personen

Empfänger können Auskunft, Berichtigung und Löschung ihrer bei PaketFix
gespeicherten Daten verlangen. Anfragen, die Geschäftskunden erreichen, leiten
diese unter Angabe der Sendungsnummer an `datenschutz@paketfix.example` weiter.

## 9. Sicherheitsvorfälle

Stellt ein Geschäftskunde fest, dass Empfängerdaten aus der Schnittstelle
unbefugt offengelegt wurden (etwa durch einen veröffentlichten API-Schlüssel),
meldet er dies unverzüglich an `security@paketfix.example`.
