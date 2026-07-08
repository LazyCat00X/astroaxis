#!/usr/bin/env python3
"""Generate topic pages, source pages, about page, and RSS feed for AstroAxis."""
import json
import re
import html
import xml.sax.saxutils as saxutils
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
DEPLOY_DIR = BASE_DIR / "deploy"
SITE_URL = "https://lazycat00x.github.io/astroaxis-site"
SITE_NAME = "AstroAxis"


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-")[:80]


def time_ago(pub_str: str) -> str:
    try:
        pub = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        s = int((now - pub).total_seconds())
        if s < 3600:
            return f"{max(1, s // 60)} min ago"
        elif s < 86400:
            return f"{s // 3600} hours ago"
        elif s < 172800:
            return "yesterday"
        else:
            return f"{s // 86400} days ago"
    except Exception:
        return ""


def clean_summary(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"<[^>]+>", "", text)
    t = html.unescape(t)
    t = t.strip()
    # Limit to ~280 chars
    if len(t) > 280:
        t = t[:277] + "..."
    return t


def escape_js(text: str) -> str:
    return text.replace("\\", "\\").replace('"', '\\"').replace("\n", "\\n")


# ── Shared dark-theme CSS (matches article pages) ───────────────────────────
DARK_CSS = """<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0a0a0f;--bg2:#12121a;--bg3:#1a1a26;--border:#2a2a3a;--text:#e4e4ec;--text2:#8888a0;--accent:#6366f1;--accent2:#818cf8;--cyan:#22d3ee}
body{background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;line-height:1.6;min-height:100vh}
.container{max-width:900px;margin:0 auto;padding:0 20px}
.header{background:var(--bg2);border-bottom:1px solid var(--border);padding:20px 0;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px)}
.header-inner{display:flex;align-items:center;gap:12px}
.header h1{font-size:20px;font-weight:700;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header a{color:var(--text2);text-decoration:none;font-size:14px;margin-left:auto}
.header a:hover{color:var(--cyan)}
.breadcrumb{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--text2);margin:24px 0 16px;flex-wrap:wrap}
.breadcrumb a{color:var(--accent2);text-decoration:none}
.breadcrumb a:hover{text-decoration:underline}
.breadcrumb span{color:var(--text)}
.page-title{font-size:clamp(24px,5vw,36px);font-weight:700;margin-bottom:8px;letter-spacing:-0.02em}
.page-subtitle{font-size:14px;color:var(--text2);margin-bottom:32px}
.card-list{display:flex;flex-direction:column;gap:16px;margin-bottom:60px}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:20px 24px;transition:border-color .2s}
.card:hover{border-color:var(--accent2)}
.card-title{font-size:16px;font-weight:600;color:var(--text);text-decoration:none;display:block;margin-bottom:8px;line-height:1.4}
.card-title:hover{color:var(--accent2)}
.card-meta{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--text2);margin-bottom:8px}
.card-source{color:var(--accent2);font-weight:600}
.card-topic{padding:2px 10px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(99,102,241,.15);color:var(--accent2)}
.card-summary{font-size:14px;color:rgba(228,228,236,.85);line-height:1.6}
.footer{text-align:center;padding:24px;color:var(--text2);font-size:12px;border-top:1px solid var(--border);margin-top:auto}
.about-section{margin-bottom:40px}
.about-section h2{font-size:18px;font-weight:600;margin-bottom:12px;color:var(--accent2)}
.about-section p,.about-section li{font-size:14px;color:var(--text2);line-height:1.7}
.about-section ul{padding-left:20px}
.about-section a{color:var(--accent2);text-decoration:none}
.about-section a:hover{text-decoration:underline}
.source-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:40px}
.source-item{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 16px;font-size:14px;color:var(--text2)}
.source-item strong{color:var(--text)}
</style>"""


# ── Page shell ──────────────────────────────────────────────────────────────
def page_shell(title: str, body: str, breadcrumb: str = "") -> str:
    bc_html = f"""<div class="container breadcrumb">{breadcrumb}</div>""" if breadcrumb else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {SITE_NAME}</title>
