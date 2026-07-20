"""Basis fuer JavaScript-gerenderte Quellen.

Manche Portale liefern ihre Termine erst nach dem Ausfuehren von JavaScript.
fetch() rendert die Seite mit einem Headless-Browser (Playwright) und gibt
den fertigen HTML-Quelltext zurueck; parse() liest daraus die strukturierten
schema.org/Event-Daten (JSON-LD). Quellen ohne JSON-LD ueberschreiben parse().

Betrieb: 'pip install playwright' + 'playwright install chromium'. Der
Headless-Abruf laeuft in eurer Betriebsumgebung (nicht Teil der Offline-Tests).
"""
from __future__ import annotations

from typing import List, Optional

from ..jsonld import extract_events as extract_jsonld
from ..model import Event
from .base import DEFAULT_HEADERS, BaseSource


class HeadlessSource(BaseSource):
    name = "headless"
    region = ""
    wait_selector: Optional[str] = None
    nav_timeout_ms: int = 60000

    def fetch(self) -> List[str]:
        from playwright.sync_api import sync_playwright

        pages: List[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(user_agent=DEFAULT_HEADERS["User-Agent"])
            page = context.new_page()
            for url in self.urls:
                page.goto(url, wait_until="networkidle", timeout=self.nav_timeout_ms)
                if self.wait_selector:
                    try:
                        page.wait_for_selector(self.wait_selector, timeout=15000)
                    except Exception:
                        pass
                pages.append(page.content())
            browser.close()
        return pages

    def parse(self, raw: str) -> List[Event]:
        return extract_jsonld(raw, region=self.region, source=self.name)
