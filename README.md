# agentic-werkstatt

Begleit-Repository zum Buch „Durchstarten mit Agentic Coding“ von Thorsten Behder (2026).

Hier liegt der gesamte Code des Buchs: der Übungsservice, die Tickets, die Listings jedes Kapitels mit Tests und die Skripte, mit denen die Messwerte im Buch entstanden sind.

## Aufbau

| Ordner | Inhalt |
|---|---|
| `bestellservice/` | Der Running Case: ein FastAPI-Service mit pytest-Suite, an dem alle Agenten arbeiten |
| `issues/` | Die 20 Tickets NL-101 bis NL-120 |
| `solutions/` | Referenz-Patches zu einzelnen Tickets |
| `kapitelNN/` | Code je Kapitel, meist mit `starter/`, `solution/` und `messung/` |
| `evals/` | Eval-Aufgaben, inklusive verdeckter Tests (Kap. 10) |
| `egress/` | Musterkonfiguration für einen Egress-Proxy (ungetestet) |
| `anhang_f/` | Beispiele zu Anhang F „Python kompakt“ |

## Loslegen

```bash
git clone https://github.com/<IHR-KONTO>/agentic-werkstatt.git
cd agentic-werkstatt/bestellservice
uv sync
uv run pytest
```

Die Einrichtung von Terminal, Python, uv und Git beschreibt Kapitel 2. Jedes Kapitel hat seine eigene virtuelle Umgebung; die Tests laufen mit einem geskripteten Modell und brauchen keinen API-Schlüssel.

Für echte Modellläufe erwartet `llm.py` einen OpenAI-kompatiblen Endpunkt, im Buch Ollama lokal. Vorlage: `.env.example` (nach `.env` kopieren, `.env` wird nicht eingecheckt).

## Versionen

Getestete Versionen stehen in `VERSIONS.md`. Die Workflows unter `kapitel14/` liegen bewusst nicht im Wurzelordner `.github/` und laufen in diesem Repository nicht; kopieren Sie sie in Ihr eigenes Projekt.
