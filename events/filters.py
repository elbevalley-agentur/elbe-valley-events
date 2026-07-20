"""Filter: vergangene Termine raus, Zeithorizont begrenzen, Region optional.

Umfang laut Vorgabe: 'moeglichst alles aus der Region' -> es wird nicht nach
Kategorie gefiltert, nur nach Zeit und (optional) Region.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from .model import Event


def filter_events(
    events: List[Event],
    months_ahead: int = 12,
    drop_past: bool = True,
    allowed_regions: Optional[List[str]] = None,
) -> List[Event]:
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    horizon = now + timedelta(days=30 * months_ahead)
    out: List[Event] = []
    for ev in events:
        end = ev.end or ev.start
        if drop_past and end < today:
            continue
        if ev.start > horizon:
            continue
        if allowed_regions and ev.region and ev.region not in allowed_regions:
            continue
        out.append(ev)
    return out
