"""Ein leerer String ist keine Antwort, sondern ein Fehler."""

LEER = ("FEHLER [leer]: Werkzeug lieferte keine Ausgabe. "
        "Das heißt nicht, dass nichts da ist. Erneut "
        "versuchen oder anders prüfen.")


def guard(obs) -> str:
    if obs is None or not str(obs).strip():
        return LEER
    return str(obs)
