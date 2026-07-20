"""Quelle Altmark - freier HTML-Abruf von altmark.de/veranstaltungen.

altmark.de (TYPO3, Extension altmark_oa_events) rendert die Termine serverseitig;
sie stehen also direkt im HTML. Kein Zugang, kein Headless-Browser noetig.
Jeder Eintrag (.event-item) liefert Titel, Datum, Ort, Teaser, Art (Tag) und
Detail-Link.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup

from ..model import Event
from .base import BaseSource

_DATE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
_SKIP_TAGS = {"dauerveranstaltung", "langzeit"}


class AltmarkSource(BaseSource):
    name = "altmark"
    region = "Altmark"
    base_url = "https://www.altmark.de"
    urls = ["https://www.altmark.de/veranstaltungen"]

    def parse(self, raw: str) -> List[Event]:
        soup = BeautifulSoup(raw, "lxml")
        events: List[Event] = []
        seen: set[tuple[str, str]] = set()

        for item in soup.select(".event-item"):
            anchor = item.select_one("h3.title a") or item.select_one(".title a") or item.select_one("a")
            if not anchor:
                continue
            title = anchor.get_text(strip=True)
            href = anchor.get("href", "")
            if not title:
                continue

            date_el = item.select_one(".date")
            dates = _DATE.findall(date_el.get_text(" ", strip=True)) if date_el else []
            if not dates:
                continue
            d, m, y = (int(x) for x in dates[0])
            start = datetime(y, m, d)
            end = None
            if len(dates) > 1:
                d2, m2, y2 = (int(x) for x in dates[1])
                end = datetime(y2, m2, d2, 23, 59)

            loc_el = item.select_one(".location span") or item.select_one(".location")
            location = loc_el.get_text(" ", strip=True) if loc_el else ""
            teaser_el = item.select_one(".teaser")
            description = teaser_el.get_text(" ", strip=True) if teaser_el else ""

            category = ""
            for tag in item.select(".tags .tag"):
                text = tag.get_text(strip=True)
                if text and text.lower() not in _SKIP_TAGS:
                    category = text
                    break

            url = href if href.startswith("http") else self.base_url + href
            key = (title, start.isoformat())
            if key in seen:
                continue
            seen.add(key)

            events.append(
                Event(
                    title=title,
                    start=start,
                    end=end,
                    location=location,
                    description=description,
                    url=url,
                    category=category,
                    region=self.region,
                    source=self.name,
                )
            )
        return events
