# ADR 0002: Security Reviewer als Code statt Modellrolle

Status: angenommen, 21.10.2026 (Miriam Kessler)

## Kontext
Der Release Engineer soll vor jeder Empfehlung prüfen, ob
ein Run Tests geändert, die Policy berührt oder neue
Abhängigkeiten eingeführt hat. Diese Fragen haben eindeutige
Antworten.

## Entscheidung
Der Security Reviewer ist Code: die Policy des Harness
(Kap. 9, 11) je Tool Call und security_review() je Diff.

## Alternativen
- Modellrolle „prüfe auf Risiken“: streut, kostet Token
  und liest selbst Text, der Prompt Injection tragen kann.
- keine eigene Rolle: alles bleibt beim Review im PR.

## Konsequenzen
- deterministisch, mit pytest geprüft, ohne Tokenkosten
- erkennt nur, was als Regel formuliert ist
- semantische Risiken bleiben beim menschlichen Review

## Beleg
- Report: kapitel16/messung/report.log, Spalte Policy
- Trace: kapitel12/messung/ergebnisse_multi/NL-120/run_3
  Coder will zweimal einen bestehenden Test überschreiben,
  die Policy lehnt beide Male ab.
- Fault Injection: kapitel16/messung/fault_matrix.log
  abhaengigkeit: starter empfiehlt, solution eskaliert

## Was die Entscheidung ändern würde
Ein Fall im Golden Task Set, den eine Modellrolle in zwei
von drei Runs findet und die Regeln nicht.
