"""ET4 / destination.one meta-search - offizielle Tourismus-Datenschnittstelle.

Sachsen-Anhalt stellt seine Tourismusdaten (Plattform SAiNT) ueber die
destination.one/ET4 meta-Search-API bereit. Endpoint und Parameter sind
dokumentiert: http://meta.et4.de/rest.ashx/search/  (Template ET2014A.json).

Zugang: es werden der Projektname ("experience") und ggf. ein "licensekey"
benoetigt - beim Tourismusverband anzufordern (siehe ACCESS_REQUESTS.md).

Die Verarbeitung (parse) ist vollstaendig und getestet. Nur der konkrete
Projektname/Key ist noch einzutragen; die Feldnamen werden beim ersten
Live-Aufruf einmalig gegengeprueft.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from typing import List, Optional
from urllib.parse import urlencode

from ..jsonld import _parse_iso
from ..model import Event
from .base import DEFAULT_HEADERS, BaseSource

_ENDPOINT = "https://meta.et4.de/rest.ashx/search/ET2014A.json"


def _first(d: dict, *keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def _address_to_str(addr) -> str:
    if not isinstance(addr, dict):
        return ""
    street = _first(addr, "street", "streetAddress") or ""
    zip_ = _first(addr, "zip", "postalCode", "zipcode") or ""
    city = _first(addr, "city", "addressLocality", "town") or ""
    line2 = " ".join(p for p in (str(zip_), str(city)) if p).strip()
    return ", ".join(p for p in (str(street).strip(), line2) if p)


def _interval_dates(item: dict):
    intervals = item.get("timeIntervals") or item.get("timeintervals") or []
    if not intervals:
        return None, None
    first = intervals[0]
    start = _parse_iso(_first(first, "start", "begin", "tsFrom", "startDate"))
    end = _parse_iso(_first(first, "end", "tsTo", "endDate"))
    return start, end


class Et4Source(BaseSource):
    name = "et4"
    region = ""
    experience = ""          # Projekt-/Datenpool-Name (obligatorisch)
    licensekey = ""          # nur fuer nicht-oeffentliche Projekte
    q = ""                   # optionaler Query-Filter (z.B. Region eingrenzen)
    months_ahead = 12

    def build_url(self, start: str, end: str) -> str:
        params = {
            "experience": self.experience,
            "type": "Event",
            "mkt": "de-DE",
            "startdate": start,
            "enddate": end,
            "unrollIntervals": "true",   # Serientermine in Einzeltermine aufloesen
            "sort": "start asc",
            "limit": "1000",
        }
        if self.licensekey:
            params["licensekey"] = self.licensekey
        if self.q:
            params["q"] = self.q
        return f"{_ENDPOINT}?{urlencode(params)}"

    def fetch(self) -> List[str]:
        import requests

        start = date.today().isoformat()
        end = (date.today() + timedelta(days=30 * self.months_ahead)).isoformat()
        resp = requests.get(self.build_url(start, end), headers=DEFAULT_HEADERS, timeout=self.request_timeout)
        resp.raise_for_status()
        return [resp.text]

    def parse(self, raw: str) -> List[Event]:
        data = json.loads(raw)
        items = data.get("items") or data.get("Items") or []
        events: List[Event] = []
        for item in items:
            ev = self._map(item)
            if ev:
                events.append(ev)
        return events

    def _map(self, item: dict) -> Optional[Event]:
        title = (_first(item, "title", "name") or "").strip()
        start, end = _interval_dates(item)
        if not title or not start:
            return None

        # Beschreibung: teaser bevorzugt, sonst details
        description = ""
        texts = item.get("texts") or []
        if isinstance(texts, list):
            teaser = next((t.get("value") for t in texts if isinstance(t, dict) and t.get("rel") == "teaser"), None)
            details = next((t.get("value") for t in texts if isinstance(t, dict) and t.get("rel") == "details"), None)
            description = (teaser or details or "").strip()

        # Bild
        image = ""
        media = item.get("media_objects") or item.get("media") or []
        if isinstance(media, list) and media:
            image = _first(media[0], "url", "URL") or ""

        return Event(
            title=title,
            start=start,
            end=end,
            location=_address_to_str(item.get("address")),
            description=description,
            url=(_first(item, "url", "link", "global_id") or ""),
            category=(_first(item, "category") or ""),
            image=image or "",
            region=self.region,
            source=self.name,
        )
