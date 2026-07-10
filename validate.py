#!/usr/bin/env python3
"""Pre-push validation — run full pipeline and verify output before push."""
import json, sys, subprocess, os
from pathlib import Path

BASE = Path(__file__).parent
errors = 0

def step(name, cmd):
    global errors
    print(f"  → {name}...", end=" ")
    r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"FAIL\n{r.stderr[:500]}")
        errors += 1
    else:
        print("OK")

print("=== Pre-Push Validation ===")

# 1. Regenerate
step("globe data", ["python3", "generate_globe_data.py"])
step("content pages", ["python3", "generate_content_pages.py"])
step("article pages", ["python3", "generate_articles.py"])
step("sitemap", ["python3", "generate_sitemap.py"])

# 2. Verify outputs exist
for f in ["deploy/index.html", "deploy/news-data.json", "deploy/sitemap.xml", "deploy/topic/index.html", "deploy/source/index.html", "deploy/feed.xml"]:
    p = BASE / f
    if not p.exists():
        print(f"  ✗ MISSING: {f}")
        errors += 1

# 3. Verify sitemap is valid XML with URLs
try:
    import xml.etree.ElementTree as ET
    tree = ET.parse(BASE / "deploy/sitemap.xml")
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    urls = tree.getroot().findall(f"{ns}url")
    if len(urls) < 100:
        print(f"  ✗ Sitemap only has {len(urls)} URLs (expected 100+)")
        errors += 1
    else:
        print(f"  → Sitemap: {len(urls)} URLs OK")
except Exception as e:
    print(f"  ✗ Sitemap invalid: {e}")
    errors += 1

# 4. Verify news-data has articles
with open(BASE / "deploy/news-data.json") as f:
    nd = json.load(f)
    articles = nd.get("articles", [])
    if len(articles) < 100:
        print(f"  ✗ Only {len(articles)} articles in news-data.json")
        errors += 1
    else:
        print(f"  → {len(articles)} articles OK")
    globe = nd.get("globeArticles", [])
    print(f"  → {len(globe)} globe markers")

# 5. Verify index.html has key JS elements
html = (BASE / "deploy/index.html").read_text()
checks = ["buildMarkers", "animate", "raycaster", "renderFeed", "renderTimeline"]
for c in checks:
    if c not in html:
        print(f"  ✗ Missing JS function: {c}")
        errors += 1

# 6. Check robots.txt
robots = (BASE / "deploy/robots.txt").read_text()
if "Sitemap" not in robots:
    print("  ✗ robots.txt missing Sitemap directive")
    errors += 1
else:
    print("  → robots.txt OK")

# 7. Basic sanity checks on globe.html
print(f"  → globe.html size: {len(html)} chars OK")
# Check for balanced function braces (quick integrity check)
open_braces = html.count('{')
close_braces = html.count('}')
if abs(open_braces - close_braces) > 5:
    print(f"  ✗ Unbalanced braces: {open_braces} open, {close_braces} close")
    errors += 1
else:
    print("  → Brace balance OK")

print()
if errors:
    print(f"❌ {errors} error(s) found. Fix before push.")
    sys.exit(1)
else:
    print("✅ All checks passed. Ready to push.")
    sys.exit(0)