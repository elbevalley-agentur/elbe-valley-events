"""Einheitliches Event-Datenmodell und Normalisierungshelfer.

Alle Quellen liefern ihre Termine in dieses Modell. So bleiben Entdopplung,
Filter und ICS-Erzeugung quellenunabhaengig.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("Europe/Berlin")


def _to_naive_local(dt: Optional[datetime]) -> Optional[datetime]:
    """Alle Zeiten einheitlich als naive Ortszeit (Europe/Berlin) speichern.

    So sind Vergleiche, Sortierung und Entdopplung quellenunabhaengig; die
    ICS-Erzeugung haengt die Zeitzone wieder an.
    """
    if dt is not None and dt.tzinfo is not None:
        return dt.astimezone(_TZ).replace(tzinfo=None)
    return dt


def normalize_text(text: str) -> str:
    """Klein, ohne Akzente, ohne Sonderzeichen - fuer Vergleiche/Schluessel."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return text


@dataclass
class Event:
    """Ein normalisierter Veranstaltungstermin."""

    title: str
    start: datetime
    end: Optional[datetime] = None
    location: str = ""
    description: str = ""
    url: str = ""
    category: str = ""
    region: str = ""
    source: str = ""
    image: str = ""

    @property
    def uid(self) -> str:
        """Stabile ID: gleiche Veranstaltung -> gleiche UID (wichtig fuer Re-Import)."""
        base = f"{normalize_text(self.title)}|{self.start.date().isoformat()}|{normalize_text(self.location)}"
        digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]
        return f"{digest}@elbevalley-agentur.de"

    def __post_init__(self) -> None:
        self.title = (self.title or "").strip()
        self.location = (self.location or "").strip()
        self.description = (self.description or "").strip()
        self.start = _to_naive_local(self.start)
        self.end = _to_naive_local(self.end)
