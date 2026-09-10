#!/usr/bin/env python3
"""
CRO Daily - Skript -> MP3 via Gemini TTS (zwei Sprecher).

Aufruf:
    python3 pipeline/tts.py <skript.md> <out.mp3>

Skriptformat (Markdown):
    ---
    title: ...
    description: ...
    date: YYYY-MM-DD
    ---
    NINA: Satz ...
    JONAS: Satz ...
    ===                      <- optionale Chunk-Grenze (sonst automatisch ~ alle 900 Woerter; Free Tier erlaubt 3 Requests/Minute und 10/Tag, Paid Tier 1000/Tag)

Umgebung:
    GEMINI_API_KEY   optional, wenn die Cloud-Umgebung den Key als API-Credential anhaengt (Header x-goog-api-key)
    TTS_MODEL        optional, Default gemini-2.5-flash-preview-tts
    TTS_VOICE_A/B    optional, Default Kore (NINA) / Charon (JONAS)
"""
import base64
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

SPEAKER_A = os.environ.get("TTS_SPEAKER_A", "NINA")
SPEAKER_B = os.environ.get("TTS_SPEAKER_B", "JONAS")
VOICE_A = os.environ.get("TTS_VOICE_A", "Kore")
VOICE_B = os.environ.get("TTS_VOICE_B", "Charon")
MODEL = os.environ.get("TTS_MODEL", "gemini-2.5-flash-preview-tts")
FALLBACK_MODELS = ["gemini-2.5-flash-preview-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-pro-preview-tts"]
CHUNK_WORDS = int(os.environ.get("TTS_CHUNK_WORDS", "900"))
MAX_TRIES = int(os.environ.get("TTS_MAX_TRIES", "6"))
PAUSE_BETWEEN_CHUNKS = int(os.environ.get("TTS_PAUSE", "22"))  # Free Tier: 3 Requests/Minute
SAMPLE_RATE = 24000

STYLE_PROMPT = (
    f"Lies das folgende Gespraech auf Deutsch vor. Es ist ein Podcast zwischen {SPEAKER_A} und {SPEAKER_B}. "
    f"{SPEAKER_A} moderiert: klar, warm, zuegig, neugierig. {SPEAKER_B} ist der Analyst: ruhig, praezise, trocken-humorvoll. "
    "Natuerliches Sprechtempo wie in einem professionellen Podcast, keine Kunstpausen, englische Fachbegriffe "
    "englisch aussprechen, Zahlen und Abkuerzungen natuerlich lesen.\n\n"
)


def parse_script(path: Path):
    text = path.read_text(encoding="utf-8")
    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        text = text[m.end():]
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == "===":
            lines.append(("BREAK", ""))
            continue
        mm = re.match(rf"^({SPEAKER_A}|{SPEAKER_B})\s*:\s*(.+)$", line)
        if mm:
            lines.append((mm.group(1), mm.group(2).strip()))
        elif lines and lines[-1][0] not in ("BREAK",):
            # Fortsetzungszeile
            lines[-1] = (lines[-1][0], lines[-1][1] + " " + line)
    return meta, lines


def chunk_lines(lines):
    """Teilt in moeglichst wenige, gleich grosse Chunks (<= CHUNK_WORDS).

    "===" ist eine weiche Grenze: bevorzugter Schnittpunkt, aber kein Zwang zu einem
    eigenen Request pro Block (Free Tier: jeder Request zaehlt aufs Tageskontingent).
    """
    import math
    spoken = [(s, t) for s, t in lines if s != "BREAK"]
    total = sum(len(t.split()) for _, t in spoken)
    if total == 0:
        return []
    n_chunks = max(1, math.ceil(total / CHUNK_WORDS))
    target = total / n_chunks
    chunks, cur, words, done = [], [], 0, 0
    for i, (spk, txt) in enumerate(lines):
        if spk == "BREAK":
            # Weiche Grenze: schneiden, wenn der Chunk schon nahe am Ziel ist
            if cur and words >= 0.7 * target and len(chunks) < n_chunks - 1:
                chunks.append(cur)
                cur, words = [], 0
            continue
        n = len(txt.split())
        if cur and (words + n > CHUNK_WORDS or (words >= target and len(chunks) < n_chunks - 1)):
            chunks.append(cur)
            cur, words = [], 0
        cur.append((spk, txt))
        words += n
    if cur:
        chunks.append(cur)
    return chunks


