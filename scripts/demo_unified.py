#!/usr/bin/env python3
"""Demo: alle Quellen zu EINER Datei zusammenfuehren (offline, aus Beispieldaten).

Zeigt die Zusammenfuehrung ueber alle vier Regionen inkl.
- Grenzort-Dublette (dieselbe Veranstaltung in zwei Quellen -> zusammengelegt),
- Gegenprobe (gleicher Titel, anderer Ort -> bleibt getrennt).

Im Livebetrieb liefert scripts/build.py dasselbe Ergebnis aus echten Quellen.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from events.dedup import deduplicate  # noqa: E402
from events.filters import filter_events  # noqa: E402
from events.ics import write_ics  # noqa: E402
from events.model import Event  # noqa: E402
from events.sources.et4 import Et4Source  # noqa: E402
from events.sources.lup import LupSource  # noqa: E402
from events.sources.wendland import WendlandSource  # noqa: E402

SAMPLES = os.path.join(ROOT, "tests", "sample_data")


def _load(name):
    with open(os.path.join(SAMPLES, name), encoding="utf-8") as fh:
        return fh.read()


def main():
    events = []
    events += WendlandSource().parse(_load("wendland_sample.html"))
    events += LupSource().parse(_load("lup_sample.html"))
    events += Et4Source().parse(_load("et4_sample.json"))

    # Grenzort-Dublette: dieselbe Lesung wie in Wendland, aber aus LUP gemeldet
    events.append(Event(
        title="Lesung & Gespräch: Abschiedsbriefe zwischen Helmuth James und Freya von Moltke",
        start=datetime(2026, 7, 20, 19, 0),
        location="19303 Dömitz",
        region="Ludwigslust-Parchim",
        source="kultur-lup",
        description="Ergänzte Beschreibung aus der LUP-Quelle.",
    ))
    # Gegenprobe: gleicher Titel, gleicher Tag, verschiedene Orte -> beide behalten
    events.append(Event("Sommerfest", datetime(2026, 8, 15, 15, 0), location="Salzwedel",
                        region="Altmark", source="altmark-saint"))
    events.append(Event("Sommerfest", datetime(2026, 8, 15, 15, 0), location="Perleberg",
                        region="Prignitz", source="prignitz"))

    raw = len(events)
    # Fuer die Demo Vergangenes NICHT verwerfen (Beispieldaten liegen teils in 2024/25).
    filtered = filter_events(events, months_ahead=36, drop_past=False)
    deduped = deduplicate(filtered)
    deduped.sort(key=lambda e: (e.start, e.title))

    out = os.path.join(ROOT, "elbe-valley-events.ics")
    write_ics(deduped, out, name="Elbe Valley Veranstaltungen")

    print(f"Roh-Termine (alle Quellen): {raw}")
    print(f"Nach Entdopplung:           {len(deduped)}")
    print("Verteilung nach Region:", dict(Counter(e.region for e in deduped)))
    print()
    doemitz = next((e for e in deduped if e.title.startswith("Lesung & Gespräch")), None)
    if doemitz:
        print(f"Grenzort-Dublette zusammengefuehrt -> Quelle: {doemitz.source}")
    sommerfeste = [e for e in deduped if e.title == "Sommerfest"]
    print(f"'Sommerfest' getrennt gehalten: {len(sommerfeste)} Eintraege "
          f"({', '.join(e.location for e in sommerfeste)})")
    print(f"\nGeschrieben: {out}")


if __name__ == "__main__":
    main()
