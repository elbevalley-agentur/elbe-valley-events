"""Quelle Prignitz (Brandenburg) - dieprignitz.de/veranstaltungskalender.

Der Kalender ist JavaScript-gerendert. Zwei Wege:

1. Sofort nutzbar (kein Partner-Zugang): Headless-Rendering + JSON-LD
   (diese Klasse). Falls die Seite keine JSON-LD-Daten liefert, wird parse()
   auf die DOM-Struktur umgestellt - das wird beim ersten Live-Render geprueft.

2. Empfohlene Produktionsloesung: die offizielle Veranstaltungsdatenbank der
   TMB (Contentnetzwerk Brandenburg, ~40.000 Termine/Jahr, filterbar nach
   Region). Zugang ueber die TMB anzufordern (siehe ACCESS_REQUESTS.md).
"""
from __future__ import annotations

from .headless import HeadlessSource


class PrignitzSource(HeadlessSource):
    name = "prignitz"
    region = "Prignitz"
    urls = ["https://dieprignitz.de/veranstaltungskalender"]
    wait_selector = "a[href*='veranstaltung'], .event, [class*='event']"
