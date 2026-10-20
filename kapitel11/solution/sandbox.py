"""Befehle im Container: kein Netz, Repository read-only,
kein Root, Zeitlimit, leere Umgebung plus Allowlist."""
import subprocess
import uuid
from pathlib import Path

DOCKER = "docker"
IMAGE = "python:3.12-slim"      # Beispiel; besser per Digest
TIMEOUT = 120                   # Sekunden, Beispielwert


def docker_args(repo: Path, work: Path, cmd: list[str],
                env: dict[str, str], name: str) -> list[str]:
    args = [DOCKER, "run", "--rm", "--name", name,
            "--network", "none",            # kein Netz
            "--read-only", "--tmpfs", "/tmp",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges=true",
            "--pids-limit", "128", "--memory", "1g",
            "--user", "1000:1000",          # kein Root
            "--mount", (f"type=bind,src={repo},dst=/repo,"
                        "readonly"),
            "--mount", f"type=bind,src={work},dst=/work",
            "--workdir", "/work"]
    for k, v in sorted(env.items()):    # nur die Allowlist
        args += ["--env", f"{k}={v}"]
    return [*args, IMAGE, *cmd]


def run(repo: Path, work: Path, cmd: list[str],
        env: dict[str, str], timeout: int = TIMEOUT):
    """(Exit-Code oder None, Ausgabe), wie run_capped()."""
    name = f"agent-{uuid.uuid4().hex[:12]}"
    try:
        p = subprocess.run(
            docker_args(repo, work, cmd, env, name),
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout,
            check=False)        # Exit-Code werten wir aus
    except subprocess.TimeoutExpired:   # Container läuft
        subprocess.run([DOCKER, "rm", "-f", name],  # sonst
                       capture_output=True, check=False)
        return None, f"Zeitlimit {timeout} s überschritten."
    return p.returncode, (p.stdout + p.stderr)[-4000:]


def docker_ready() -> bool:
    try:
        p = subprocess.run([DOCKER, "info"], timeout=30,
                           capture_output=True, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return p.returncode == 0
