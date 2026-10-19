#!/bin/sh
# Nacheinander ausfuehren (Ollama auf einer GPU)
cd "$(dirname "$0")/.."
.venv/Scripts/python -u messung/einstieg.py einstieg_default.jsonl > messung/einstieg_default.log 2>&1
.venv/Scripts/python -u messung/request_beispiel.py > messung/request_beispiel.log 2>&1
.venv/Scripts/python -u messung/tokens_de_en.py > messung/tokens_de_en.log 2>&1
.venv/Scripts/python -u messung/streuung_temp.py > messung/streuung_temp.log 2>&1
.venv/Scripts/python -u messung/klassifizierer.py break,harden llama3.2:3b,gemma3:4b,phi4-mini >> messung/klassifizierer.log 2>&1
