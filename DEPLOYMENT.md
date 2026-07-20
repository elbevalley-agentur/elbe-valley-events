# Deployment: Automatik & Website-Anbindung

Gewählter Weg: **GitHub Actions** erzeugt die `.ics` täglich und veröffentlicht sie
über **GitHub Pages**; WordPress zieht sie automatisch per **iCal-Auto-Import**.

## 1. Repository & Zeitplan (GitHub Actions)

1. Projektordner `elbe-valley-events/` in ein GitHub-Repository legen.
2. Unter **Settings → Pages**: Source = "GitHub Actions".
3. Der Workflow `.github/workflows/build.yml` läuft dann
   - täglich um 04:00 UTC,
   - bei jedem Push,
   - manuell über "Run workflow".
4. Ergebnis-URL (fester iCal-Feed):
   `https://<organisation>.github.io/<repo>/elbe-valley-events.ics`

### Optionale Quellen als Secrets/Variables hinterlegen
Unter **Settings → Secrets and variables → Actions**:

- Secret `ALTMARK_ET4_EXPERIENCE`, ggf. `ALTMARK_ET4_LICENSEKEY` → aktiviert Altmark.
- Variable `ALTMARK_ET4_QUERY` (optional) → Regionsfilter.
- Variable `ENABLE_PRIGNITZ_HEADLESS = 1` → aktiviert Prignitz (Headless).

Ohne diese laufen automatisch **Wendland** und **Ludwigslust-Parchim**.

## 2. WordPress-Anbindung (iCal-Auto-Import)

Zwei Möglichkeiten – eine genügt:

### A) Kostenlos: mitgeliefertes Mini-Plugin (empfohlen)
1. Datei `wordpress/eva-ics-importer.php` nach
   `wp-content/mu-plugins/` kopieren (oder als normales Plugin aktivieren).
2. In `wp-config.php` die Feed-URL setzen:
   ```php
   define('EVA_ICS_FEED_URL', 'https://<organisation>.github.io/<repo>/elbe-valley-events.ics');
   ```
3. Fertig. Der Import läuft täglich via WP-Cron. Termine werden über ihre UID
   erkannt und aktualisiert statt doppelt angelegt.
   Manueller Testlauf (als Admin eingeloggt): `https://euredomain.de/?eva_ics_import=1`

### B) No-Code: The Events Calendar "Event Aggregator" (kostenpflichtiges Add-on)
Falls vorhanden: unter Veranstaltungen → Importe eine neue **iCal**-Importquelle
anlegen, die obige Feed-URL eintragen, Zeitplan "täglich" wählen. Kein Code nötig.

## 3. Kontrolle
- `…/last-build.txt` zeigt den Zeitpunkt des letzten erfolgreichen Builds.
- Der Actions-Lauf gibt eine Statistik aus (Termine je Quelle, nach Filter/Dedup).

## Datenfluss
```
GitHub Actions (täglich)
  → scripts/build.py  (Quellen abrufen, filtern, entdoppeln)
  → public/elbe-valley-events.ics
  → GitHub Pages (feste URL)
      → WordPress (Mini-Plugin oder Event Aggregator, täglich)
          → The Events Calendar  → Veranstaltungsseite
```
