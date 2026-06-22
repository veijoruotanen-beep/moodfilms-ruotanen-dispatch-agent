#!/usr/bin/env python3
"""
Moodfilms + Ruotanen Dispatch Agent v3

Purpose:
- Moodfilms is on Webnode, so this tool DOES NOT require Moodfilms root file access.
- ruotanen.com works as the technical dispatch hub.
- The tool generates machine-readable update files under:
  upload-to-ruotanen/dispatch/moodfilms/

It can run:
- locally on a Mac
- in GitHub Actions
- as a workflow_dispatch "agent-like" form in GitHub
"""

from pathlib import Path
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape
import argparse
import json
import urllib.request
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config.json"
CHANGES = ROOT / "data" / "changes.json"
OUT = ROOT / "upload-to-ruotanen" / "dispatch" / "moodfilms"
DRAFTS = ROOT / "drafts"
MANUAL = ROOT / "manual-submit"
WEBNODE = ROOT / "webnode-header-snippets"

def now_utc():
    return datetime.now(timezone.utc)

def now_iso():
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")

def rss_date(dt=None):
    return format_datetime(dt or now_utc())

def read_json(path, default):
    if not Path(path).exists():
        return default
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load():
    return read_json(CONFIG, {}), read_json(CHANGES, [])

def save_changes(changes):
    write_json(CHANGES, changes)

def normalize_tags(tags):
    if isinstance(tags, str):
        return [t.strip() for t in tags.split(",") if t.strip()]
    return tags or []

def add_change(args):
    changes = read_json(CHANGES, [])
    item = {
        "date": args.date or now_iso()[:10],
        "type": args.type or "update",
        "title": args.title.strip(),
        "url": args.url.strip(),
        "summary": args.summary.strip(),
        "tags": normalize_tags(args.tags),
        "local_signal": bool(args.local_signal),
        "gbp_draft": bool(args.gbp_draft),
        "linkedin_draft": bool(args.linkedin_draft)
    }
    changes.insert(0, item)
    save_changes(changes)
    print(f"Added change: {item['title']}")

def hashtags(tags):
    out = []
    for tag in tags:
        t = tag.replace(" ", "").replace("-", "")
        t = t.replace("ä","a").replace("ö","o").replace("å","a").replace("Ä","A").replace("Ö","O").replace("Å","A")
        t = "".join(ch for ch in t if ch.isalnum() or ch == "_")
        if t:
            out.append("#" + t)
    return " ".join(list(dict.fromkeys(out))[:8])

def build_rss(cfg, changes):
    base = cfg["dispatch_base_url"]
    latest = rss_date()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        '  <channel>',
        '    <title>Moodfilms dispatch feed</title>',
        f'    <link>{escape(cfg["moodfilms"]["site"])}</link>',
        f'    <description>{escape(cfg["moodfilms"]["description"])}</description>',
        '    <language>fi</language>',
        f'    <lastBuildDate>{escape(latest)}</lastBuildDate>',
        f'    <atom:link href="{escape(base + "/feed.xml")}" rel="self" type="application/rss+xml" />'
    ]
    for item in changes[:50]:
        title = item.get("title","")
        url = item.get("url","")
        summary = item.get("summary","")
        pub = item.get("date","")
        try:
            pubdate = format_datetime(datetime.fromisoformat(pub + "T09:00:00+00:00"))
        except Exception:
            pubdate = latest
        lines += [
            '    <item>',
            f'      <title>{escape(title)}</title>',
            f'      <link>{escape(url)}</link>',
            f'      <guid isPermaLink="true">{escape(url)}</guid>',
            f'      <pubDate>{escape(pubdate)}</pubDate>',
            f'      <description>{escape(summary)}</description>',
        ]
        for tag in item.get("tags", []):
            lines.append(f'      <category>{escape(tag)}</category>')
        lines.append('    </item>')
    lines += ['  </channel>', '</rss>']
    return "\n".join(lines) + "\n"

