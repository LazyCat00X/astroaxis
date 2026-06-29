#!/usr/bin/env python3
"""Generate globe.html with fresh article data for AstroAxis deploy."""
import json, re, os, sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
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
    deploy_html = BASE_DIR / "deploy" / "index.html"
    if deploy_html.exists():
        with open(deploy_html) as f:
            html = f.read()
        m = re.search(r'"sourceLocations":(\{[^}]+?\})', html)
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

    # Filter to summarized only
    summarized = [a for a in articles if a.get("summarized") and a.get("ai_summary")]
    summarized.sort(key=lambda a: a.get("published", ""), reverse=True)
    summarized = summarized[:100]

    # Read globe template
    with open(BASE_DIR / "globe.html") as f:
        html = f.read()

    # Find NEWS_DATA using brace counting (handles nested {})
    marker = "const NEWS_DATA = "
    start = html.find(marker)
    if start == -1:
        print("ERROR: Could not find NEWS_DATA in globe.html", file=sys.stderr)
        sys.exit(1)
    data_start = html.index("{", start)
    depth = 0
    end = data_start
    for ch in html[data_start:]:
        end += 1
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if depth == 0:
            break
    old_text = html[start:end]

    # Build article payload
    articles_out = []
    for a in summarized:
        articles_out.append({
            "url": a["url"],
            "title": a["title"],
            "source": a["source"],
            "topic": a.get("topic", "General"),
            "category": a.get("category", "general"),
            "published": a.get("published", ""),
            "ai_summary": a.get("ai_summary", ""),
            "summaries": a.get("summaries", {}),
        })

    source_locs = load_source_locs()
    news_data = json.dumps(
        {"articles": articles_out, "sourceLocations": source_locs},
        ensure_ascii=False,
    )
    html = html.replace(old_text, f"const NEWS_DATA = {news_data};")

    # ── Inject timeline data (recent 5 years for speed) ──
    timeline_file = DATA_DIR / "timeline_recent.json"
    if timeline_file.exists():
        with open(timeline_file) as f:
            timeline_data = json.load(f)
        timeline_json = json.dumps(timeline_data, ensure_ascii=False)
        # Replace hardcoded timelineData using brace counting
        tl_marker = "const timelineData = "
        tl_start = html.find(tl_marker)
        if tl_start >= 0:
            tl_brace = html.index("{", tl_start)
            depth = 0
            tl_end = tl_brace
            for ch in html[tl_brace:]:
                tl_end += 1
                if ch == "{": depth += 1
                elif ch == "}": depth -= 1
                if depth == 0: break
            html = html.replace(html[tl_start:tl_end], f"{tl_marker}{timeline_json}")
            total_events = sum(len(v) for v in timeline_data.values())
            print(f"Injected timeline: {total_events} events, {len(timeline_data)} years")
        else:
            print("WARNING: Could not find timelineData in globe.html", file=sys.stderr)
    else:
        print("WARNING: data/timeline.json not found, using hardcoded timeline", file=sys.stderr)

    with open(BASE_DIR / "deploy" / "index.html", "w") as f:
        f.write(html)

    print(f"Generated globe with {len(articles_out)} articles, {len(source_locs)} source locations")


if __name__ == "__main__":
    main()
