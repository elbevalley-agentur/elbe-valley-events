#!/usr/bin/env python3
"""Einstiegspunkt: alle Quellen abrufen und eine .ics erzeugen.

Alle vier Regionen laufen ohne Zugangsdaten:
- Wendland            -> wendland-net.de (HTML)
- Ludwigslust-Parchim -> kultur-lup.de (HTML)
- Altmark             -> altmark.de (HTML, serverseitig gerendert)
- Prignitz            -> dieprignitz.de/tmb/data/TMBEvents.xml (freie XML)

Beispiel:
    python scripts/build.py --output elbe-valley-events.ics
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from events.pipeline import run  # noqa: E402
from events.sources.altmark import AltmarkSource  # noqa: E402
from events.sources.lup import LupSource  # noqa: E402
from events.sources.prignitz import PrignitzSource  # noqa: E402
from events.sources.wendland import WendlandSource  # noqa: E402

SOURCES = [
    WendlandSource(),
    LupSource(),
    AltmarkSource(),
    PrignitzSource(),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Elbe Valley Veranstaltungs-Automatik")
    parser.add_argument("--output", default=config.OUTPUT_PATH)
    parser.add_argument("--months-ahead", type=int, default=config.MONTHS_AHEAD)
    args = parser.parse_args()

    result = run(SOURCES, args.output, months_ahead=args.months_ahead)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