def build_latest_md(changes):
    if not changes:
        return "# Moodfilms dispatch latest\n\nNo updates yet.\n"
    i = changes[0]
    tags = ", ".join(i.get("tags", []))
    return f"""# Moodfilms dispatch latest

## {i.get("title","")}

URL: {i.get("url","")}

Date: {i.get("date","")}

Summary: {i.get("summary","")}

Tags: {tags}

This file is part of the ruotanen.com dispatch hub for Moodfilms updates.
"""

def build_index(cfg, changes):
    return {
        "name": "Moodfilms dispatch hub",
        "generated": now_iso(),
        "purpose": "Machine-readable dispatch hub for Moodfilms updates. Moodfilms is hosted on Webnode; ruotanen.com acts as the technical update feed and AI/search discovery layer.",
        "moodfilms": cfg["moodfilms"],
        "ruotanen_dispatch_base_url": cfg["dispatch_base_url"],
        "feeds": {
            "rss": cfg["dispatch_base_url"] + "/feed.xml",
            "updates": cfg["dispatch_base_url"] + "/updates.json",
            "targets": cfg["dispatch_base_url"] + "/targets.json",
            "latest": cfg["dispatch_base_url"] + "/latest.md"
        },
        "latest_update": changes[0] if changes else None
    }

def build_targets(cfg, changes):
    urls = []
    for i in changes:
        u = i.get("url")
        if u and u not in urls:
            urls.append(u)
    defaults = [
        "https://www.moodfilms.com/",
        "https://www.moodfilms.com/videotuotanto/",
        "https://www.moodfilms.com/valokuvaus/",
        "https://www.moodfilms.com/lehtikuvaus/",
        "https://www.moodfilms.com/ilmakuvaus/",
        "https://www.moodfilms.com/360-kuvaus/",
        "https://www.moodfilms.com/yhteydenotto/"
    ]
    for u in defaults:
        if u not in urls:
            urls.append(u)
    return {
        "name": "Moodfilms target URLs",
        "generated": now_iso(),
        "note": "These are Moodfilms URLs referenced by the ruotanen.com dispatch hub. Because Moodfilms is hosted on Webnode, IndexNow is submitted for ruotanen.com dispatch URLs, while these target URLs are for manual Bing/Search Console checks and automation drafts.",
        "urls": urls
    }

def build_webnode_snippet(cfg):
    base = cfg["dispatch_base_url"]
    return f"""<!-- Moodfilms machine-readable dispatch links.
     Add once to Webnode global HTML header if possible. -->
<link rel="alternate" type="application/rss+xml" title="Moodfilms updates" href="{base}/feed.xml">
<link rel="alternate" type="application/json" title="Moodfilms machine updates" href="{base}/updates.json">
<link rel="author" href="https://ruotanen.com/">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://www.moodfilms.com/#website",
  "url": "https://www.moodfilms.com/",
  "name": "Moodfilms",
  "subjectOf": [
    {{
      "@type": "DataFeed",
      "name": "Moodfilms updates",
      "url": "{base}/feed.xml"
    }},
    {{
      "@type": "DigitalDocument",
      "name": "Moodfilms machine-readable update log",
      "url": "{base}/updates.json"
    }}
  ]
}}
</script>
"""

def draft_linkedin(item):
    return f"""Päivitin Moodfilmsin sivuille uuden sisällön:

{item.get("title","")}

{item.get("summary","")}

Lue lisää:
{item.get("url","")}

{hashtags(item.get("tags", []))}
"""

def draft_gbp(item):
    return f"""Otsikko:
{item.get("title","")}

Teksti:
{item.get("summary","")}

Lue lisää:
{item.get("url","")}
"""

