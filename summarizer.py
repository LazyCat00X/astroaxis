#!/usr/bin/env python3
"""LLM summarizer — summarize + translate articles to Traditional Chinese."""

import json
import logging
import os
import time
from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("summarizer")

# DeepSeek API
API_URL = "https://api.deepseek.com/v1/chat/completions"

# Read API key from .env
API_KEY = ""
env_paths = [
    Path(__file__).parent.parent.parent / ".hermes-luna" / ".env",
    Path.home() / ".hermes-luna" / ".env",
]
for env_file in env_paths:
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("DEEPSEEK_API_KEY="):
                    API_KEY = line.split("=", 1)[1].strip()
                    break
    if API_KEY:
        break

MODEL = "deepseek-v4-flash"
MAX_ARTICLES_PER_RUN = int(os.environ.get("MAX_ARTICLES_PER_RUN", "30"))

SYSTEM_PROMPT = """You are a professional financial news translator and summarizer. Your task:

1. Read the article title and content
2. Write a concise 3-5 bullet point summary in Traditional Chinese (香港繁體)
3. Keep each bullet point under 80 characters (Chinese characters)
4. Focus on key facts: what happened, why it matters, market impact
5. Be objective and factual — no editorializing
6. If the article is in Chinese, still summarize in Traditional Chinese
7. Include the original title in English (if English) or Chinese (if Chinese)

Output format:
Original Title: <original title>
Summary:
• <point 1>
• <point 2>
• <point 3>
"""


def load_articles():
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE) as f:
            return json.load(f)
    return []


def save_articles(articles):
    ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTICLES_FILE, "w") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def summarize_text(title, text, max_retries=2):
    """Call DeepSeek API to summarize + translate."""
    if not API_KEY:
        log.error("No API key found")
        return None

    # Truncate text to avoid token limits
    if len(text) > 6000:
        text = text[:6000] + "..."

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Title: {title}\n\nContent:\n{text}"}
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip()
        except requests.exceptions.Timeout:
            log.warning("Timeout on attempt %d/%d", attempt + 1, max_retries)
            if attempt < max_retries - 1:
                time.sleep(5)
        except Exception as e:
            log.error("API error: %s", e)
            if attempt < max_retries - 1:
                time.sleep(5)
    return None


def run():
    articles = load_articles()
    if not articles:
        log.info("No articles to summarize")
        return 0

    # Find unsummarized articles, prioritize recent ones
    pending = [a for a in articles if not a.get("summarized")]
    pending.sort(key=lambda a: a.get("published", ""), reverse=True)
    pending = pending[:MAX_ARTICLES_PER_RUN]

    if not pending:
        log.info("All articles already summarized")
        return 0

    count = 0
    for article in pending:
        text = article.get("full_text", "") or article.get("summary", "")
        title = article.get("title", "")

        if not text:
            log.info("No text for: %s", title)
            article["summarized"] = True
            article["ai_summary"] = "(no content available)"
            continue

        log.info("Summarizing: %s", title[:60])
        result = summarize_text(title, text)

        if result:
            article["ai_summary"] = result
            article["summarized"] = True
            count += 1
        else:
            log.warning("Failed to summarize: %s", title[:60])

        # Rate limit: 1 request every 2 seconds
        time.sleep(2)

    save_articles(articles)
    log.info("Summarized %d articles", count)
    return count


if __name__ == "__main__":
    run()
