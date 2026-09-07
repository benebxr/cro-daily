#!/usr/bin/env python3
"""
CRO Daily - baut docs/feed.xml und docs/index.html aus docs/episodes/*.json.

Aufruf:
    python3 pipeline/feed.py

Liest pipeline/config.json (base_url, title, author, description, email, keep_episodes).
Fuer jede Episode YYYY-MM-DD.json wird YYYY-MM-DD.mp3 erwartet, optional YYYY-MM-DD.md (Shownotes).
Aeltere Episoden als keep_episodes werden aus Feed, Index und Ordner entfernt (Repo-Groesse).
"""
import html
import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EPS = DOCS / "episodes"
CFG = json.loads((ROOT / "pipeline" / "config.json").read_text(encoding="utf-8"))


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def md_to_html(md: str) -> str:
    out = []
    for line in md.splitlines():
        if line.startswith("### "):
            out.append(f"<h4>{esc(line[4:])}</h4>")
        elif line.startswith("## "):
            out.append(f"<h3>{esc(line[3:])}</h3>")
        elif line.startswith("# "):
            out.append(f"<h2>{esc(line[2:])}</h2>")
        elif line.startswith("- "):
            out.append(f"<li>{linkify(esc(line[2:]))}</li>")
        elif line.strip() == "":
            out.append("")
        else:
            out.append(f"<p>{linkify(esc(line))}</p>")
    s = "\n".join(out)
    s = re.sub(r"(<li>.*?</li>\n?)+", lambda m: "<ul>" + m.group(0) + "</ul>", s, flags=re.S)
    return s


def linkify(s: str) -> str:
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', s)


def fmt_dur(sec: int) -> str:
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main():
    eps = []
    for j in sorted(EPS.glob("*.json"), key=lambda x: x.stem.replace("-", "~", 2).replace("-", "."), reverse=True):
        info = json.loads(j.read_text(encoding="utf-8"))
        mp3 = EPS / info["file"]
        if not mp3.exists():
            continue
        notes_md = EPS / (j.stem + ".md")
        info["notes_md"] = notes_md.read_text(encoding="utf-8") if notes_md.exists() else ""
        info["stem"] = j.stem
        eps.append(info)

    keep = int(CFG.get("keep_episodes", 60))
    for old in eps[keep:]:
        for ext in (".mp3", ".json", ".md"):
            (EPS / (old["stem"] + ext)).unlink(missing_ok=True)
    eps = eps[:keep]

    base = CFG["base_url"].rstrip("/")
    now = format_datetime(datetime.now(timezone.utc))
    items = []
    for e in eps:
        d = datetime.strptime(e["date"], "%Y-%m-%d").replace(hour=4, minute=0, tzinfo=timezone.utc)
        # Zweite Folge am selben Tag (Stem "YYYY-MM-DD-2") bekommt eine spaetere pubDate
        msfx = re.search(r"-(\d+)$", e["stem"][10:])
        if msfx:
            d = d.replace(hour=4 + int(msfx.group(1)))
        url = f"{base}/episodes/{e['file']}"
        notes_html = md_to_html(e["notes_md"]) if e["notes_md"] else f"<p>{esc(e['description'])}</p>"
        items.append(f"""
    <item>
      <title>{esc(e['title'])}</title>
      <itunes:title>{esc(e['title'])}</itunes:title>
      <description><![CDATA[{notes_html}]]></description>
      <itunes:summary>{esc(e['description'])}</itunes:summary>
      <pubDate>{format_datetime(d)}</pubDate>
      <guid isPermaLink="false">cro-daily-{e['stem']}</guid>
      <enclosure url="{url}" length="{e['bytes']}" type="audio/mpeg"/>
      <itunes:duration>{fmt_dur(e['duration_sec'])}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{esc(CFG['title'])}</title>
    <link>{base}/</link>
    <atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>de-de</language>
    <description>{esc(CFG['description'])}</description>
    <itunes:author>{esc(CFG['author'])}</itunes:author>
    <itunes:owner><itunes:name>{esc(CFG['author'])}</itunes:name><itunes:email>{esc(CFG.get('email',''))}</itunes:email></itunes:owner>
    <itunes:image href="{base}/cover.png"/>
    <itunes:category text="Business"/>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <lastBuildDate>{now}</lastBuildDate>
    {''.join(items)}
  </channel>
</rss>
"""
    (DOCS / "feed.xml").write_text(feed, encoding="utf-8")

    cards = []
    for e in eps:
        notes_html = md_to_html(e["notes_md"]) if e["notes_md"] else f"<p>{esc(e['description'])}</p>"
        cards.append(f"""
<article id="{e['stem']}">
  <h2>{esc(e['title'])}</h2>
  <p class="meta">{e['date']} · {fmt_dur(e['duration_sec'])} · {e['bytes']/1e6:.1f} MB</p>
  <audio controls preload="none" src="episodes/{e['file']}"></audio>
  <details><summary>Shownotes und Quellen</summary>{notes_html}</details>
</article>""")

    index = f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(CFG['title'])}</title>
<link rel="alternate" type="application/rss+xml" title="{esc(CFG['title'])}" href="feed.xml">
<style>
body{{font-family:-apple-system,system-ui,sans-serif;max-width:720px;margin:0 auto;padding:24px 16px;color:#1a1a1a;background:#fafaf8}}
h1{{font-size:1.5rem;margin:0 0 4px}} .sub{{color:#666;margin:0 0 20px}}
article{{border-top:1px solid #ddd;padding:18px 0}} article h2{{font-size:1.1rem;margin:0 0 4px}}
.meta{{color:#777;font-size:.85rem;margin:0 0 8px}} audio{{width:100%}}
details{{margin-top:8px;font-size:.92rem}} summary{{cursor:pointer;color:#444}}
code{{background:#eee;padding:2px 5px;border-radius:4px}}
</style></head><body>
<h1>{esc(CFG['title'])}</h1>
<p class="sub">{esc(CFG['description'])}</p>
<p>Feed-URL fuer Apple Podcasts / Overcast: <code>{base}/feed.xml</code></p>
{''.join(cards) if cards else '<p>Noch keine Folgen.</p>'}
</body></html>
"""
    (DOCS / "index.html").write_text(index, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Feed gebaut: {len(eps)} Folgen -> docs/feed.xml, docs/index.html")


if __name__ == "__main__":
    main()
