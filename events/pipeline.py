"""Orchestrierung: Quellen einsammeln -> filtern -> entdoppeln -> .ics schreiben."""
from __future__ import annotations

from typing import Iterable, List, Optional

from .dedup import deduplicate
from .filters import filter_events
from .ics import write_ics
from .model import Event


def collect_events(sources: Iterable) -> tuple[List[Event], dict]:
    all_events: List[Event] = []
    stats: dict = {}
    for src in sources:
        try:
            evs = src.collect()
        except Exception as exc:  # eine kaputte Quelle darf nicht alles stoppen
            stats[src.name] = f"FEHLER: {exc}"
            continue
        stats[src.name] = len(evs)
        all_events.extend(evs)
    return all_events, stats


def run(
    sources: Iterable,
    output_path: str,
    months_ahead: int = 12,
    allowed_regions: Optional[List[str]] = None,
    calendar_name: str = "Elbe Valley Veranstaltungen",
) -> dict:
    all_events, stats = collect_events(sources)
    filtered = filter_events(all_events, months_ahead=months_ahead, allowed_regions=allowed_regions)
    deduped = deduplicate(filtered)
    deduped.sort(key=lambda e: e.start)
    write_ics(deduped, output_path, name=calendar_name)
    return {
        "sources": stats,
        "total_raw": len(all_events),
        "after_filter": len(filtered),
        "after_dedup": len(deduped),
        "output": output_path,
    }
