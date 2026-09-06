# CRO Daily

Taegliches Wissensbriefing als Podcast fuer Bene (CRO, easybill). Ein Scheduled Task in Claude (Cloud) recherchiert jeden Morgen, schreibt ein Zwei-Sprecher-Skript, laesst es von Gemini TTS vertonen und veroeffentlicht die MP3 ueber diesen Feed.

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
===            (optionale Chunk-Grenze; sonst automatisch alle ~550 Woerter)
```

Richtwert: rund 160 Woerter pro Minute; 2.700 bis 3.000 Woerter ergeben 17 bis 19 Minuten.

## Umgebung (Scheduled Task)

Der Task laeuft in Benes Cloud-Umgebung. GitHub-Zugriff kommt ueber die GitHub-Verbindung des Claude-Kontos (Proxy, kein Token im Container). Der Gemini-Key liegt als API-Credential der Umgebung (Host generativelanguage.googleapis.com, Header x-goog-api-key) oder ersatzweise als Umgebungsvariable GEMINI_API_KEY. Fehlt beides, bricht tts.py mit einer klaren Meldung ab statt eine halbe Folge zu bauen.

## Wenn interne easybill-Quellen dazukommen

GitHub Pages ist unverlinkt, aber oeffentlich. Vor der ersten internen Quelle: Hosting auf einen privaten Speicher mit signierten URLs umstellen (z.B. Cloudflare R2) oder auf eine Claude-Artifact-Seite. Bis dahin nur oeffentliche Quellen und Benes eigene Newsletter.
