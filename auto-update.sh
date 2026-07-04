#!/bin/bash
# AstroAxis auto-update — crawl, summarize, generate, deploy
# Repo structure (split):
#   origin  = LazyCat00X/astroaxis        (source code)
#   astroaxis-site = deploy target (GitHub Pages)
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
source .venv/bin/activate 2>/dev/null || true

echo "=== AstroAxis Auto-Update $(date -u) ==="

# Step 1: Fetch timeline historical events (daily)
python3 timeline_fetcher.py 2>&1 | tail -2

# Step 2: Crawl new articles
python3 crawler.py 2>&1 | tail -3

# Step 3: Summarize (up to 30 per run)
source ~/.hermes-luna/.env 2>/dev/null || true
MAX_ARTICLES_PER_RUN=30 python3 summarizer.py 2>&1 | tail -3

# Step 4: Generate fresh globe data for deploy
python3 generate_globe_data.py

# Step 5: Generate sitemap for SEO
python3 generate_sitemap.py

# Step 6: Push source code to astroaxis repo
git add globe.html generate_globe_data.py crawler.py summarizer.py run.py \
    site_generator.py timeline_fetcher.py feeds.yaml auto-update.sh \
    requirements.txt .gitignore data/ 2>/dev/null || true
if ! git diff --cached --quiet; then
    git commit -m "auto: source update $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    git push origin main 2>&1 || echo "Source push failed (non-fatal)"
    echo "Source pushed."
fi

# Step 7: Deploy to GitHub Pages (astroaxis-site repo)
DEPLOY_DIR="/tmp/astroaxis-site-deploy"
if [ ! -d "$DEPLOY_DIR/.git" ]; then
    git clone https://github.com/LazyCat00X/astroaxis-site.git "$DEPLOY_DIR"
fi
cd "$DEPLOY_DIR"
git pull origin main 2>&1 || true

# Copy generated files
cp /home/kevyn/projects/astroaxis/deploy/index.html .
cp /home/kevyn/projects/astroaxis/deploy/news-data.json .
cp /home/kevyn/projects/astroaxis/deploy/timeline-data.json .
cp /home/kevyn/projects/astroaxis/deploy/og-image.png . 2>/dev/null || true
cp /home/kevyn/projects/astroaxis/deploy/robots.txt . 2>/dev/null || true
cp /home/kevyn/projects/astroaxis/sitemap.xml . 2>/dev/null || true

git add -A
if ! git diff --cached --quiet; then
    git -c user.email="kevyn@users.noreply.github.com" -c user.name="LazyCat00X" \
        commit -m "auto: deploy update $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    git push origin main 2>&1
    echo "Deployed to GitHub Pages."
else
    echo "No changes to deploy."
fi

echo "=== Done $(date -u) ==="
