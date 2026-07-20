"""Generischer schema.org/Event-Extraktor.

Viele Veranstaltungsseiten (WordPress-Plugins, TYPO3, Tourismus-Systeme)
betten strukturierte Daten als <script type="application/ld+json"> ein.
Dieser Extraktor liest daraus Events aus - eine Strategie, die quellenueber-
greifend funktioniert und robust gegen Layout-Aenderungen ist.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from typing import Iterator, List

from .model import Event

_SCRIPT_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _parse_iso(value) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    s = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[: len(fmt) + 2], fmt)
        except ValueError:
            continue
    return None


def _location_str(loc) -> str:
    if not loc:
        return ""
    if isinstance(loc, str):
        return loc.strip()
    if isinstance(loc, list):
        return _location_str(loc[0]) if loc else ""
    if isinstance(loc, dict):
        name = (loc.get("name") or "").strip()
        addr = loc.get("address", "")
        if isinstance(addr, dict):
            parts = [
                addr.get("streetAddress", ""),
                addr.get("postalCode", ""),
                addr.get("addressLocality", ""),
            ]
            addr = " ".join(p for p in parts if p)
        addr = (addr or "").strip() if isinstance(addr, str) else ""
        return ", ".join(p for p in (name, addr) if p)
    return ""


def _is_event(node: dict) -> bool:
    t = node.get("@type", "")
    types = t if isinstance(t, list) else [t]
    return any("Event" in str(x) for x in types)


def _walk(obj) -> Iterator[dict]:
    if isinstance(obj, list):
        for item in obj:
            yield from _walk(item)
    elif isinstance(obj, dict):
        if _is_event(obj):
            yield obj
        for value in obj.values():
            if isinstance(value, (list, dict)):
                yield from _walk(value)


def extract_events(raw: str, region: str = "", source: str = "") -> List[Event]:
    events: List[Event] = []
    seen: set[tuple[str, str]] = set()
    for match in _SCRIPT_RE.finditer(raw):
        block = unescape(match.group(1).strip())
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        for node in _walk(data):
            name = (node.get("name") or "").strip()
            start = _parse_iso(node.get("startDate"))
            if not name or not start:
                continue
            key = (name, start.isoformat())
            if key in seen:
                continue
            seen.add(key)
            events.append(
                Event(
                    title=name,
                    start=start,
                    end=_parse_iso(node.get("endDate")),
                    location=_location_str(node.get("location")),
                    description=(node.get("description") or "").strip(),
                    url=(node.get("url") or "") if isinstance(node.get("url"), str) else "",
                    region=region,
                    source=source,
                )
            )
    return events
