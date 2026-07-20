#!/usr/bin/env python3
"""Einstiegspunkt: alle konfigurierten Quellen abrufen und eine .ics erzeugen.

Beispiel:
    python scripts/build.py --output elbe-valley-events.ics

Aktive Quellen haengen von der Konfiguration ab (config.py / ENV):
- Wendland und Ludwigslust-Parchim laufen ohne Zugangsdaten.
- Altmark wird aktiv, sobald ALTMARK_ET4_EXPERIENCE gesetzt ist.
- Prignitz wird aktiv, sobald ENABLE_PRIGNITZ_HEADLESS=1 gesetzt ist.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from events.pipeline import run  # noqa: E402
from events.sources.lup import LupSource  # noqa: E402
from events.sources.wendland import WendlandSource  # noqa: E402


def build_sources():
    sources = [WendlandSource(), LupSource()]

    if config.ALTMARK_ET4_EXPERIENCE:
        from events.sources.altmark import AltmarkSource

        sources.append(
            AltmarkSource(
                experience=config.ALTMARK_ET4_EXPERIENCE,
                licensekey=config.ALTMARK_ET4_LICENSEKEY,
                q=config.ALTMARK_ET4_QUERY,
                months_ahead=config.MONTHS_AHEAD,
            )
        )

    if config.ENABLE_PRIGNITZ_HEADLESS:
        from events.sources.prignitz import PrignitzSource

        sources.append(PrignitzSource())

    return sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Elbe Valley Veranstaltungs-Automatik")
    parser.add_argument("--output", default=config.OUTPUT_PATH)
    parser.add_argument("--months-ahead", type=int, default=config.MONTHS_AHEAD)
    args = parser.parse_args()

    result = run(build_sources(), args.output, months_ahead=args.months_ahead)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
