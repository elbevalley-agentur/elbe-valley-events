# Elbe Valley Veranstaltungs-Automatik

Sammelt Kultur- und Regionalveranstaltungen aus dem Vierländereck automatisch
ein, führt sie zusammen (entdoppelt, gefiltert) und stellt sie als iCal-Datei
(.ics) bereit, die der Website-Kalender (The Events Calendar) automatisch importiert.

**Regionen:** Wendland (Lüchow-Dannenberg), Altmark (Stendal), Prignitz,
Ludwigslust-Parchim.

## Schnellstart
Die vollständige Einrichtung steht in **`ANLEITUNG.md`** (Schritt für Schritt,
ohne Programmierkenntnisse). Technische Details in **`DEPLOYMENT.md`**,
Datenzugänge in **`ACCESS_REQUESTS.md`**.

## Status der Quellen
| Region | Quelle | Weg | Status |
|---|---|---|---|
| Wendland | wendland-net.de | HTML-Parser | läuft ohne Zugang |
| Ludwigslust-Parchim | kultur-lup.de | HTML-Parser | läuft ohne Zugang |
| Altmark | SAiNT / ET4 (Sachsen-Anhalt) | offizielle API | Zugang anfragen |
| Prignitz | dieprignitz.de / TMB Brandenburg | Headless bzw. API | freischaltbar |

## Aufbau
```
events/            Kernlogik
  model.py         Event-Datenmodell + Zeitzonen-Normalisierung
  ics.py           iCalendar-Erzeugung
  dedup.py         regionsübergreifende Entdopplung (ortsbewusst)
  filters.py       Zeit-/Regionsfilter
  jsonld.py        schema.org/Event-Extraktor (wiederverwendbar)
  pipeline.py      Orchestrierung
  sources/         eine Datei je Quelle (wendland, lup, altmark/et4, prignitz/headless)
scripts/
  build.py         Einstiegspunkt (erzeugt die .ics)
  demo_unified.py  Offline-Demo der Zusammenführung
wordpress/
  eva-ics-importer.php   kostenloses WP-Plugin für den Auto-Import
.github/workflows/build.yml   tägliche Automatik (GitHub Actions)
web/index.html     Landing-Page für den Feed
tests/             Offline-Tests (python3 tests/run_tests.py)
```

## Lokal testen
```
pip install -r requirements.txt
python3 tests/run_tests.py     # alle Prüfungen
python3 scripts/demo_unified.py # Beispiel-.ics erzeugen
```

## Konfiguration (Umgebungsvariablen)
`ALTMARK_ET4_EXPERIENCE`, `ALTMARK_ET4_LICENSEKEY`, `ALTMARK_ET4_QUERY`,
`ENABLE_PRIGNITZ_HEADLESS=1`, `EVENTS_MONTHS_AHEAD`, `EVENTS_OUTPUT`.
Keine Zugangsdaten im Code – alles über ENV bzw. GitHub-Secrets.
