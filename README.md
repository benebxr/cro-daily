# CRO Daily

Taegliches Wissensbriefing als Podcast fuer Bene (CRO, easybill). Ein Scheduled Task in Claude (Cloud) recherchiert jeden Morgen, schreibt ein Zwei-Sprecher-Skript, laesst es von Gemini TTS vertonen und veroeffentlicht die MP3 ueber diesen Feed.

Arbeitsteilung seit 19.09.2026: Die Claude-Routinen (04:30 Hauptlauf, 06:00 Nachlauf, Prompt in `pipeline/TASK_PROMPT.md`) recherchieren, schreiben Skript und Shownotes und pushen sie als "Entwurf". Die Vertonung macht die GitHub Action `.github/workflows/render.yml`: sie startet bei jedem Skript-Push, laeuft um 05:05 und 07:05 Berlin nach und kann per workflow_dispatch fuer ein bestimmtes Datum gestartet werden. Sie braucht das Repository-Secret `GEMINI_API_KEY`. Grund fuer die Trennung: Gemini-TTS-Aufrufe aus der Claude-Cloud-Umgebung scheitern ab etwa 30 Sekunden Antwortzeit mit HTTP 502 (Proxy), eine 700-Woerter-Passage braucht 60 bis 90 Sekunden.

**Feed-URL (in Apple Podcasts / Overcast per "URL hinzufuegen"):** `https://benebxr.github.io/cro-daily/feed.xml`

## Aufbau

```
pipeline/tts.py        Skript (Markdown, NINA/JONAS) -> MP3 via Gemini TTS, chunked, ffmpeg, loudnorm
pipeline/feed.py       docs/episodes/*.json -> docs/feed.xml + docs/index.html (Player + Shownotes)
pipeline/config.json   Titel, base_url, keep_episodes (aeltere Folgen werden geloescht)
pipeline/TASK_PROMPT.md  Der Prompt des Scheduled Tasks, versioniert (Kopie des Live-Prompts)
docs/                  GitHub-Pages-Root: feed.xml, index.html, cover.png, episodes/
docs/episodes/         YYYY-MM-DD.mp3 + .json (Metadaten) + .md (Shownotes und Quellen)
scripts/               YYYY-MM-DD.md, das vertonte Skript (Archiv)
```

## Steuerung

Die Quellen, das Themenprofil und das Themen-Log leben **nicht** hier, sondern auf der Notion-Seite **"CRO Daily HQ"**. Der Task liest sie vor jedem Lauf und haengt nach jedem Lauf einen Log-Eintrag an. Quellen aendern = Notion-Seite editieren, sonst nichts.

## Manuell eine Folge bauen

```bash
export GEMINI_API_KEY=...
python3 pipeline/tts.py scripts/2026-09-07.md docs/episodes/2026-09-07.mp3
cp shownotes.md docs/episodes/2026-09-07.md
python3 pipeline/feed.py
git add -A && git commit -m "Folge 2026-09-07" && git push
```

## Skriptformat

```
---
title: CRO Daily 07.09. - Titel
description: Ein Satz.
date: 2026-09-07
---
NINA: ...
JONAS: ...
===            (optionale Chunk-Grenze; sonst automatisch alle ~900 Woerter)
```

Richtwert: rund 160 Woerter pro Minute; 2.700 bis 3.000 Woerter ergeben 17 bis 19 Minuten.

## Umgebung (Scheduled Task und Action)

Der Task laeuft in Benes Cloud-Umgebung. GitHub-Zugriff kommt ueber die GitHub-Verbindung des Claude-Kontos (Proxy, kein Token im Container). Der Gemini-Key liegt als API-Credential der Umgebung (Host generativelanguage.googleapis.com, Header x-goog-api-key) oder ersatzweise als Umgebungsvariable GEMINI_API_KEY. Fehlt beides, bricht tts.py mit einer klaren Meldung ab statt eine halbe Folge zu bauen.

## Gemini-Kontingent

Der Free Tier von Gemini 2.5 Flash TTS erlaubt 3 Requests pro Minute und 10 pro Tag (Reset Mitternacht Pacific = 09:00 Berlin; der 04:30-Lauf faellt noch in den Kontingent-Tag des Vortags). Eine 18-Minuten-Folge braucht mit 900-Woerter-Chunks 4 Requests, Tests und Wiederholungen kommen dazu. Die Laeufe am 06.09., 08.09. und 09.09.2026 sind daran gescheitert (RESOURCE_EXHAUSTED bzw. HTTP 502). `tts.py` wartet bei 429/5xx die von Gemini genannte Zeit, pausiert 22 Sekunden zwischen Chunks und bricht bei erschoepftem Tageskontingent sofort ab. Fuer den Dauerbetrieb muss im Google-AI-Studio-Projekt Billing aktiviert sein (Paid Tier 1: 1.000 Requests pro Tag, Kosten pro Folge im Cent-Bereich). Der API-Key bleibt derselbe.

## Wenn interne easybill-Quellen dazukommen

GitHub Pages ist unverlinkt, aber oeffentlich. Vor der ersten internen Quelle: Hosting auf einen privaten Speicher mit signierten URLs umstellen (z.B. Cloudflare R2) oder auf eine Claude-Artifact-Seite. Bis dahin nur oeffentliche Quellen und Benes eigene Newsletter.
