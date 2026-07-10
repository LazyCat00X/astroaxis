#!/usr/bin/env bash
# AstroAxis local dev server — run full pipeline + serve
# Usage: ./dev.sh          # generate + serve
#        ./dev.sh --watch  # generate + serve + watch for changes

set -e

cd "$(dirname "$0")"

echo "=== AstroAxis Local Dev Server ==="

# Step 1: Generate data files
echo "→ Generating globe data..."
python3 generate_globe_data.py

echo "→ Generating content pages..."
python3 generate_content_pages.py

echo "→ Generating article pages..."
python3 generate_articles.py

echo "→ Generating sitemap..."
python3 generate_sitemap.py

# Step 2: Start HTTP server
PORT=${PORT:-8080}
echo "→ Starting server at http://localhost:$PORT"
echo "  Press Ctrl+C to stop"

if [ "$1" = "--watch" ]; then
  # Watch mode: regenerate on changes
  python3 -c "
import subprocess, sys, time
from pathlib import Path
watched = ['globe.html', 'generate_globe_data.py', 'generate_content_pages.py', 'generate_articles.py', 'generate_sitemap.py', 'feeds.yaml', 'crawler.py', 'summarizer.py']
last = {p: Path(p).stat().st_mtime for p in watched if Path(p).exists()}
while True:
  for p in watched:
    f = Path(p)
    if f.exists() and f.stat().st_mtime != last.get(p, 0):
      print(f'  ↻ {p} changed, regenerating...')
      last[p] = f.stat().st_mtime
      subprocess.run([sys.executable, 'generate_globe_data.py'], cwd='.')
      subprocess.run([sys.executable, 'generate_content_pages.py'], cwd='.')
      subprocess.run([sys.executable, 'generate_articles.py'], cwd='.')
      subprocess.run([sys.executable, 'generate_sitemap.py'], cwd='.')
      print('  ✓ Regenerated')
      break
  time.sleep(1)
  " &
  sleep 1
fi

python3 -m http.server $PORT --directory deploy