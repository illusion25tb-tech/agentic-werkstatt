"""Module importieren."""

import json
import sys
from collections import Counter
from pathlib import Path

print(sys.version_info >= (3, 12))
print(Path("issues/NL-104.md").stem)
print(Counter(["bug", "frage", "bug"]).most_common(1))
print(json.dumps({"issue": "NL-104"}))
