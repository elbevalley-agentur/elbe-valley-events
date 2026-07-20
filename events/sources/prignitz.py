"""Quelle Prignitz - freie TMB-XML-Datei.

Die Prignitz-Portalseite veroeffentlicht die offiziellen TMB-Brandenburg-Termine
als statische XML unter dieprignitz.de/tmb/data/TMBEvents.xml. Kein Zugang noetig.
Wir filtern auf die Region 'Prignitz' (der Feed enthaelt auch Nachbarregionen).
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree as ET

from ..model import Event
from .base import DEFAULT_HEADERS, BaseSource

FEED_URL = "https://dieprignitz.de/tmb/data/TMBEvents.xml"


def _txt(node, tag: str) -> str:
    el = node.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""


def _dt(date_s: str, time_s: str) -> Optional[datetime]:
    if not date_s:
        return None
    try:
        d = datetime.strptime(date_s, "%Y-%m-%d")
    except ValueError:
        return None
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = datetime.strptime(time_s, fmt)
            return d.replace(hour=t.hour, minute=t.minute)
        except ValueError:
            continue
    return d


class PrignitzSource(BaseSource):
    name = "prignitz-tmb"
    region = "Prignitz"
    urls = [FEED_URL]
    region_filter = "Prignitz"   # nur Termine dieser TMB-Region uebernehmen

    def fetch(self) -> List[str]:
        import requests

        resp = requests.get(FEED_URL, headers=DEFAULT_HEADERS, timeout=self.request_timeout)
        resp.raise_for_status()
        return [resp.text]

    def parse(self, raw: str) -> List[Event]:
        root = ET.fromstring(raw)
        events: List[Event] = []
        for ev in root.findall(".//EVENT"):
            if self.region_filter and _txt(ev, "REGION_NAME_D") != self.region_filter:
                continue
            if _txt(ev, "E_NONTOURISTIC") == "1":
                continue  # nicht-touristische Eintraege ausblenden
            title = _txt(ev, "E_TITEL")
            von_d = _txt(ev, "E_DATUM_VON")
            bis_d = _txt(ev, "E_DATUM_BIS")
            start = _dt(von_d, _txt(ev, "E_ZEIT_VON"))
            if not title or not start:
                continue
            end = _dt(bis_d, _txt(ev, "E_ZEIT_BIS")) if bis_d else None
            if end:
                if end < start and bis_d != von_d:
                    end = end.replace(hour=23, minute=59)
                elif end <= start:
                    end = None

            city = " ".join(x for x in [_txt(ev, "E_LOC_PLZ"), _txt(ev, "E_LOC_ORT")] if x)
            location = ", ".join(p for p in [_txt(ev, "E_LOC_NAME"), city] if p)

            events.append(
                Event(
                    title=title,
                    start=start,
                    end=end,
                    location=location,
                    description=_txt(ev, "E_BESCHREIBUNG"),
                    url=_txt(ev, "E_URL1"),
                    region=self.region,
                    source=self.name,
                )
            )
        return events
