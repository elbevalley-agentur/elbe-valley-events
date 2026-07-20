"""Basisklasse fuer alle Quellen.

Wichtig: fetch() (Netzzugriff) ist bewusst von parse() (reine Logik) getrennt.
So laesst sich das Parsen offline gegen gespeicherte Beispieldaten testen,
waehrend der Live-Abruf spaeter in eurer Betriebsumgebung stattfindet.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..model import Event

DEFAULT_HEADERS = {
    "User-Agent": (
        "ElbeValleyEventsBot/1.0 "
        "(+https://elbevalley-agentur.de; kontakt@elbevalley-agentur.de)"
    ),
    "Accept-Language": "de-DE,de;q=0.9",
}


class BaseSource(ABC):
    name: str = "base"
    region: str = ""
    urls: List[str] = []
    request_timeout: int = 30

    @abstractmethod
    def parse(self, raw: str) -> List[Event]:
        """Rohinhalt einer Seite -> Liste von Events. Rein, kein Netz."""
        raise NotImplementedError

    def fetch(self) -> List[str]:
        """Alle konfigurierten URLs abrufen (Netzzugriff, Betriebsumgebung)."""
        import requests  # lokal importiert, damit Tests ohne requests laufen

        pages: List[str] = []
        for url in self.urls:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=self.request_timeout)
            resp.raise_for_status()
            pages.append(resp.text)
        return pages

    def collect(self) -> List[Event]:
        events: List[Event] = []
        for raw in self.fetch():
            events.extend(self.parse(raw))
        return events
