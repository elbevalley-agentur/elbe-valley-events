"""Erzeugt eine valide iCalendar-Datei (.ics) aus Event-Objekten.

Die Ausgabe ist mit 'The Events Calendar' (WordPress) und gaengigen
Kalendern kompatibel. Zeitzone: Europe/Berlin.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from icalendar import Calendar
from icalendar import Event as IcsEvent

from .model import Event

TZ = ZoneInfo("Europe/Berlin")


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=TZ)


def build_calendar(events: List[Event], name: str = "Elbe Valley Veranstaltungen") -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//Elbe Valley Agentur//Veranstaltungs-Automatik//DE")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", name)
    cal.add("x-wr-timezone", "Europe/Berlin")

    stamp = datetime.now(TZ)
    for ev in events:
        start = _aware(ev.start)
        end = _aware(ev.end) if ev.end else start
        if end <= start:
            end = start + timedelta(hours=1)

        ie = IcsEvent()
        ie.add("uid", ev.uid)
        ie.add("summary", ev.title)
        ie.add("dtstart", start)
        ie.add("dtend", end)
        ie.add("dtstamp", stamp)
        if ev.location:
            ie.add("location", ev.location)

        desc_parts = []
        if ev.description:
            desc_parts.append(ev.description)
        if ev.url:
            desc_parts.append(ev.url)
        if ev.source:
            desc_parts.append(f"Quelle: {ev.source}")
        if desc_parts:
            ie.add("description", "\n\n".join(desc_parts))

        if ev.url:
            ie.add("url", ev.url)
        # Kategorien = Region + Art (fuer die Filter im Kalender)
        cats = []
        for c in (ev.region, ev.category):
            c = (c or "").strip()
            if c and c not in cats:
                cats.append(c)
        if cats:
            ie.add("categories", cats)
        cal.add_component(ie)
    return cal


def write_ics(events: List[Event], path: str, name: str = "Elbe Valley Veranstaltungen") -> str:
    cal = build_calendar(events, name)
    with open(path, "wb") as fh:
        fh.write(cal.to_ical())
    return path
