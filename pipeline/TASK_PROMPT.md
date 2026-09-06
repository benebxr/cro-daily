CRO Daily: taegliche Podcast-Folge fuer Bene (CRO bei easybill). Du produzierst heute eine Folge von Recherche bis MP3 im Feed. Arbeite die Schritte vollstaendig ab, ohne Rueckfragen; niemand liest mit.

STORAGE-REGEL: Diese Session laeuft in der Cloud ohne Zugriff auf Benes Vault. Behaupte nichts ueber Projekt-, Mandats- oder Trainingsstatus. Das Werkprodukt (Skript, Shownotes, MP3) landet im GitHub-Repo `cro-daily`; die Akte im Vault ist `Business Thought Partner/Business Thought Partner/cro-daily/` und wird von dort aus dem Repo nachgezogen, nicht von dir.

VERTRAULICHKEIT: Der Feed liegt auf GitHub Pages, unverlinkt, aber technisch oeffentlich. Deshalb: keine easybill-internen Zahlen (ARR, Churn, Headcount, Budgets, Verguetung, Namen von Kollegen oder Investoren-Interna) im Skript oder in den Shownotes. easybill wird als Anwendungsfall in allgemeinen Worten behandelt ("ein SMB-Rechnungs-SaaS vor der E-Rechnungswelle"). Oeffentlich Bekanntes (Produkt, Preise auf der Website, E-Rechnungspflicht) ist erlaubt.

SCHRITT 0 - Vorbedingungen
Das Repo `benebxr/cro-daily` ist dieser Routine zugeordnet und liegt bereits geklont im Arbeitsverzeichnis (pruefe mit `ls`; liegt es nicht da: `git clone https://github.com/benebxr/cro-daily.git`, der GitHub-Proxy authentifiziert). Wechsle hinein und ziehe den aktuellen Stand: `git checkout main && git pull`.
Der Gemini-Key liegt als API-Credential der Cloud-Umgebung (Host generativelanguage.googleapis.com) und wird vom Proxy angehaengt; er ist nicht als Variable sichtbar, das ist normal. Schlaegt der TTS-Aufruf spaeter mit 401 oder 403 fehl, fehlt das Credential: dann abbrechen und in einem Satz melden "CRO Daily: Gemini-Credential der Cloud-Umgebung fehlt oder ist ungueltig, keine Folge produziert."

SCHRITT 1 - Steuerseite lesen
a) Notion-Seite "CRO Daily HQ" (ID 3d37a10d-51e5-81d5-a048-d8a72951d43b) vollstaendig lesen. Sie ist kanonisch: Hoererprofil, Themenprofil mit 90-Tage-Kalender, Format-Vertrag, Quellenlisten 4a-4g, Feedback von Bene, Themen-Log.
b) Notion-Seite "Morning Brief HQ" (ID 3c37a10d-51e5-8102-a9b1-ed335e183668): aus den letzten 14 Log-Eintraegen nur die "Learning:"-Teile extrahieren. Diese Stuecke sind gesperrt.
c) Heutigen Tag im 90-Tage-Plan bestimmen (Tag 1 = Mo 07.09.2026) und die Phase daraus ableiten. Beides steuert die Auswahl.

SCHRITT 2 - Sammeln (Zeitbudget ca. 20 Minuten, nicht mehr)
a) Gmail: `search_threads` mit `newer_than:2d` und den Absendern aus Liste 4a (als OR-Gruppe). Treffer mit `get_message` im Format PLAIN_TEXT lesen.
b) RSS: in Bash `pip install feedparser requests --break-system-packages -q`, dann per Python alle Feeds aus 4b laden und Eintraege der letzten 3 Tage (montags: 4 Tage) mit Titel, Datum, Link, Summary ausgeben. User-Agent "Mozilla/5.0 cro-daily" setzen.
c) Podcasts aus 4d: Feed per iTunes-Suche aufloesen (`https://itunes.apple.com/search?term=<Name>&media=podcast&limit=1`, Feld `feedUrl`), Episoden der letzten 7 Tage mit Shownotes. Bei Lenny's Podcast die Substack-Episodenseite per WebFetch lesen (enthaelt das Transkript).
d) Websites aus 4c per WebFetch mit der Frage "Welche Beitraege sind seit <Datum vor 4 Tagen> erschienen? Titel, Datum, URL, Kernaussage."
e) WebSearch: zwei bis drei Suchen aus 4e, passend zur Phase.
Ergebnis: Kandidatenliste mit Titel, Quelle, Datum, URL, zwei Saetzen Inhalt und Relevanz-Score 1-5. Score-Kriterien: enthaelt Mechanik oder Zahlen (kein Meinungsstueck), trifft die aktuelle Phase, besteht den "wuerde jedem CRO irgendwo passen"-Test nicht (also spezifisch), steht nicht in 4g oder in einer Sperrliste.

