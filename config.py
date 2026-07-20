"""Zentrale Konfiguration ueber Umgebungsvariablen.

Keine Zugangsdaten im Code - alles ueber ENV. So bleibt das Repo teilbar und
Keys landen nicht in der Versionsverwaltung.
"""
import os

# --- Altmark: offizielle SAiNT/ET4-Schnittstelle (Sachsen-Anhalt) ---
# Beim Tourismusverband anzufordern (siehe ACCESS_REQUESTS.md).
ALTMARK_ET4_EXPERIENCE = os.environ.get("ALTMARK_ET4_EXPERIENCE", "")
ALTMARK_ET4_LICENSEKEY = os.environ.get("ALTMARK_ET4_LICENSEKEY", "")
ALTMARK_ET4_QUERY = os.environ.get("ALTMARK_ET4_QUERY", "")  # optionaler Regionsfilter

# --- Prignitz: Headless-Rendering aktivieren (kein Zugang noetig) ---
ENABLE_PRIGNITZ_HEADLESS = os.environ.get("ENABLE_PRIGNITZ_HEADLESS", "") == "1"

# --- Allgemein ---
MONTHS_AHEAD = int(os.environ.get("EVENTS_MONTHS_AHEAD", "12"))
OUTPUT_PATH = os.environ.get("EVENTS_OUTPUT", "elbe-valley-events.ics")