def generate(submit=False):
    cfg, changes = load()
    OUT.mkdir(parents=True, exist_ok=True)
    DRAFTS.mkdir(exist_ok=True)
    MANUAL.mkdir(exist_ok=True)
    WEBNODE.mkdir(exist_ok=True)

    # outputs for ruotanen.com
    (OUT / "feed.xml").write_text(build_rss(cfg, changes), encoding="utf-8")
    write_json(OUT / "updates.json", {
        "name": "Moodfilms updates",
        "generated": now_iso(),
        "source_site": cfg["moodfilms"]["site"],
        "dispatch_site": cfg["dispatch_base_url"],
        "updates": changes
    })
    write_json(OUT / "index.json", build_index(cfg, changes))
    write_json(OUT / "targets.json", build_targets(cfg, changes))
    (OUT / "latest.md").write_text(build_latest_md(changes), encoding="utf-8")

    # snippets/manual files
    (WEBNODE / "moodfilms-global-header-extra.html").write_text(build_webnode_snippet(cfg), encoding="utf-8")
    target_urls = build_targets(cfg, changes)["urls"]
    (MANUAL / "bing-submit-urls-moodfilms.txt").write_text("\n".join(target_urls) + "\n", encoding="utf-8")
    (MANUAL / "google-search-console-check-urls-moodfilms.txt").write_text("\n".join(target_urls[:10]) + "\n", encoding="utf-8")

    if changes:
        (DRAFTS / "linkedin-draft.md").write_text(draft_linkedin(changes[0]), encoding="utf-8")
        (DRAFTS / "google-business-profile-post.md").write_text(draft_gbp(changes[0]), encoding="utf-8")

    # IndexNow only for ruotanen.com dispatch URLs
    dispatch_urls = [
        cfg["dispatch_base_url"] + "/feed.xml",
        cfg["dispatch_base_url"] + "/updates.json",
        cfg["dispatch_base_url"] + "/index.json",
        cfg["dispatch_base_url"] + "/targets.json",
        cfg["dispatch_base_url"] + "/latest.md",
    ]
    payload = {
        "host": cfg["indexnow"]["host"],
        "key": cfg["indexnow"]["key"],
        "keyLocation": cfg["indexnow"]["keyLocation"],
        "urlList": dispatch_urls
    }
    write_json(MANUAL / "indexnow-payload-ruotanen-dispatch.json", payload)

    print("Generated dispatch hub files:")
    print(f"- {OUT}")
    print(f"- {WEBNODE / 'moodfilms-global-header-extra.html'}")
    print(f"- {MANUAL / 'bing-submit-urls-moodfilms.txt'}")
    print(f"- {DRAFTS}")

    if submit:
        status, body = submit_indexnow(cfg["indexnow_endpoint"], payload)
        print(f"IndexNow status: {status}")
        if body:
            print(body)

def submit_indexnow(endpoint, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None, str(e)

def interactive():
    print("Moodfilms + Ruotanen Dispatch Agent v3")
    print("Moodfilms is Webnode-safe: no Moodfilms root upload needed.")
    print("")
    title = input("Title: ").strip()
    url = input("Moodfilms URL: ").strip()
    summary = input("Short summary: ").strip()
    tags = input("Tags, comma-separated: ").strip()
    kind = input("Type [blog/project/service_page_update/update]: ").strip() or "update"
    args = argparse.Namespace(
        date=None,
        type=kind,
        title=title,
        url=url,
        summary=summary,
        tags=tags,
        local_signal=True,
        gbp_draft=True,
        linkedin_draft=True
    )
    add_change(args)
    submit = input("Submit IndexNow for ruotanen.com dispatch URLs now? [y/N]: ").strip().lower() == "y"
    generate(submit=submit)

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("add")
    a.add_argument("--date")
    a.add_argument("--type", default="update")
    a.add_argument("--title", required=True)
    a.add_argument("--url", required=True)
    a.add_argument("--summary", required=True)
    a.add_argument("--tags", default="")
    a.add_argument("--local-signal", action="store_true")
    a.add_argument("--gbp-draft", action="store_true")
    a.add_argument("--linkedin-draft", action="store_true")

    g = sub.add_parser("generate")
    g.add_argument("--submit", action="store_true")

    sub.add_parser("interactive")

    args = p.parse_args()

    if args.cmd == "add":
        add_change(args)
        generate(submit=False)
    elif args.cmd == "generate":
        generate(submit=args.submit)
    else:
        interactive()

if __name__ == "__main__":
    main()
