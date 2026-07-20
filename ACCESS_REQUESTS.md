# Zugangs-Checkliste: offizielle Datenschnittstellen

Wendland und Ludwigslust-Parchim laufen ohne Zugangsdaten (statische Quellen).
Für Altmark und Prignitz sind die offiziellen Tourismus-Datenschnittstellen der
sauberste Weg. Hier die konkreten Schritte.

## Altmark (Sachsen-Anhalt) - SAiNT / ET4 / destination.one

Sachsen-Anhalt stellt Veranstaltungen über die Open-Data-Plattform SAiNT
(Technik: destination.one/ET4) bereit.

Anzufragen bei: Investitions- und Marketinggesellschaft Sachsen-Anhalt (IMG) /
Tourismusnetzwerk Sachsen-Anhalt bzw. Altmärkischer Regionalmarketing- &
Tourismusverband.

Benötigt werden:
1. Der Projektname ("experience") des Altmark- bzw. Sachsen-Anhalt-Datenpools.
2. Falls nicht öffentlich: ein "licensekey".
3. Optional: der korrekte Query-/Regionsfilter, um auf die Altmark einzugrenzen.

Eintragen als Umgebungsvariablen (nicht im Code):
```
ALTMARK_ET4_EXPERIENCE=<projektname>
ALTMARK_ET4_LICENSEKEY=<key, falls nötig>
ALTMARK_ET4_QUERY=<optionaler Regionsfilter>
```
Danach ist die Quelle automatisch aktiv. Beim ersten Live-Aufruf einmal die
Feldnamen der Antwort gegen den Parser prüfen (Doku: help.destination.one).

## Prignitz (Brandenburg) - zwei Optionen

**Sofort nutzbar, ohne Zugang:** Headless-Rendering von dieprignitz.de aktivieren:
```
ENABLE_PRIGNITZ_HEADLESS=1
```
(Voraussetzung im Betrieb: `pip install playwright` + `playwright install chromium`.)

**Empfohlene Produktionslösung:** die offizielle Veranstaltungsdatenbank der
TMB Tourismus-Marketing Brandenburg (Contentnetzwerk Brandenburg, ~40.000
Termine/Jahr, filterbar nach Region). Zugang/Partner-ID bei der TMB anfragen.
Sobald die Schnittstellen-Spezifikation vorliegt, ergänzen wir analog zum
ET4-Connector ein TMB-Modul (kleiner Zusatzaufwand).

## Rechtlicher Hinweis
Offizielle Open-Data-Schnittstellen sind ausdrücklich zur Weiterverwendung
gedacht - der klar bevorzugte Weg gegenüber Scraping. Nutzungsbedingungen der
jeweiligen Plattform (Lizenz, Quellenangabe) beim Onboarding kurz prüfen.
