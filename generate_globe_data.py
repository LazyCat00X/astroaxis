#!/usr/bin/env python3
"""Generate deploy/index.html + data files for AstroAxis.

globe.html now uses dynamic fetch('news-data.json') and fetch('timeline-data.json')
instead of inline injection. This script writes those JSON files into deploy/ and
copies globe.html as deploy/index.html.
"""
import json, re, sys
from pathlib import Path

from config import BASE_DIR, DATA_DIR, DEPLOY_DIR, SITE_URL, load_articles
SRC_LOCS_PATHS = [
    DATA_DIR / "source_locs.json",
    Path("/tmp/source_locs.json"),
]

# Default source locations (fallback if /tmp file missing)
DEFAULT_SOURCE_LOCS = {
    "CoinDesk": [40.7, -74.0, "New York"],
    "CoinTelegraph": [51.5, -0.1, "London"],
    "The Block": [40.7, -74.0, "New York"],
    "Decrypt": [37.8, -122.4, "San Francisco"],
    "Blockworks": [40.7, -74.0, "New York"],
    "Bloomberg Crypto": [40.7, -74.0, "New York"],
    "Bloomberg": [40.7, -74.0, "New York"],
    "CNBC": [40.9, -73.9, "Englewood Cliffs"],
    "WSJ Markets": [40.7, -74.0, "New York"],
    "FT Tech": [51.5, -0.1, "London"],
    "TechCrunch": [37.8, -122.4, "San Francisco"],
    "ArsTechnica": [42.4, -71.1, "Boston"],
    "Wired": [37.8, -122.4, "San Francisco"],
    "Chainlink (Chinese)": [31.2, 121.5, "Shanghai"],
    "Unchained": [40.7, -74.0, "New York"],
    "DL News": [51.5, -0.1, "London"],
    "Bankless": [37.8, -122.4, "San Francisco"],
    "Reuters": [51.5, -0.1, "London"],
    "BBC World": [51.5, -0.1, "London"],
    "Reuters World": [51.5, -0.1, "London"],
    "AP News": [40.7, -74.0, "New York"],
    "Al Jazeera": [25.3, 51.5, "Doha"],
    "NPR": [38.9, -77.0, "Washington DC"],
    "Nikkei Asia": [35.7, 139.7, "Tokyo"],
    "SCMP": [22.3, 114.2, "Hong Kong"],
    "The Guardian": [51.5, -0.1, "London"],
    "New York Times": [40.7, -74.0, "New York"],
    "Washington Post": [38.9, -77.0, "Washington DC"],
    "Time": [40.7, -74.0, "New York"],
    "The Economist": [51.5, -0.1, "London"],
    "動區動趨 (BlockTempo)": [25.0, 121.5, "Taipei"],
    "區塊客 (Blockcast)": [25.0, 121.5, "Taipei"],
    "科技新報": [25.0, 121.5, "Taipei"],
    "鉅亨網": [25.0, 121.5, "Taipei"],
    "香港經濟日報": [22.3, 114.2, "Hong Kong"],
}


def load_source_locs():
    """Load source locations, with fallback."""
    for path in SRC_LOCS_PATHS:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    # Try extracting from existing deploy/index.html
    deploy_html = DEPLOY_DIR / "index.html"
    if deploy_html.exists():
        with open(deploy_html) as f:
            html = f.read()
        m = re.search(r'"sourceLocations":(\{[^}]+\})', html)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    print("WARNING: Using default source locations (no /tmp/source_locs.json)", file=sys.stderr)
    return DEFAULT_SOURCE_LOCS


def load_articles():
    with open(BASE_DIR / "data" / "articles.json") as f:
        return json.load(f)


def main():
    articles = load_articles()

    # Sort newest first
    articles.sort(key=lambda a: a.get("published", ""), reverse=True)

    # Build article payload — include all articles, summarized or not
    articles_out = []
    for a in articles:
        summary = a.get("ai_summary", "") or a.get("summary", "")
        articles_out.append({
            "url": a["url"],
            "title": a["title"],
            "source": a["source"],
            "topic": a.get("topic", "General"),
            "category": a.get("category", "general"),
            "lang": a.get("lang", "en"),
            "published": a.get("published", ""),
            "ai_summary": summary,
            "summaries": a.get("summaries", {}),
        })

    # Globe payload: lightweight (no summaries), all articles for full globe coverage
    globe_articles = [
        {
            "url": a["url"],
            "title": a["title"],
            "source": a["source"],
            "topic": a["topic"],
            "published": a["published"],
        }
        for a in articles_out
    ]

    source_locs = load_source_locs()
    news_data = {
        "articles": articles_out,
        "globeArticles": globe_articles,
        "sourceLocations": source_locs,
    }

    # Write news-data.json to deploy directory
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    news_json_path = DEPLOY_DIR / "news-data.json"
    with open(news_json_path, "w") as f:
        json.dump(news_data, f, ensure_ascii=False)
    print(f"Wrote {len(articles_out)} articles to {news_json_path}")

    # Write timeline-data.json: use full timeline.json (all years), fallback to timeline_recent.json
    timeline_full = DATA_DIR / "timeline.json"
    timeline_recent = DATA_DIR / "timeline_recent.json"
    timeline_source = timeline_full if timeline_full.exists() else timeline_recent
    if timeline_source.exists():
        with open(timeline_source) as f:
            timeline_data = json.load(f)
        tl_path = DEPLOY_DIR / "timeline-data.json"
        with open(tl_path, "w") as f:
            json.dump(timeline_data, f, ensure_ascii=False)
        total_events = sum(len(v) for v in timeline_data.values())
        print(f"Wrote timeline: {total_events} events, {len(timeline_data)} years (from {timeline_source.name})")
    else:
        print("WARNING: no timeline data found, skipping timeline", file=sys.stderr)

    # Copy globe.html as deploy/index.html (no inline injection needed)
    with open(BASE_DIR / "globe.html") as f:
        html = f.read()
    index_path = DEPLOY_DIR / "index.html"
    with open(index_path, "w") as f:
        f.write(html)
    
    # Now inject dynamic meta into the copied index.html
    # Replace <title> and <meta name="description"> with dynamic content
    latest = articles_out[:5]
    headlines = [a["title"] for a in latest if a["title"]]
    if headlines:
        first = headlines[0][:100]
        rest = " · ".join(h[:60] for h in headlines[1:4])
        new_title = f"{first} — AstroAxis"
        new_desc = f"{rest} — AI-powered world news aggregator with 3D globe, AI summaries, and real-time news"
        if rest:
            new_title = f"{first} · {rest} — AstroAxis"
        
        with open(index_path) as f:
            html = f.read()
        html = html.replace(
            '<title>AstroAxis — AI-powered world news aggregator</title>',
            f"<title>{new_title[:120]}</title>"
        )
        html = html.replace(
            'content="AstroAxis — AI-powered world news aggregator with 3D globe, AI summaries, and real-time crypto/finance news"',
            f'content="{new_desc[:200]}"'
        )
        with open(index_path, "w") as f:
            f.write(html)
    
    print(f"Copied globe.html -> {index_path}")

    # Write robots.txt with Sitemap directive for Google
    robots_path = DEPLOY_DIR / "robots.txt"
    with open(robots_path, "w") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: https://lazycat00x.github.io/astroaxis-site/sitemap.xml\n")
    print(f"Wrote {robots_path}")


if __name__ == "__main__":
    main()
