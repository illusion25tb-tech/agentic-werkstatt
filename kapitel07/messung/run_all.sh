#!/bin/sh
# Alle Runs für Kapitel 7, nacheinander (Ollama wird geteilt).
# Nur llama3.2-16k, je Bedingung höchstens 3 Runs.
PY=../.venv/Scripts/python.exe
$PY run_nl105.py diff_spec 3
$PY run_nl105.py diff_roh 3
$PY run_nl105.py plan 3
