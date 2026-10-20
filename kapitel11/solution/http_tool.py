"""Ein Netzwerk-Tool. Wer GET für lesend hält, irrt."""
import urllib.request
from urllib.parse import urlparse


def http_get(deps, url: str) -> str:
    """Lädt eine Webseite als Text, höchstens 2.000 Zeichen."""
    if urlparse(url).scheme != "https":
        raise ValueError("Nur https-Adressen.")
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.read(2000).decode("utf-8", "replace")