SCHRITT 3 - Auswahl
Hauptstueck: hoechster Score mit Substanz; Volltext per WebFetch lesen, nie aus dem Teaser schreiben. Zweites Stueck: anderes Themenfeld als das Hauptstueck. Radar: zwei bis drei Kurzmeldungen. Konzept des Tages: aus 4f, passend zum Hauptstueck, nicht im Themen-Log der letzten 30 Tage. Der eine Move: eine konkrete Handlung fuer diese Woche, an die Phase gekoppelt, in einem Satz formulierbar.
Liegt kein Kandidat bei Score 3 oder hoeher: kuerzere Folge (mindestens 8 Minuten) nur aus Radar plus Konzept plus Move. Ist auch das nicht tragfaehig: keine Folge, Log-Eintrag mit Begruendung, Schritt 5 ueberspringen.

SCHRITT 4 - Skript und Shownotes schreiben
Skript nach `scripts/YYYY-MM-DD.md` (Datum = heute, Europe/Berlin). Format:
```
---
title: CRO Daily DD.MM. - <Kernthema in 3-6 Woertern>
description: <ein Satz>
date: YYYY-MM-DD
---
NINA: ...
JONAS: ...
===
```
Regeln fuer das Skript:
- 2.700 bis 3.000 Woerter (gemessen: rund 160 Woerter pro Minute Audio). Nach jedem Block (Cold Open, Hauptstueck, zweites Stueck, Radar, Konzept, Move) eine Zeile `===`.
- Zwei Sprecher, exakt "NINA:" und "JONAS:" am Zeilenanfang, jede Aeusserung eine Zeile. NINA moderiert, fragt nach, stellt den Bezug zu Benes Woche her. JONAS liefert Substanz, Zahlen, Mechanik, Gegenargument.
- Deutsch, englische Fachbegriffe bleiben englisch. Direkt, dicht, keine Floskeln, keine Begruessungsrituale laenger als ein Satz, kein Lob des eigenen Formats.
- Verboten: Gedankenstriche, "nicht X, sondern Y"-Konstruktionen, leere Verstaerker ("wirklich", "unglaublich"), Aufzaehlungsrhythmus um seiner selbst willen.
- TTS-tauglich: keine Sonderzeichen wie %, €, →, keine URLs, keine Klammern, keine Abkuerzungen, die man nicht spricht (schreibe "zum Beispiel", "Prozent", "Euro"). Zahlen so schreiben, wie sie gesprochen werden sollen.
- Jede Zahl stammt aus der genannten Quelle. Wenn eine Quelle nur Shownotes hat, sagt JONAS das. Im Audio Quellen nur mit Autor und Format nennen ("Kyle Poyar in Growth Unhinged"), Details stehen in den Shownotes.
- Der Move ist der letzte Block, in einem Satz von NINA zusammengefasst, dann Schluss ohne Verabschiedungsfloskel-Kaskade.
Shownotes nach `docs/episodes/YYYY-MM-DD.md`: drei Saetze Zusammenfassung; "## Quellen" mit Titel, Autor, Datum, URL je Zeile als "- "; "## Konzept des Tages" mit Buch/Autor; "## Der eine Move" ein Satz.

SCHRITT 5 - Produktion und Veroeffentlichung
Im Repo-Verzeichnis:
```
pip install requests --break-system-packages -q
python3 pipeline/tts.py scripts/YYYY-MM-DD.md docs/episodes/YYYY-MM-DD.mp3
python3 pipeline/feed.py
git add -A && git commit -m "Folge YYYY-MM-DD" && git push origin main
```
Direkt auf `main` pushen, keinen `claude/`-Branch und keinen Pull Request anlegen: der Feed wird aus `main` gebaut.
Schlaegt `tts.py` fehl: einmal wiederholen. Schlaegt es wieder fehl: nichts pushen (keine halbe Folge, kein JSON ohne MP3), Fehlertext in den Log-Eintrag, Meldung an Bene. Nach dem Push zwei Minuten warten, dann `curl -sI <base_url aus pipeline/config.json>/episodes/YYYY-MM-DD.mp3` pruefen; HTTP 200 erwartet. Bleibt es nach drei Versuchen im Abstand von zwei Minuten bei etwas anderem: melden, nicht endlos warten.

SCHRITT 6 - Log und Meldung
Auf der Notion-Seite "CRO Daily HQ" im Abschnitt "6. Themen-Log" ganz oben (direkt unter der Ueberschrift) einen Eintrag einfuegen, bestehende Eintraege unangetastet lassen:
`**YYYY-MM-DD** (Tag N, Phase X) - <Titel>, <Dauer> Min, <Woerter> W. Hauptstueck: <Quelle, Titel>. Zweites Stueck: <...>. Radar: <a; b; c>. Konzept: <...>. Move: <...>. Verworfen: <Kandidat (Grund); ...>.`
Bei Ausfall: `**YYYY-MM-DD** - keine Folge. Grund: <...>.`
Schlussantwort an Bene, genau ein Satz: "CRO Daily DD.MM.: <Titel>, <Dauer> Min. Move: <ein Satz>." Bei Ausfall ein Satz mit dem Grund. Keine Zusammenfassung des Vorgehens.
