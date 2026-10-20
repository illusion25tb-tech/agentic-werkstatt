"""Taint-Policy: Steht fremder Text im Verlauf, entscheidet
der Harness strenger. Geprüft werden Tool und Argumente."""
import sys
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse

BUTLER = Path(__file__).resolve().parents[2] / "kapitel09"
sys.path.insert(0, str(BUTLER / "solution"))   # Kapitel 9

from policy import NEEDS_OK, Policy

from provenance import wrap
from redact_secrets import leaks, redact

READ, WRITE, EXTERNAL = "read", "write", "external"
KLASSE = {"list_files": READ, "read_file": READ,
          "search": READ, "replace_in_file": WRITE,
          "create_test": WRITE, "run_tests": WRITE,
          "http_get": EXTERNAL}
EIGEN = ("bestellservice/*.py", "tests/*.py", "AGENTS.md")
GESPERRT = (".env*", "*.pem", "*.key", "id_*")  # Dateinamen
HOSTS = {"pypi.org", "files.pythonhosted.org"}  # Beispiel


def verdict(tool: str, args: dict, tainted: bool,
            secrets: list[str]) -> tuple[str, str]:
    """(allow, approve oder deny; Grund). Absicht egal."""
    k = KLASSE.get(tool)
    path = str(args.get("path", "")).replace("\\", "/")
    name = path.rsplit("/", 1)[-1]
    if k is None:
        return "deny", f"{tool} ist kein Werkzeug des Agenten"
    if any(fnmatch(name, g) for g in GESPERRT):
        return "deny", f"{name} ist für Agenten gesperrt"
    if leaks(args, secrets):
        return "deny", "Argumente enthalten ein Secret"
    if k == EXTERNAL:
        host = urlparse(str(args.get("url", ""))).hostname
        if host not in HOSTS:
            return "deny", f"{host} fehlt in der Allowlist"
        if tainted:
            return "deny", "kein Netz nach fremdem Text"
        return "approve", "extern"
    if k == WRITE and tainted:
        return "approve", "nach fremdem Text"
    return "allow", ""


def sources(tool: str, args: dict, obs: str) -> list[str]:
    """Woher der Text einer Observation stammt."""
    if tool == "read_file":
        return [str(args.get("path", "")).replace("\\", "/")]
    if tool == "http_get":
        return [str(args.get("url", ""))]
    if tool == "search":                # Datei:Zeile: Text
        return sorted({z.split(":", 1)[0]
                       for z in obs.splitlines() if ":" in z})
    return []                           # Meldungen des Harness


@dataclass
class TaintPolicy(Policy):
    secrets: list[str] = field(default_factory=list)
    tainted_by: list[str] = field(default_factory=list)

    def check(self, tool: str, args: dict,
              approve) -> str | None:
        v, grund = verdict(tool, args, bool(self.tainted_by),
                           self.secrets)
        if grund.endswith("fremdem Text"):
            grund += self._why()
        if v == "deny":
            return f"Taint-Policy: {grund}."
        if v == "allow":
            return super().check(tool, args, approve)
        if KLASSE[tool] == EXTERNAL or \
                self.risk(tool, args) not in NEEDS_OK:
            return self._gate(tool, args, approve, grund)

        def ask(r, t, a):               # Kap. 9 fragt, mit
            return approve(f"{r}, {grund}", t, a)  # Hinweis
        return super().check(tool, args, ask)

    def _gate(self, tool, args, approve, frage):
        key = "extern" if KLASSE[tool] == EXTERNAL else "fremd"
        self.asked[key] = self.asked.get(key, 0) + 1
        if self.mode == "eval" and KLASSE[tool] == WRITE:
            return None                 # Wegwerfkopie
        if self.mode != "interaktiv":
            return f"{tool}: im Modus {self.mode} gesperrt."
        if approve(frage, tool, args):
            return None
        return f"{tool}, {frage}: vom Menschen abgelehnt."

    def _why(self) -> str:
        quellen = ", ".join(self.tainted_by[-3:])
        return f" (fremd: {quellen})" if quellen else ""

    def observe(self, tool: str, args: dict, obs: str) -> str:
        """Nach jedem Tool: Taint merken, schwärzen, rahmen."""
        quellen = sources(tool, args, obs)
        fremd = [q for q in quellen
                 if not any(fnmatch(q, m) for m in EIGEN)]
        self.tainted_by += [q for q in fremd
                            if q not in self.tainted_by]
        text = redact(obs, self.secrets)
        if not quellen:
            return text
        return wrap(text, ", ".join(quellen), not fremd)