<meta name="description" content="{title}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE_URL}" />
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='45' fill='none' stroke='%2322d3ee' stroke-width='3'/%3E%3Ccircle cx='50' cy='50' r='30' fill='none' stroke='%236366f1' stroke-width='2' opacity='0.6'/%3E%3C/svg%3E">
{DARK_CSS}
</head>
<body>
<header class="header">
<div class="container header-inner">
<h1><a href="/" style="background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent">{SITE_NAME}</a></h1>
<a href="/">← Back to Globe</a>
</div>
</header>
{bc_html}
<div class="container">
{body}
</div>
<footer class="footer">
<div>{SITE_NAME} · AI-powered news aggregator · <a href="/" style="color:var(--accent2)">Home</a></div>
</footer>
</body>
</html>"""


# ── Build article card HTML ─────────────────────────────────────────────────
def article_card(a: dict) -> str:
    title = html.escape(a.get("title", "Untitled") or "Untitled")
    source = html.escape(a.get("source", "Unknown") or "Unknown")
    topic = html.escape(a.get("topic", "General") or "General")
    summary = clean_summary(a.get("ai_summary", ""))
    url = a.get("url", "#")
    pub = a.get("published", "")
    ta = time_ago(pub) if pub else ""

    card = f"""<article class="card">
<div class="card-meta">
<span class="card-source">{source}</span>
<span class="card-topic">{topic}</span>
<time datetime="{pub}">{ta}</time>
</div>
<a class="card-title" href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
<div class="card-summary">{html.escape(summary)}</div>
</article>"""
    return card


# ── Generate topic / source listing pages ───────────────────────────────────
def generate_listing_page(name: str, articles: list, kind: str) -> str:
    """kind: 'topic' or 'source'"""
    safe = slugify(name)
    if kind == "topic":
        breadcrumb = f'<a href="/">Home</a> <span>/</span> <span>Topic: {html.escape(name)}</span>'
        page_title = f"Topic: {html.escape(name)}"
        page_sub = f"{len(articles)} article{'s' if len(articles) != 1 else ''}"
    else:
        breadcrumb = f'<a href="/">Home</a> <span>/</span> <span>Source: {html.escape(name)}</span>'
        page_title = f"Source: {html.escape(name)}"
        page_sub = f"{len(articles)} article{'s' if len(articles) != 1 else ''}"

    cards = "\n".join(article_card(a) for a in articles)
    body = f"""<h1 class="page-title">{page_title}</h1>
<p class="page-subtitle">{page_sub}</p>
<div class="card-list">
{cards}
</div>"""
    return page_shell(page_title, body, breadcrumb)


# ── Generate about page ───────────────────────────────────────────────────
def generate_about_page(sources: list) -> str:
    breadcrumb = '<a href="/">Home</a> <span>/</span> <span>About</span>'
    source_items = "\n".join(
        f'<div class="source-item"><strong>{html.escape(s)}</strong></div>' for s in sorted(set(sources))
    )
    body = f"""<h1 class="page-title">About {SITE_NAME}</h1>
<div class="about-section">
<h2>What is {SITE_NAME}?</h2>
<p>{SITE_NAME} is an AI-powered news aggregator that collects, summarizes, and organizes the latest headlines from trusted sources across the web. Our goal is to help you stay informed with a clean, fast, and distraction-free reading experience.</p>
</div>
<div class="about-section">
<h2>Sources</h2>
<p>Articles are gathered from a curated list of reputable news outlets and blogs:</p>
<div class="source-grid">
{source_items}
</div>
</div>
<div class="about-section">
<h2>Disclaimer</h2>
<p>The summaries on this site are generated automatically by artificial intelligence and may contain inaccuracies, omissions, or errors. Always verify critical information with the original source before acting on it. {SITE_NAME} does not endorse any particular viewpoint or source.</p>
</div>
<div class="about-section">
<h2>Contact</h2>
<p>For questions or feedback, visit our <a href="/">homepage</a> or check the project repository.</p>
</div>"""
    return page_shell("About", body, breadcrumb)


# ── Generate RSS 2.0 feed ──────────────────────────────────────────────────
def generate_rss(articles: list) -> str:
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for a in articles:
        title = a.get("title", "Untitled") or "Untitled"
        source = a.get("source", "Unknown") or "Unknown"
        topic = a.get("topic", "General") or "General"
        summary = clean_summary(a.get("ai_summary", ""))
        url = a.get("url", "")
        pub = a.get("published", "")
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            pub_rfc = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except Exception:
            pub_rfc = now
        items.append(
            f"""<item>
