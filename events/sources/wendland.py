"""Quelle Wendland (Lkr. Luechow-Dannenberg) - wendland-net.de/events.

Strategie: Jeder Termin traegt einen 'In Google Kalender uebertragen'-Link
(google.com/calendar/event?action=TEMPLATE...). Dessen Query-String enthaelt
Titel, Start/Ende und Ort sauber und stabil - unabhaengig vom umgebenden
HTML-Layout. Diese Links sind daher die verlaessliche Datengrundlage.
Ergaenzend werden Detail-Links (/event/...) fuer die URL nachgezogen.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import List
from urllib.parse import parse_qs, unquote_plus, urlparse

from bs4 import BeautifulSoup

from ..model import Event
from .base import BaseSource

_GCAL_RE = re.compile(r"https?://www\.google\.com/calendar/event\?[^\s\"'<>]+")


def _parse_dt(token: str) -> datetime:
    token = token.strip()
    if "T" in token:
        return datetime.strptime(token, "%Y%m%dT%H%M%S")
    return datetime.strptime(token, "%Y%m%d")


def _parse_gcal_dates(dates: str) -> tuple[datetime, datetime]:
    start_s, _, end_s = dates.partition("/")
    end_s = end_s or start_s
    start = _parse_dt(start_s)
    end = _parse_dt(end_s)
    if end <= start:
        end = start + timedelta(hours=1)
    return start, end


class WendlandSource(BaseSource):
    name = "wendland-net"
    region = "Wendland"
    base_url = "https://wendland-net.de"
    urls = [
        "https://wendland-net.de/events",
        "https://wendland-net.de/events?pn=1",
        "https://wendland-net.de/events?pn=2",
        "https://wendland-net.de/events?pn=3",
        "https://wendland-net.de/events?pn=4",
    ]

    def parse(self, raw: str) -> List[Event]:
        events: List[Event] = []
        seen: set[tuple[str, str]] = set()

        for match in _GCAL_RE.finditer(raw):
            url = match.group(0).replace("&amp;", "&")
            query = parse_qs(urlparse(url).query)
            title = unquote_plus(query.get("text", [""])[0]).strip()
            dates = query.get("dates", [""])[0]
            location = unquote_plus(query.get("location", [""])[0]).strip()
            if not title or not dates:
                continue
            try:
                start, end = _parse_gcal_dates(dates)
            except ValueError:
                continue
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
                    region=self.region,
                    source=self.name,
                )
            )

        self._enrich_detail_links(raw, events)
        return events

    def _enrich_detail_links(self, raw: str, events: List[Event]) -> None:
        """Detail-URL (/event/<id>) je Titel nachziehen, wenn moeglich."""
        try:
            soup = BeautifulSoup(raw, "lxml")
        except Exception:
            return
        by_title: dict[str, str] = {}
        for anchor in soup.select("a[href*='/event/']"):
            text = anchor.get_text(strip=True)
            href = anchor.get("href", "")
            if not text or not href:
                continue
            if href.startswith("/"):
                href = self.base_url + href
            by_title.setdefault(text, href)
        for ev in events:
            if not ev.url and ev.title in by_title:
                ev.url = by_title[ev.title]
