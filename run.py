#!/usr/bin/env python3
"""Main pipeline orchestrator — crawl → summarize → generate site."""

import logging
import sys
import time
from pathlib import Path

import crawler
import summarizer
import generate_globe_data
import generate_articles
import generate_content_pages
import generate_sitemap

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("pipeline")


def run():
    log.info("=== AstroAxis Pipeline Start ===")

    # Step 1: Crawl
    log.info("--- Step 1: Crawling feeds ---")
    new_count = crawler.crawl()
    log.info("Crawled %d new articles", new_count)

    if new_count == 0:
        log.info("No new articles, checking if summarization needed")

    # Step 2: Summarize
    log.info("--- Step 2: Summarizing ---")
    summarized = summarizer.run()
    log.info("Summarized %d articles", summarized)

    # Step 3: Generate deploy files
    log.info("--- Step 3: Generating deploy files ---")
    generate_globe_data.main()
    generate_articles.generate()
    generate_content_pages.main()
    generate_sitemap.generate_sitemap()

    log.info("=== Pipeline Complete ===")
    return True


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)