"""Geskriptete Rollen: feste Antworten statt Modell."""
import pytest

from capstone import security_review

DIFF = """--- a/bestellservice/tariffs.py
+++ b/bestellservice/tariffs.py
@@ -12 +12 @@
-    return "XL"
+    return "SPERRGUT"
"""


@pytest.fixture
def roles() -> dict:
    return {
        "planner": lambda issue: "bestellservice/tariffs.py",
        "implementer": lambda plan: DIFF,
        "tester": lambda diff: True,       # steht für pytest
        "security": security_review,       # echter Code
        "release_reviewer":
            lambda diff: "Empfehlung: freigeben",
    }
