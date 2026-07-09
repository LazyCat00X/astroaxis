#!/usr/bin/env python3
"""Shared configuration for AstroAxis generators."""
import re
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DEPLOY_DIR = BASE_DIR / "deploy"
SITE_URL = "https://lazycat00x.github.io/astroaxis-site"
SITE_NAME = "AstroAxis"
ARTICLES_SOURCE = DATA_DIR / "articles.json"


def slugify(text: str, max_len: int = 80) -> str:
    """Create URL-safe slug from text. Consistent across all generators."""
    if not text:
        return "unknown"
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    s = s.strip("-")[:max_len]
    if not s:
        s = hashlib.md5(text.encode()).hexdigest()[:12]
    return s


def load_articles(source_path=None):
    """Load articles from the canonical source (data/articles.json)."""
    p = source_path or ARTICLES_SOURCE
    if p.exists():
        import json
        with open(p) as f:
            return json.load(f)
    return []