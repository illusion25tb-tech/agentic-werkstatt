"""Provenienz- und Personendaten-Gate des K2C-Agenten."""
from pathlib import Path

from check_k2c import main, personal_data, provenance

DOC = "docs/paketfix/paketfix_api_v2.md"
GUT = f'''def anmelden(sendung: dict) -> dict:
    """Meldet eine Sendung an. Quelle: {DOC}:30-45"""
    return sendung
'''
OHNE = '''def etikett(nr: str) -> str:
    return nr
'''


def repo(tmp_path: Path, code: str) -> Path:
    doc = tmp_path / DOC
    doc.parent.mkdir(parents=True)
    doc.write_text("Zeile\n" * 60, encoding="utf-8")
    (tmp_path / "client.py").write_text(code, "utf-8")
    return tmp_path / "client.py"


def test_funktion_mit_quelle(tmp_path):
    assert provenance(repo(tmp_path, GUT), tmp_path) == []


def test_funktion_ohne_quelle(tmp_path):
    code = repo(tmp_path, GUT + "\n\n" + OHNE)
    assert provenance(code, tmp_path) == [
        "etikett: keine Quelle"]


def test_quelle_ausserhalb_des_dokuments(tmp_path):
    code = repo(tmp_path, GUT.replace("30-45", "58-70"))
    assert "gibt es nicht" in provenance(code, tmp_path)[0]


def test_fixture_nur_synthetisch(tmp_path):
    fx = tmp_path / "sendung.json"
    fx.write_text('{"name": "Erika Musterfrau", '
                  '"avis_email": "erika@paketfix.example"}',
                  encoding="utf-8")
    assert personal_data(fx) == []
    fx.write_text('{"name": "Jana Krüger", '
                  '"avis_email": "jana.k@web.de"}',
                  encoding="utf-8")
    assert personal_data(fx) == [
        "sendung.json: jana.k@web.de",
        "sendung.json: Jana Krüger"]


def test_exit_code(tmp_path):
    code = repo(tmp_path, OHNE)
    assert main(["--root", str(tmp_path), str(code)]) == 1
