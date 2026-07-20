#!/usr/bin/env python3
"""Offline-Tests: Datenmodell, Parser (Wendland), Dedup, ICS-Erzeugung.

Kein Netzzugriff - der Wendland-Parser wird gegen eine gespeicherte
Beispielseite getestet. So ist die Kernlogik verlaesslich pruefbar.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from events.dedup import deduplicate  # noqa: E402
from events.filters import filter_events  # noqa: E402
from events.ics import build_calendar, write_ics  # noqa: E402
from events.jsonld import extract_events as extract_jsonld  # noqa: E402
from events.model import Event  # noqa: E402
from events.sources.et4 import Et4Source  # noqa: E402
from events.sources.lup import LupSource  # noqa: E402
from events.sources.wendland import WendlandSource  # noqa: E402


def _load(name):
    with open(os.path.join(HERE, "sample_data", name), encoding="utf-8") as fh:
        return fh.read()

FAILS = []


def check(cond, msg):
    if cond:
        print(f"  ok   - {msg}")
    else:
        print(f"  FAIL - {msg}")
        FAILS.append(msg)


def test_wendland_parse():
    print("Test: Wendland-Parser")
    with open(os.path.join(HERE, "sample_data", "wendland_sample.html"), encoding="utf-8") as fh:
        raw = fh.read()
    events = WendlandSource().parse(raw)

    # 5 Bloecke, aber der Clubkino-Termin ist doppelt -> 4 eindeutige Events aus Parser
    check(len(events) == 4, f"4 eindeutige Termine erkannt (waren {len(events)})")

    by_title = {e.title: e for e in events}
    check("Rund um den Lübelner Mühlbachgraben" in by_title, "Umlaut-Titel korrekt dekodiert")

    lesung = by_title.get("Lesung & Gespräch: Abschiedsbriefe zwischen Helmuth James und Freya von Moltke")
    check(lesung is not None, "Titel mit '&' (%26) korrekt dekodiert")
    if lesung:
        check(lesung.start == datetime(2026, 7, 20, 19, 0), "Startzeit korrekt geparst")
        # gleiche Start=Ende im Feed -> auf +1h korrigiert
        check(lesung.end == datetime(2026, 7, 20, 20, 0), "Null-Dauer auf 1h korrigiert")
        check("Dömitz" in lesung.location, "Ort mit Umlaut korrekt")
        check(lesung.url.endswith("/event/1pj7j2gbvxtd"), "Detail-URL nachgezogen")

    muehlbach = by_title.get("Rund um den Lübelner Mühlbachgraben")
    if muehlbach:
        check(muehlbach.end == datetime(2026, 7, 20, 16, 0), "Endzeit aus Feed uebernommen")
    return events


def test_lup_parse():
    print("Test: LUP-Parser (kultur-lup.de)")
    events = LupSource().parse(_load("lup_sample.html"))
    check(len(events) == 4, f"4 Termine erkannt (waren {len(events)})")
    by_title = {e.title: e for e in events}

    konf = by_title.get("Landeskulturkonferenz am 02.12.2026 in Ludwigslust")
    check(konf is not None, "Naechste Veranstaltung erkannt")
    if konf:
        check(konf.start == datetime(2026, 12, 2, 0, 0), "Datum ohne Zeit korrekt")
        check(konf.location == "Ludwigslust", "Ort aus Meta-Zeile")
        check(konf.url.endswith("landeskulturkonferenz-am-02-12-2026-in-ludwigslust"), "Detail-URL absolut")

    netz = by_title.get("Kulturnetzwerktreffen LUP am 20.7.2025 | Kunstraum Dobbertin")
    if netz:
        check(netz.start == datetime(2025, 7, 20, 11, 0), "Startzeit aus Zeitspanne")
        check(netz.end == datetime(2025, 7, 20, 14, 0), "Endzeit aus Zeitspanne")
        check(netz.location == "Dobbertin", "Ort trotz Zeitspanne korrekt")

    lupinale = by_title.get("LUPINALE 2024")
    if lupinale:
        check(lupinale.start == datetime(2024, 5, 19, 0, 0), "Mehrtaegig: Startdatum")
        check(lupinale.end == datetime(2024, 9, 30, 23, 59), "Mehrtaegig: Enddatum ('bis ...')")
        check(lupinale.location == "Landkreis LUP", "Ort trotz Datumsbereich korrekt")


def test_jsonld():
    print("Test: JSON-LD-Extraktor")
    events = extract_jsonld(_load("jsonld_sample.html"), region="Altmark", source="altmark")
    check(len(events) == 1, f"Genau 1 Event aus @graph (Nicht-Event ignoriert) (waren {len(events)})")
    if events:
        ev = events[0]
        check(ev.title == "Tourismustag Altmark 2026", "Titel aus JSON-LD")
        check(ev.start == datetime(2026, 9, 15, 10, 0), "Startzeit (nach Zeitzonen-Normalisierung, Ortszeit)")
        check("Uchtspringe" in ev.location and "39599" in ev.location, "Ort inkl. Adresse zusammengesetzt")


def test_et4():
    print("Test: ET4/destination.one-Parser (Altmark-Route)")
    events = Et4Source().parse(_load("et4_sample.json"))
    check(len(events) == 1, f"1 Event aus ET4-Antwort (waren {len(events)})")
    if events:
        ev = events[0]
        check(ev.title == "Waldweihnacht auf Gut Mergenthau", "Titel aus ET4")
        check(ev.start == datetime(2026, 12, 5, 14, 0), "Startzeit aus timeInterval (Ortszeit)")
        check(ev.end == datetime(2026, 12, 5, 20, 0), "Endzeit aus timeInterval (Ortszeit)")
        check(ev.location == "Mergenthau 1, 86438 Kissing", "Adresse zusammengesetzt")
        check(ev.description.startswith("Waldweihnacht mit"), "Teaser als Beschreibung bevorzugt")
        check(ev.image.endswith("waldweihnacht.jpg"), "Bild-URL uebernommen")
        check(ev.category == "Brauchtum/Kultur", "Kategorie uebernommen")


def test_dedup(events):
    print("Test: Entdopplung")
    # Kuenstliche Dublette aus anderer Quelle: gleicher Tag, aehnlicher Titel
    dupe = Event(
        title="Clubkino im Culturladen",
        start=datetime(2026, 7, 22, 20, 0),
        location="Clenze",
        region="Wendland",
        source="andere-quelle",
        description="Beschreibung aus zweiter Quelle",
    )
    combined = events + [dupe]
    deduped = deduplicate(combined, title_threshold=80)
    check(len(deduped) == len(events), "Aehnlicher Titel am selben Tag als Dublette erkannt")
    club = next((e for e in deduped if e.title.startswith("Clubkino")), None)
    check(club is not None and club.description == "Beschreibung aus zweiter Quelle",
          "Fehlendes Feld aus Dublette angereichert")


def test_cross_region_dedup():
    print("Test: Regionsuebergreifende Entdopplung")
    day = datetime(2026, 8, 15, 19, 0)

    # Fall 1: gleiche Veranstaltung, zwei Quellen, gleicher Ort -> zusammenlegen
    a = Event("Orgelkonzert in der Kirche", day, location="19303 Dömitz", region="Wendland", source="wendland-net")
    b = Event("Orgelkonzert in der Kirche", day, location="Dömitz", region="Ludwigslust-Parchim",
              source="kultur-lup", description="Text aus LUP")
    merged = deduplicate([a, b])
    check(len(merged) == 1, "Grenzort-Dublette (2 Quellen, gleicher Ort) zusammengelegt")
    if merged:
        check(merged[0].description == "Text aus LUP", "Beschreibung aus zweiter Quelle ergaenzt")
        check("wendland-net" in merged[0].source and "kultur-lup" in merged[0].source,
              "Quellenherkunft beider Quellen vermerkt")

    # Fall 2: gleicher Titel, gleicher Tag, ANDERE Orte -> NICHT zusammenlegen
    c = Event("Sommerfest", day, location="Salzwedel", region="Altmark", source="altmark-saint")
    d = Event("Sommerfest", day, location="Perleberg", region="Prignitz", source="prignitz")
    kept = deduplicate([c, d])
    check(len(kept) == 2, "Gleicher Titel in verschiedenen Orten bleibt getrennt")

    # Fall 3: ein Ort unbekannt -> zusammenlegen und Ort ergaenzen
    e = Event("Lesung am Abend", day, location="", region="Wendland", source="wendland-net")
    f = Event("Lesung am Abend", day, location="Hitzacker", region="Wendland", source="andere")
    merged2 = deduplicate([e, f])
    check(len(merged2) == 1 and merged2[0].location == "Hitzacker", "Fehlender Ort wird ergaenzt")


def test_filter():
    print("Test: Filter (vergangene Termine)")
    past = Event(title="Alt", start=datetime(2020, 1, 1, 10, 0), region="Wendland")
    future = Event(title="Neu", start=datetime(2099, 1, 1, 10, 0), region="Wendland")
    near = Event(title="Bald", start=datetime(2026, 8, 1, 10, 0), region="Wendland")
    out = filter_events([past, future, near], months_ahead=12)
    titles = {e.title for e in out}
    check("Alt" not in titles, "Vergangener Termin entfernt")
    check("Neu" not in titles, "Termin jenseits des Horizonts entfernt")


def test_ics(events):
    print("Test: ICS-Erzeugung")
    cal = build_calendar(events)
    ical = cal.to_ical().decode("utf-8")
    check(ical.startswith("BEGIN:VCALENDAR"), "Gueltiger VCALENDAR-Kopf")
    check(ical.count("BEGIN:VEVENT") == len(events), "Ein VEVENT je Termin")
    check("SUMMARY:Clubkino" in ical, "Titel im VEVENT enthalten")
    check("UID:" in ical, "UID gesetzt")

    # Re-Parsen als Validitaetsnachweis
    from icalendar import Calendar
    reparsed = Calendar.from_ical(ical)
    vevents = [c for c in reparsed.walk() if c.name == "VEVENT"]
    check(len(vevents) == len(events), "ICS laesst sich wieder einlesen (valide)")

    out_path = os.path.join(ROOT, "wendland_demo.ics")
    write_ics(events, out_path)
    check(os.path.exists(out_path), f"Demo-Datei geschrieben: {out_path}")


def main():
    events = test_wendland_parse()
    test_lup_parse()
    test_jsonld()
    test_et4()
    test_dedup(events)
    test_cross_region_dedup()
    test_filter()
    test_ics(events)
    print()
    if FAILS:
        print(f"FEHLGESCHLAGEN: {len(FAILS)} Pruefung(en)")
        sys.exit(1)
    print("ALLE TESTS BESTANDEN")


if __name__ == "__main__":
    main()
