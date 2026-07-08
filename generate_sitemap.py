#!/usr/bin/env python3
"""Generate sitemap.xml for AstroAxis."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

BASE_URL = "https://lazycat00x.github.io/astroaxis-site/"
SITE_URL = BASE_URL.rstrip("/")

def generate_sitemap():
    DATA_DIR = Path(__file__).parent / "data"
    DEPLOY_DIR = Path(__file__).parent / "deploy"
    
    # Load articles from deploy/news-data.json (has the actual published data)
    articles = []
    news_file = DEPLOY_DIR / "news-data.json"
    if news_file.exists():
        with open(news_file) as f:
            data = json.load(f)
            articles = data.get("articles", [])
    else:
        articles_file = DATA_DIR / "articles.json"
        if articles_file.exists():
            with open(articles_file) as f:
                articles = json.load(f)
    
    urls = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Main page
    urls.append({
        "loc": BASE_URL,
        "lastmod": now,
        "changefreq": "hourly",
        "priority": "1.0"
    })
    
    # Article pages
    import re, hashlib
    def slugify(title):
        s = title.lower().strip()
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'[-\s]+', '-', s)
        s = s.strip('-')[:80]
        if not s:
            s = hashlib.md5(title.encode()).hexdigest()[:12]
        return s
    
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
    
    # Build XML — include topic + source pages
    topics_seen = set()
    sources_seen = set()
    topics_xml = []
    sources_xml = []
    for a in articles:
        topic = a.get("topic", "General") or "General"
        source = a.get("source", "Unknown") or "Unknown"
        slug = lambda s: re.sub(r'[^\\w\\s-]', '', s.lower().strip()).replace(' ', '-')[:80]
        ts = slug(topic)
        ss = slug(source)
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
    
    # Write to deploy
    output_path = DEPLOY_DIR / "sitemap.xml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(xml)
    
    print(f"Generated sitemap.xml with {len(urls)} URLs")

if __name__ == "__main__":
    generate_sitemap()