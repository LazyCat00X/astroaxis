#!/bin/bash
# ChainLens auto-update — crawl, summarize, deploy globe with fresh data
set -euo pipefail

cd /home/kevyn/projects/news-aggregator
source .venv/bin/activate

echo "=== ChainLens Auto-Update $(date -u) ==="

# Step 1: Crawl new articles
python3 crawler.py 2>&1 | tail -3

# Step 2: Summarize (up to 15 per run to stay fast)
MAX_ARTICLES_PER_RUN=15 python3 summarizer.py 2>&1 | tail -3

# Step 3: Generate fresh site data for globe
python3 -c "
import json, re
from pathlib import Path

# Read articles
with open('data/articles.json') as f:
    articles = json.load(f)

# Filter to summarized articles only
summarized = [a for a in articles if a.get('summarized') and a.get('ai_summary')]
# Sort by published, newest first
summarized.sort(key=lambda a: a.get('published', ''), reverse=True)
# Keep top 100
summarized = summarized[:100]

# Read current globe.html
with open('globe.html') as f:
    html = f.read()

# Read globe.html, replace the NEWS_DATA section
# Find the NEWS_DATA assignment and replace it
old = re.search(r'const NEWS_DATA = \{.*?\};', html, re.DOTALL)
if old:
    # Build minimal article data
    articles_out = []
    for a in summarized:
        articles_out.append({
            'url': a['url'],
            'title': a['title'],
            'source': a['source'],
            'topic': a.get('topic', 'General'),
            'category': a.get('category', 'general'),
            'published': a.get('published', ''),
            'ai_summary': a.get('ai_summary', '')
        })
    
    with open('/tmp/source_locs.json') as f:
        source_locs = json.load(f)
    
    news_data = json.dumps({'articles': articles_out, 'sourceLocations': source_locs}, ensure_ascii=False)
    html = html.replace(old.group(0), f'const NEWS_DATA = {news_data};')
    
    with open('deploy/index.html', 'w') as f:
        f.write(html)
    
    print(f'Generated globe with {len(articles_out)} articles')
else:
    print('ERROR: Could not find NEWS_DATA in globe.html')
    exit(1)
"

# Step 4: Deploy to GitHub Pages
cd deploy
git add index.html
if git diff --cached --quiet; then
    echo "No changes to deploy."
else
    git commit -m "Update $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    git push origin main 2>&1
    echo "Deployed to GitHub Pages."
fi

echo "=== Done $(date -u) ==="
