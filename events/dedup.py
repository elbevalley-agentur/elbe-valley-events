"""Entdopplung - regionsuebergreifend.

Dieselbe Veranstaltung taucht oft in mehreren Quellen auf (gerade an den
Landesgrenzen, z.B. Doemitz zwischen Wendland und Ludwigslust-Parchim).

Zwei Termine gelten nur dann als Dublette, wenn ALLE gelten:
- gleicher Kalendertag,
- aehnlicher Titel (Fuzzy-Match),
- vereinbarer Ort (gleiche PLZ / gleicher Ort / hohe Ortsaehnlichkeit; ist ein
  Ort unbekannt, wird eine Zusammenlegung erlaubt und der Ort ergaenzt).

Wichtig: Gleicher Titel am gleichen Tag in VERSCHIEDENEN Orten (z.B. zwei
"Sommerfest" in verschiedenen Doerfern) wird NICHT zusammengelegt.

Der erste Treffer (nach Eingangs-/Quellenreihenfolge) bleibt erhalten und wird
aus der Dublette mit fehlenden Feldern angereichert.
"""
from __future__ import annotations

import re
from typing import List

from rapidfuzz import fuzz

from .model import Event, normalize_text

_ENRICH_ATTRS = ("end", "location", "description", "url", "image", "category")
_ZIP_RE = re.compile(r"\b(\d{5})\b")


def _zip(text: str) -> str:
    m = _ZIP_RE.search(text or "")
    return m.group(1) if m else ""


def _locations_compatible(a: str, b: str, threshold: int = 72) -> bool:
    na, nb = normalize_text(a), normalize_text(b)
    if not na or not nb:
        return True  # ein Ort unbekannt -> Zusammenlegung erlaubt (Anreicherung)
    if na == nb:
        return True
    za, zb = _zip(a), _zip(b)
    if za and zb:
        return za == zb  # beide PLZ vorhanden -> muessen uebereinstimmen
    if na in nb or nb in na:
        return True
    return fuzz.token_set_ratio(na, nb) >= threshold


def _enrich(base: Event, other: Event) -> None:
    for attr in _ENRICH_ATTRS:
        if not getattr(base, attr) and getattr(other, attr):
            setattr(base, attr, getattr(other, attr))


def deduplicate(events: List[Event], title_threshold: int = 85) -> List[Event]:
    kept: List[Event] = []
    for ev in events:
        match = None
        for k in kept:
            if k.start.date() != ev.start.date():
                continue
            if fuzz.token_set_ratio(normalize_text(k.title), normalize_text(ev.title)) < title_threshold:
                continue
            if not _locations_compatible(k.location, ev.location):
                continue
            match = k
            break
        if match is None:
            kept.append(ev)
        else:
            _enrich(match, ev)
            # Quellenherkunft transparent halten
            if other := ev.source:
                if other not in (match.source or ""):
                    match.source = f"{match.source}+{other}" if match.source else other
    return kept
