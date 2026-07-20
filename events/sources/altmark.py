"""Quelle Altmark (Lkr. Stendal u.a.) ueber die offizielle Tourismus-Datenschnittstelle.

Sachsen-Anhalt betreibt die Open-Data-Plattform SAiNT auf Basis von
destination.one/ET4. Der Altmark-Datenpool wird darueber als Event-Feed
bereitgestellt. Vorteile gegenueber Scraping: rechtlich sauber, vollstaendig,
stabil, mit Serientermin-Aufloesung.

Benoetigt: Projektname ("experience") und ggf. "licensekey" - beim
Altmaerkischen Regionalmarketing- & Tourismusverband bzw. der IMG
Sachsen-Anhalt anzufordern (siehe ACCESS_REQUESTS.md). Beides wird ueber
Umgebungsvariablen gesetzt (siehe config.py), kein Hardcoding von Keys.
"""
from __future__ import annotations

from .et4 import Et4Source


class AltmarkSource(Et4Source):
    name = "altmark-saint"
    region = "Altmark"

    def __init__(self, experience: str, licensekey: str = "", q: str = "", months_ahead: int = 12):
        self.experience = experience
        self.licensekey = licensekey
        # Eingrenzung auf die Altmark innerhalb des Landes-Datenpools.
        # Exakter Filterausdruck wird beim ersten Live-Aufruf bestaetigt.
        self.q = q
        self.months_ahead = months_ahead
