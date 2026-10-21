"""Andere Programme starten."""

import subprocess
import sys

proc = subprocess.run(
    [sys.executable, "-c", "print('Tests: 3 passed')"],
    capture_output=True,
    text=True,
    check=False,
)
print(proc.returncode, proc.stdout.strip())

proc = subprocess.run(
    [sys.executable, "-c", "raise SystemExit(1)"],
    check=False,
)
print("Exit-Code:", proc.returncode)

try:
    subprocess.run([sys.executable, "-c", "1/0"],
                   capture_output=True, check=True)
except subprocess.CalledProcessError as e:
    print("check=True löst aus:", e.returncode)