<title>{saxutils.escape(title)}</title>
<link>{saxutils.escape(url)}</link>
<guid>{saxutils.escape(url)}</guid>
<pubDate>{pub_rfc}</pubDate>
<category>{saxutils.escape(topic)}</category>
<description>{saxutils.escape(summary)}</description>
<source url="{saxutils.escape(url)}">{saxutils.escape(source)}</source>
</item>"""
        )
    items_xml = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>{SITE_NAME}</title>
<link>{SITE_URL}</link>
<description>AI-powered news aggregator</description>
<language>en</language>
<lastBuildDate>{now}</lastBuildDate>
<generator>{SITE_NAME}</generator>
<image>
<url>{SITE_URL}/og-image.png</url>
<title>{SITE_NAME}</title>
<link>{SITE_URL}</link>
</image>
{items_xml}
</channel>
</rss>"""


# ── Main entry ──────────────────────────────────────────────────────────────
def main():
    news_path = DEPLOY_DIR / "news-data.json"
    if not news_path.exists():
        print("ERROR: news-data.json not found.", file=sys.stderr)
        return False

    with open(news_path, encoding="utf-8") as f:
        data = json.load(f)

    articles = data.get("articles", [])
    if not articles:
        print("ERROR: No articles in news-data.json", file=sys.stderr)
        return False

    # Group by topic and source
    topics = defaultdict(list)
    sources = defaultdict(list)
    for a in articles:
        topic = a.get("topic", "General") or "General"
        source = a.get("source", "Unknown") or "Unknown"
        topics[topic].append(a)
        sources[source].append(a)

    # 1. Generate topic pages (subdirectory structure for clean URLs)
    topic_dir = DEPLOY_DIR / "topic"
    topic_dir.mkdir(parents=True, exist_ok=True)
    for topic_name, topic_arts in topics.items():
        slug = slugify(topic_name)
        sub_dir = topic_dir / slug
        sub_dir.mkdir(parents=True, exist_ok=True)
        sorted_arts = sorted(topic_arts, key=lambda x: x.get("published", ""), reverse=True)[:20]
        html_content = generate_listing_page(topic_name, sorted_arts, "topic")
        (sub_dir / "index.html").write_text(html_content, encoding="utf-8")
    # Generate topic index
    topic_index_body = "<h1 class=\"page-title\">Topics</h1>\n<div class=\"card-list\">\n"
    for topic_name in sorted(topics.keys()):
        count = len(topics[topic_name])
        topic_index_body += f"""<article class="card">
<a class="card-title" href="/topic/{slugify(topic_name)}/">{html.escape(topic_name)}</a>
<div class="card-meta">{count} article{'s' if count != 1 else ''}</div>
</article>\n"""
    topic_index_body += "</div>"
    (topic_dir / "index.html").write_text(
        page_shell("Topics", topic_index_body, '<a href="/">Home</a> <span>/</span> <span>Topics</span>'),
        encoding="utf-8",
    )

    # 2. Generate source pages (subdirectory structure for clean URLs)
    source_dir = DEPLOY_DIR / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    for source_name, source_arts in sources.items():
        slug = slugify(source_name)
        sub_dir = source_dir / slug
        sub_dir.mkdir(parents=True, exist_ok=True)
        sorted_arts = sorted(source_arts, key=lambda x: x.get("published", ""), reverse=True)[:20]
        html_content = generate_listing_page(source_name, sorted_arts, "source")
        (sub_dir / "index.html").write_text(html_content, encoding="utf-8")
    # Generate source index
    source_index_body = "<h1 class=\"page-title\">Sources</h1>\n<div class=\"card-list\">\n"
    for source_name in sorted(sources.keys()):
        count = len(sources[source_name])
        source_index_body += f"""<article class="card">
<a class="card-title" href="/source/{slugify(source_name)}/">{html.escape(source_name)}</a>
<div class="card-meta">{count} article{'s' if count != 1 else ''}</div>
</article>\n"""
    source_index_body += "</div>"
    (source_dir / "index.html").write_text(
        page_shell("Sources", source_index_body, '<a href="/">Home</a> <span>/</span> <span>Sources</span>'),
        encoding="utf-8",
    )

    # 3. Generate about page
    about_dir = DEPLOY_DIR / "about"
    about_dir.mkdir(parents=True, exist_ok=True)
    about_html = generate_about_page(list(sources.keys()))
    (about_dir / "index.html").write_text(about_html, encoding="utf-8")

    # 4. Generate RSS feed
    sorted_all = sorted(articles, key=lambda x: x.get("published", ""), reverse=True)
    rss = generate_rss(sorted_all)
    (DEPLOY_DIR / "feed.xml").write_text(rss, encoding="utf-8")

    print(f"Generated {len(topics)} topic pages, {len(sources)} source pages, about page, and feed.xml")
    return True


if __name__ == "__main__":
    import sys

    ok = main()
    sys.exit(0 if ok else 1)