def tts_chunk(dialogue: str, api_key: str, model: str, attempt_models=None) -> bytes:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": STYLE_PROMPT + dialogue}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "multiSpeakerVoiceConfig": {
                    "speakerVoiceConfigs": [
                        {"speaker": SPEAKER_A, "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE_A}}},
                        {"speaker": SPEAKER_B, "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE_B}}},
                    ]
                }
            },
        },
    }
    last_err = None
    for i in range(MAX_TRIES):
        headers = {"x-goog-api-key": api_key} if api_key else {}
        try:
            r = requests.post(url, headers=headers, json=body, timeout=300)
        except requests.RequestException as e:
            last_err = f"network: {e}"
            wait = min(90, 10 * (i + 1))
            print(f"  [{model}] Netzwerkfehler, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        if r.status_code in (401, 403):
            raise RuntimeError(f"HTTP {r.status_code}: kein gueltiger Gemini-Key (weder GEMINI_API_KEY noch API-Credential der Umgebung): {r.text[:300]}")
        if r.status_code == 200:
            data = r.json()
            try:
                part = data["candidates"][0]["content"]["parts"][0]["inlineData"]
                return base64.b64decode(part["data"]), part.get("mimeType", "")
            except (KeyError, IndexError):
                last_err = f"unexpected response: {json.dumps(data)[:500]}"
                break
        if r.status_code == 429 and "PerDay" in r.text:
            # Tageskontingent (Free Tier: 10 Requests/Tag) ist weg, Warten hilft nicht.
            raise RuntimeError(f"HTTP 429 Tageskontingent erschoepft: {r.text[:300]}")
        if r.status_code in (429, 500, 502, 503, 504):
            wait = min(90, 15 * (i + 1))
            m = re.search(r"retry in (\d+(?:\.\d+)?)s", r.text)
            if m:
                wait = max(wait, int(float(m.group(1))) + 2)
            print(f"  [{model}] HTTP {r.status_code}, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
            last_err = r.text[:500]
            continue
        last_err = f"HTTP {r.status_code}: {r.text[:500]}"
        break
    raise RuntimeError(last_err)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        # Kein Key in der Umgebung: die Cloud-Umgebung kann den Key als "API credential"
        # (Host generativelanguage.googleapis.com, Header x-goog-api-key) selbst anhaengen.
        print("Hinweis: GEMINI_API_KEY nicht gesetzt, verlasse mich auf das API-Credential der Cloud-Umgebung.")

    meta, lines = parse_script(src)
    chunks = chunk_lines(lines)
    total_words = sum(len(t.split()) for c in chunks for _, t in c)
    print(f"Skript: {len(lines)} Zeilen, {total_words} Woerter, {len(chunks)} Chunks")

    work = out.parent / (out.stem + "_work")
    work.mkdir(parents=True, exist_ok=True)
    pcm_parts = []
    models = [MODEL] + [m for m in FALLBACK_MODELS if m != MODEL]
    for idx, chunk in enumerate(chunks, 1):
        dialogue = "\n".join(f"{s}: {t}" for s, t in chunk)
        pcm = None
        for model in models:
            try:
                print(f"Chunk {idx}/{len(chunks)} ({sum(len(t.split()) for _, t in chunk)} W) -> {model}")
                pcm, mime = tts_chunk(dialogue, api_key, model)
                break
            except RuntimeError as e:
                print(f"  Fehler mit {model}: {e}", file=sys.stderr)
                # Nur wenn das Hauptmodell sein Tageskontingent meldet, ist der Tag verloren.
                # Fallback-Modelle haben im Free Tier oft Limit 0 und melden das immer; das sagt nichts ueber das Hauptmodell.
                if "Tageskontingent erschoepft" in str(e) and model == models[0]:
                    print("FEHLER: Tageskontingent erschoepft (Hauptmodell), Abbruch.", file=sys.stderr)
                    sys.exit(5)
        if pcm is None:
            print("FEHLER: TTS fuer Chunk fehlgeschlagen, alle Modelle (voruebergehend, Wiederholung sinnvoll).", file=sys.stderr)
            sys.exit(4)
        # mime ist normalerweise audio/L16;codec=pcm;rate=24000
        rate = SAMPLE_RATE
        mr = re.search(r"rate=(\d+)", mime or "")
        if mr:
            rate = int(mr.group(1))
        p = work / f"chunk_{idx:02d}.pcm"
        p.write_bytes(pcm)
        pcm_parts.append((p, rate))
        if idx < len(chunks):
            time.sleep(PAUSE_BETWEEN_CHUNKS)

    # Stille zwischen Chunks (0.35 s), dann MP3
    concat = work / "all.pcm"
    with concat.open("wb") as f:
        for i, (p, rate) in enumerate(pcm_parts):
            f.write(p.read_bytes())
            if i < len(pcm_parts) - 1:
                f.write(b"\x00" * int(rate * 0.35) * 2)
    rate = pcm_parts[0][1]
    title = meta.get("title", "CRO Daily")
    date = meta.get("date", "")
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", str(concat),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-codec:a", "libmp3lame", "-b:a", "64k",
            "-metadata", f"title={title}",
            "-metadata", "artist=CRO Daily",
            "-metadata", "album=CRO Daily",
            "-metadata", f"date={date}",
            str(out),
        ],
        check=True,
    )
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    print(f"OK: {out} ({float(dur)/60:.1f} min, {out.stat().st_size/1e6:.1f} MB)")
    # Metadaten fuer feed.py
    info = {
        "file": out.name,
        "title": title,
        "description": meta.get("description", ""),
        "date": date,
        "duration_sec": int(float(dur)),
        "bytes": out.stat().st_size,
        "words": total_words,
    }
    (out.with_suffix(".json")).write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    for p, _ in pcm_parts:
        p.unlink(missing_ok=True)
    concat.unlink(missing_ok=True)
    work.rmdir()


if __name__ == "__main__":
    main()
