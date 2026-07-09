#!/usr/bin/env python3
"""Generate sitemap.xml for AstroAxis."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from config import DEPLOY_DIR, DATA_DIR, SITE_URL, slugify, load_articles


def generate_sitemap():
    articles = load_articles()

    urls = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Main page
    urls.append({
        "loc": f"{SITE_URL}/",
        "lastmod": now,
        "changefreq": "hourly",
        "priority": "1.0"
    })

    # Article pages
    slug_counts = {}
    for a in articles:
        title = a.get("title", "")
        url = a.get("url", "")
        if not title or not url:
            continue
        published = a.get("published", "")
        lastmod = published.replace("+00:00", "Z") if published else now

        base = slugify(title)
        if base in slug_counts:
            slug_counts[base] += 1
            base = f"{base}-{slug_counts[base]}"
        else:
            slug_counts[base] = 1

        urls.append({
            "loc": f"{SITE_URL}/articles/{quote(base)}.html",
            "lastmod": lastmod,
            "changefreq": "daily",
            "priority": "0.7"
        })

    # Topic + source pages
    topics_seen = set()
    sources_seen = set()
    topics_xml = []
    sources_xml = []
    for a in articles:
        topic = a.get("topic", "General") or "General"
        source = a.get("source", "Unknown") or "Unknown"
        ts = slugify(topic)
        ss = slugify(source)
        if ts and ts not in topics_seen:
            topics_seen.add(ts)
            topics_xml.append(f"""  <url>
    <loc>{SITE_URL}/topic/{quote(ts)}/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>0.6</priority>
  </url>""")
        if ss and ss not in sources_seen:
            sources_seen.add(ss)
            sources_xml.append(f"""  <url>
    <loc>{SITE_URL}/source/{quote(ss)}/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.5</priority>
  </url>""")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
    for u in urls:
        lastmod = u.get('lastmod', now)
        xml += f"""  <url>
    <loc>{u['loc']}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{u['changefreq']}</changefreq>
    <priority>{u['priority']}</priority>
  </url>
"""
    xml += "\n".join(topics_xml)
    xml += "\n".join(sources_xml)
    xml += "</urlset>"

    output_path = DEPLOY_DIR / "sitemap.xml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(xml)

    print(f"Generated sitemap.xml with {len(urls)} URLs")


if __name__ == "__main__":
    generate_sitemap()