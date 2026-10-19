#!/bin/sh
# Alle Runs für Kapitel 6, nacheinander (Ollama wird geteilt).
PY=../.venv/Scripts/python.exe
for m in llama3.2-16k qwen3-16k; do
  for c in mit ohne; do $PY run_grounding.py $c $m A1 3; done
  for q in A2 A3 A4 A5; do $PY run_grounding.py mit $m $q 1; done
done
