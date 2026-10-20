# Getestete Versionen

Zuletzt geprüft: 21.10.2026, Windows 11 Home, Git Bash.

| Werkzeug / Paket | Version | Wo |
|---|---|---|
| Python | 3.12.10 | alle Kapitel |
| uv | 0.13.1 | ab Kap. 2 |
| pytest | 9.1.1 | alle Kapitel |
| Ruff | 0.17.1 | alle Kapitel |
| FastAPI | 0.149.0 | bestellservice |
| pydantic | 2.14.1 | ab Kap. 9 |
| pydantic-ai-slim[openai] | 2.57.0 | Kap. 9-12 |
| opentelemetry-sdk | 1.45.1 | Kap. 13 |
| PyYAML | 6.0.3 | Kap. 14, 16 |
| Ollama | 0.40.4 | Modellläufe |
| Modell | llama3.2:3b, num_ctx 16384 (`llama3.2-16k`) | Messungen ab Kap. 6 |
| Docker Engine / Desktop | 29.8.2 / 4.95 (WSL2) | Kap. 11 |

Nicht ausgeführt: GitHub-Workflows (Kap. 14, 16), Docker-Build
Kap. 14, Langfuse/Logfire (Kap. 13), Egress-Proxy (`egress/`).
