# Inbetriebnahme – Schritt für Schritt

Diese Anleitung führt dich komplett durch. Du brauchst kein Programmierwissen,
aber für den WordPress-Teil ist Zugang zum Adminbereich eurer Website nötig
(ggf. mit eurer Web-/Hosting-Person zusammen). Zeitaufwand: ca. 30–45 Minuten.

Ergebnis: Der Kalender aktualisiert sich danach **täglich von allein**.

---

## Überblick: 3 Bausteine

1. **GitHub** – erzeugt die Termindatei automatisch jeden Tag und stellt sie unter
   einer festen Internet-Adresse bereit.
2. **WordPress** – holt sich diese Datei automatisch und zeigt die Termine auf
   eurer Veranstaltungsseite.
3. **Optional später** – zwei offizielle Datenzugänge für Altmark und Prignitz.

Ohne den optionalen Teil laufen sofort **Wendland** und **Ludwigslust-Parchim**.

---

## Teil 1 – GitHub einrichten (die tägliche Automatik)

1. **Konto anlegen** (falls nicht vorhanden): github.com → kostenlos registrieren.
2. **Neues Repository erstellen**: oben rechts „+" → „New repository".
   - Name z.B. `elbe-valley-events`
   - Sichtbarkeit **Public** (nötig, damit die kostenlose Veröffentlichung klappt;
     es sind keine Passwörter im Projekt – die liegen getrennt als „Secrets").
   - „Create repository".
3. **Projektdateien hochladen**: auf der Repo-Seite „uploading an existing file".
   Ziehe den **gesamten Inhalt** des Ordners `elbe-valley-events` hinein
   (inkl. der Unterordner). „Commit changes".
   - Tipp: Falls der versteckte Ordner `.github` beim Hochladen fehlt, lade ihn
     separat nach – er enthält die Automatik. (Alternativ GitHub Desktop nutzen.)
4. **Seiten-Veröffentlichung einschalten**: Reiter **Settings → Pages** →
   unter „Source" **GitHub Actions** auswählen.
5. **Automatik zum ersten Mal starten**: Reiter **Actions** → ggf. Workflows
   aktivieren → „Build & Publish Events ICS" auswählen → „Run workflow".
6. Nach ~1–2 Minuten ist die Termindatei online unter:
   ```
   https://<dein-github-name>.github.io/elbe-valley-events/elbe-valley-events.ics
   ```
   Diese Adresse merken – sie kommt gleich in WordPress.

> Ab jetzt baut GitHub die Datei jede Nacht neu. Nichts weiter zu tun.

---

## Teil 2 – WordPress anbinden (Termine auf der Website)

Empfohlen: das mitgelieferte kostenlose Mini-Plugin.

1. **Plugin-Datei als ZIP verpacken**: die Datei
   `wordpress/eva-ics-importer.php` in eine ZIP-Datei packen
   (Rechtsklick → „komprimieren"/„ZIP").
2. **In WordPress hochladen**: Adminbereich → **Plugins → Installieren →
   Plugin hochladen** → ZIP wählen → **installieren** → **aktivieren**.
3. **Feed-URL eintragen**: **Einstellungen → EVA iCal Import** → die Adresse
   aus Teil 1 (Schritt 6) einfügen → **Speichern**.
4. **Testlauf**: auf derselben Seite **„Jetzt importieren"** klicken.
   Es erscheint „Verarbeitete Termine: N".
5. **Kontrolle**: unter **Veranstaltungen** solltest du die importierten Termine
   sehen. Sie erscheinen automatisch auf eurer Seite
   `elbevalley-agentur.de/veranstaltungen`.

> Ab jetzt holt WordPress die Datei täglich automatisch. Termine werden über
> eine Kennung wiedererkannt – es entstehen keine Doppelungen.

Voraussetzung: „The Events Calendar" ist installiert (ist bei euch bereits der Fall).

---

## Teil 3 – Optional: Altmark & Prignitz freischalten (später)

Wendland und Ludwigslust-Parchim laufen sofort. Für die beiden anderen Regionen
gibt es offizielle Datenschnittstellen; die Zugänge muss man einmalig anfragen.
Details stehen in `ACCESS_REQUESTS.md`. Kurz:

- **Altmark**: bei der Tourismus-Organisation Sachsen-Anhalts (SAiNT/IMG) den
  Projektzugang („experience", ggf. Lizenzschlüssel) anfragen. Danach in GitHub
  unter **Settings → Secrets and variables → Actions** hinterlegen:
  `ALTMARK_ET4_EXPERIENCE` (und ggf. `ALTMARK_ET4_LICENSEKEY`).
- **Prignitz**: in GitHub die Variable `ENABLE_PRIGNITZ_HEADLESS = 1` setzen
  (nutzt die öffentliche Seite), oder – sauberer – bei der TMB Brandenburg den
  Zugang zur Veranstaltungsdatenbank anfragen.

Sobald hinterlegt, tauchen die Regionen beim nächsten nächtlichen Lauf
automatisch mit auf.

---

## Woran erkenne ich, dass alles läuft?

- **GitHub → Actions**: grüner Haken beim täglichen Lauf. Die Zusammenfassung
  zeigt, wie viele Termine je Region gefunden wurden.
- **`…/last-build.txt`** unter der Pages-Adresse zeigt den Zeitpunkt des letzten Baus.
- **WordPress → Veranstaltungen**: die Termine sind da und aktuell.

## Wenn mal etwas klemmt

- Eine Quelle liefert nichts? Die Automatik überspringt sie und macht mit den
  anderen weiter – der Kalender bleibt also gefüllt. Im Actions-Protokoll steht,
  welche Quelle betroffen war.
- Nichts in WordPress? Prüfen: Feed-URL korrekt gespeichert? „Jetzt importieren"
  getestet? „The Events Calendar" aktiv?

## Rechtlicher Hinweis
Offizielle Feeds/Schnittstellen sind zur Weiterverwendung gedacht. Bei den
öffentlich gelesenen Quellen die Nutzungsbedingungen der Betreiber beachten und
im Zweifel kurz um Freigabe bitten – das ist die dauerhaft sauberste Lösung.
