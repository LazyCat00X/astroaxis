#!/usr/bin/env python3
"""Force-reset ALL article summaries so they get re-summarized with new prompt."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"

def main():
    if not ARTICLES_FILE.exists():
        print("No articles.json found")
        return
    
    with open(ARTICLES_FILE) as f:
        articles = json.load(f)
    
    reset = 0
    for a in articles:
        if a.get("summarized") or a.get("ai_summary"):
            a["summarized"] = False
            a["ai_summary"] = ""
            a["summaries"] = {}
            reset += 1
    
    with open(ARTICLES_FILE, "w") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"Reset {reset}/{len(articles)} articles — will re-summarize on next pipeline run")

if __name__ == "__main__":
    main()