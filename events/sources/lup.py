"""Quelle Ludwigslust-Parchim - kultur-lup.de/veranstaltungen (Kunst- & Kulturrat).

Statisches WordPress-HTML. Strategie:
1. Wenn strukturierte Daten (JSON-LD) vorhanden sind, diese nutzen.
2. Sonst die Auflistung parsen: jede Veranstaltung hat eine Ueberschrift mit
   Link auf /veranstaltungen/veranstaltung/... , unmittelbar davor steht eine
   Meta-Zeile mit Datum (und ggf. Uhrzeit / Ort).

Die naechste Datumszeile vor einer Ueberschrift gehoert zuverlaessig zu
genau dieser Veranstaltung (Dokumentreihenfolge: Datum -> Titel).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from ..jsonld import extract_events as extract_jsonld
from ..model import Event
from .base import BaseSource

_VER_HREF = re.compile(r"/veranstaltungen/veranstaltung/")
_DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
_TIME_RANGE_RE = re.compile(r"(\d{1,2})(?:[:.](\d{2}))?\s*-\s*(\d{1,2})(?:[:.](\d{2}))?\s*Uhr")
_TIME_SINGLE_RE = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")


def _int(v: Optional[str], default: int = 0) -> int:
    return int(v) if v else default


def _parse_meta(meta: str) -> Optional[dict]:
    dates = _DATE_RE.findall(meta)
    if not dates:
        return None
    d, m, y = (int(x) for x in dates[0])
    start_date = (y, m, d)
    end_date = None
    if len(dates) > 1:
        d2, m2, y2 = (int(x) for x in dates[1])
        end_date = (y2, m2, d2)

    meta_wo_dates = _DATE_RE.sub("", meta)
    sh = sm = 0
    eh = em = None
    rng = _TIME_RANGE_RE.search(meta_wo_dates)
    if rng:
        sh, sm = _int(rng.group(1)), _int(rng.group(2))
        eh, em = _int(rng.group(3)), _int(rng.group(4))
    else:
        single = _TIME_SINGLE_RE.search(meta_wo_dates)
        if single:
            sh, sm = _int(single.group(1)), _int(single.group(2))

    start = datetime(start_date[0], start_date[1], start_date[2], sh, sm)
    if end_date and eh is not None:
        end = datetime(end_date[0], end_date[1], end_date[2], eh, em or 0)
    elif end_date:
        end = datetime(end_date[0], end_date[1], end_date[2], 23, 59)
    elif eh is not None:
        end = datetime(start_date[0], start_date[1], start_date[2], eh, em or 0)
    else:
        end = None

    # Ort: Kommateile ohne Datum/Zeit
    place_parts = []
    for part in meta.split(","):
        p = part.strip()
        if not p or _DATE_RE.search(p) or "Uhr" in p:
            continue
        if _TIME_SINGLE_RE.fullmatch(p):
            continue
        if p.lower().startswith("bis"):
            continue
        place_parts.append(p)
    return {"start": start, "end": end, "location": ", ".join(place_parts)}


class LupSource(BaseSource):
    name = "kultur-lup"
    region = "Ludwigslust-Parchim"
    base_url = "https://www.kultur-lup.de"
    urls = ["https://www.kultur-lup.de/veranstaltungen"]

    def parse(self, raw: str) -> List[Event]:
        jsonld = extract_jsonld(raw, region=self.region, source=self.name)
        if jsonld:
            return jsonld
        return self._parse_listing(raw)

    def _parse_listing(self, raw: str) -> List[Event]:
        soup = BeautifulSoup(raw, "lxml")
        events: List[Event] = []
        seen: set[str] = set()

        for heading in soup.find_all(["h2", "h3", "h4"]):
            anchor = heading.find("a", href=_VER_HREF)
            if not anchor:
                continue
            title = anchor.get_text(strip=True)
            href = anchor.get("href", "")
            if not title or not href:
                continue

            date_node = heading.find_previous(string=_DATE_RE)
            if not date_node:
                continue
            # Sicherstellen, dass die Datumszeile zu genau dieser Ueberschrift gehoert
            next_heading = date_node.find_next(
                lambda t: getattr(t, "name", None) in ("h2", "h3", "h4")
                and t.find("a", href=_VER_HREF)
            )
            if next_heading is not heading:
                continue

            parsed = _parse_meta(str(date_node).strip())
            if not parsed:
                continue

            url = href if href.startswith("http") else self.base_url + href
            if url in seen:
                continue
            seen.add(url)

            events.append(
                Event(
                    title=title,
                    start=parsed["start"],
                    end=parsed["end"],
                    location=parsed["location"],
                    url=url,
                    region=self.region,
                    source=self.name,
                )
            )
        return events
