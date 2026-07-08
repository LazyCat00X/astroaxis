#!/usr/bin/env python3
"""Generate individual article pages for SEO — one static HTML per article."""
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from hashlib import md5

BASE_DIR = Path(__file__).parent
DEPLOY_DIR = BASE_DIR / "deploy"
ARTICLES_DIR = DEPLOY_DIR / "articles"
SITE_URL = "https://lazycat00x.github.io/astroaxis-site"

def slugify(title):
    """Create URL-safe slug from title."""
    s = title.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[-\s]+', '-', s)
    s = s.strip('-')[:80]
    if not s:
        s = md5(title.encode()).hexdigest()[:12]
    return s

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — AstroAxis</title>
<meta name="description" content="{meta_desc}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<link rel="canonical" href="{canonical_url}" />
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='45' fill='none' stroke='%2322d3ee' stroke-width='3'/%3E%3Ccircle cx='50' cy='50' r='30' fill='none' stroke='%236366f1' stroke-width='2' opacity='0.6'/%3E%3C/svg%3E">
<!-- Open Graph -->
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{meta_desc}" />
<meta property="og:type" content="article" />
<meta property="og:url" content="{canonical_url}" />
<meta property="og:site_name" content="AstroAxis" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{title}" />
<!-- Schema.org NewsArticle -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "{title_escaped}",
  "url": "{canonical_url}",
  "datePublished": "{date_published}",
  "dateModified": "{date_modified}",
  "description": "{meta_desc}",
  "author": {{
    "@type": "Organization",
    "name": "{source}"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "{source}",
    "url": "https://lazycat00x.github.io/astroaxis-site/"
  }},
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "{canonical_url}"
  }},
  "isAccessibleForFree": true
}}
</script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0a0a0f;--bg2:#12121a;--bg3:#1a1a26;--border:#2a2a3a;--text:#e4e4ec;--text2:#8888a0;--accent:#6366f1;--accent2:#818cf8;--cyan:#22d3ee}}
body{{background:var(--bg);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;line-height:1.6;min-height:100vh}}
.container{{max-width:720px;margin:0 auto;padding:0 20px}}
.header{{background:var(--bg2);border-bottom:1px solid var(--border);padding:20px 0;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px)}}
.header-inner{{display:flex;align-items:center;gap:12px}}
.header h1{{font-size:20px;font-weight:700;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header a{{color:var(--text2);text-decoration:none;font-size:14px;margin-left:auto}}
.header a:hover{{color:var(--cyan)}}
.article{{padding:40px 0 60px}}
.article-meta{{display:flex;gap:12px;flex-wrap:wrap;font-size:13px;color:var(--text2);margin-bottom:24px}}
.article-source{{color:var(--accent2);font-weight:600}}
.article-tag{{padding:2px 10px;border-radius:4px;font-size:11px;font-weight:600;background:rgba(99,102,241,0.15);color:var(--accent2)}}
h1.article-title{{font-size:clamp(22px,4vw,36px);font-weight:700;line-height:1.25;margin-bottom:20px;letter-spacing:-0.02em}}
.article-summary{{background:var(--bg3);border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:24px;font-size:14px;line-height:1.7;color:rgba(228,228,236,0.9)}}
.article-summary li{{margin:8px 0;list-style:disc;margin-left:18px}}
.read-more{{display:inline-block;background:var(--accent);color:#fff;padding:12px 28px;border-radius:8px;font-weight:600;text-decoration:none;font-size:15px;transition:background 0.2s;margin-bottom:32px}}
.article-excerpt{{background:var(--bg2);border:1px solid var(--border);border-radius:12px;padding:16px 24px;margin-bottom:24px;font-size:13px;line-height:1.6;color:rgba(228,228,236,0.75)}}
.article-excerpt h3{{font-size:12px;text-transform:uppercase;letter-spacing:0.05em;color:var(--cyan);margin-bottom:8px;font-weight:600}}
.article-excerpt p{{overflow-wrap:break-word}}
.read-more:hover{{background:var(--accent2)}}
.back-link{{display:inline-block;color:var(--cyan);text-decoration:none;font-size:14px;margin-top:32px}}
.related-section{{margin:0 auto 60px;max-width:720px;padding:0 20px}}
.related-section h2{{font-size:16px;font-weight:600;color:var(--text2);margin-bottom:16px;letter-spacing:0.03em}}
.related-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.related-card{{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:14px 16px;text-decoration:none;transition:border-color 0.2s}}
.related-card:hover{{border-color:var(--accent2)}}
.related-card .rc-tag{{font-size:10px;font-weight:600;color:var(--accent2);text-transform:uppercase;letter-spacing:0.05em}}
.related-card .rc-title{{font-size:13px;color:var(--text);margin:4px 0 6px;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.related-card .rc-source{{font-size:11px;color:var(--text2)}}
.back-link:hover{{text-decoration:underline}}
.footer{{text-align:center;padding:24px;color:var(--text2);font-size:12px;border-top:1px solid var(--border)}}
</style>
</head>
<body>
<header class="header">
<div class="container header-inner">
<h1><a href="/" style="background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent">AstroAxis</a></h1>
<a href="/">← Back to Globe</a>
</div>
</header>
<div class="container article">
<div class="article-meta">
<span class="article-source">{source}</span>
<span class="article-tag">{topic}</span>
<time datetime="{date_published}">{time_ago}</time>
</div>
<h1 class="article-title">{title}</h1>
<div class="article-summary">
{summary_html}
</div>
{excerpt_html}
<a class="read-more" href="{article_url}" target="_blank" rel="noopener noreferrer">Read full article →</a>
<p style="font-size:13px;color:var(--text2)">This summary was generated by AI and may contain inaccuracies. Always verify with the original source.</p>
<a class="back-link" href="/">← Back to 3D Globe</a>
</div>
{related_html}
<footer class="footer">
<div>AstroAxis · AI-powered news aggregator · <a href="/" style="color:var(--accent2)">Home</a></div>
</footer>
</body>
</html>"""

def time_ago(pub_str):
    try:
        pub = datetime.fromisoformat(pub_str.replace('Z','+00:00'))
        now = datetime.now(timezone.utc)
        diff = now - pub
        s = int(diff.total_seconds())
        if s < 3600: return f"{max(1, s // 60)} minutes ago"
        elif s < 86400: return f"{s // 3600} hours ago"
        elif s < 172800: return "yesterday"
        else: return f"{s // 86400} days ago"
    except: return ""

def generate():
    # Load news data
    news_path = DEPLOY_DIR / "news-data.json"
    if not news_path.exists():
        print("ERROR: news-data.json not found. Run generate_globe_data.py first.", file=sys.stderr)
        return False
    
    with open(news_path) as f:
        news_data = json.load(f)
    
    articles = news_data.get("articles", [])
    if not articles:
        print("ERROR: No articles in news-data.json", file=sys.stderr)
        return False
    
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    
    # Track slugs to avoid duplicates
    slug_counts = {}
    
    for a in articles:
        title = a.get("title", "Untitled")
        source = a.get("source", "Unknown")
        topic = a.get("topic", "General")
        category = a.get("category", "general")
        lang = a.get("lang", "en")
        published = a.get("published", "")
        summary = a.get("ai_summary", "")
        url = a.get("url", "")
        
        # Skip articles with no content
        if not title or not url:
            continue
        
        # Create unique slug
        base_slug = slugify(title)
        slug = base_slug
        if base_slug in slug_counts:
            slug_counts[base_slug] += 1
            slug = f"{base_slug}-{slug_counts[base_slug]}"
        else:
            slug_counts[base_slug] = 1
        
        canonical_url = f"{SITE_URL}/articles/{slug}.html"
        
        # Clean summary
        summary_clean = summary
        if not summary_clean or summary_clean == "(no content available)":
            # Better fallback: use RSS summary or title-based description
            fallback = a.get("summary", "").strip()
            if fallback and len(fallback) > 20:
                summary_clean = re.sub(r'<[^>]+>', '', fallback)[:300]
            else:
                summary_clean = f"Read {title} on {source}"
        
        # Strip HTML & decode HTML entities for meta description
        meta_desc_raw = re.sub(r'<[^>]+>', '', summary_clean).strip()
        meta_desc_raw = meta_desc_raw.replace('&nbsp;', ' ').replace('&amp;', '&')
        meta_desc_raw = re.sub(r'\s+', ' ', meta_desc_raw)
        meta_desc = meta_desc_raw[:200].replace("\n", " ").replace('"', "'")
        
        summary_html = ""
        # Wrap bullets in <li> if they use •
        if "•" in summary_clean:
            lines = []
            for line in summary_clean.split("\n"):
                stripped = line.strip()
                if stripped.startswith("•"):
                    lines.append(f"<li>{stripped[1:].strip()}</li>")
                elif stripped:
                    lines.append(f"<li>{stripped}</li>")
            if lines:
                summary_html = "<ul>\n" + "\n".join(lines) + "\n</ul>"
        if not summary_html:
            summary_html = meta_desc_raw[:500].replace("\n", "<br>")
        
        meta_desc = meta_desc[:160]
        
        # Generate excerpt from full text (first 200 chars of article body)
        raw_text = a.get("full_text", "") or a.get("summary", "")
        if raw_text and len(raw_text.strip()) > 100:
            excerpt_clean = re.sub(r'<[^>]+>', '', raw_text).strip()
            excerpt_clean = excerpt_clean.replace('&nbsp;', ' ').replace('&amp;', '&')
            excerpt_clean = re.sub(r'\s+', ' ', excerpt_clean)
            excerpt = excerpt_clean[:400]
            # Find last sentence boundary
            if len(excerpt_clean) > 400:
                last_period = max(excerpt.rfind('.'), excerpt.rfind('。'), excerpt.rfind('！'), excerpt.rfind('？'))
                if last_period > 200:
                    excerpt = excerpt_clean[:last_period+1]
            excerpt_html = f'<div class="article-excerpt"><h3>原文節錄</h3><p>{excerpt}</p></div>'
        else:
            excerpt_html = ""
        
        # Generate related articles (same topic, exclude self)
        related = []
        for other in articles:
            if len(related) >= 3:
                break
            if other.get("url") == url:
                continue
            if other.get("topic") == topic and other.get("title"):
                rel_slug = slugify(other.get("title", ""))
                related.append({
                    "slug": rel_slug,
                    "title": other.get("title", ""),
                    "source": other.get("source", ""),
                    "topic": other.get("topic", ""),
                })
        if related:
            items = "".join(
                f'<a class="related-card" href="/articles/{r["slug"]}.html">'
                f'<div class="rc-tag">{r["topic"]}</div>'
                f'<div class="rc-title">{r["title"]}</div>'
                f'<div class="rc-source">{r["source"]}</div></a>'
                for r in related
            )
            related_html = f'<div class="related-section"><h2>相關新聞</h2><div class="related-grid">{items}</div></div>'
        else:
            related_html = ""
        
        article_html = ARTICLE_TEMPLATE.format(
            title=title,
            title_escaped=title.replace('"', '\\"'),
            source=source,
            topic=topic,
            lang=lang if lang in ('en','zh','ja','ko') else 'en',
            date_published=published or datetime.now(timezone.utc).isoformat(),
            date_modified=published or datetime.now(timezone.utc).isoformat(),
            time_ago=time_ago(published),
            meta_desc=meta_desc,
            canonical_url=canonical_url,
            article_url=url,
            summary_html=summary_html,
            excerpt_html=excerpt_html,
            related_html=related_html,
        )
        
        filepath = ARTICLES_DIR / f"{slug}.html"
        with open(filepath, "w") as f:
            f.write(article_html)
        count += 1
    
    print(f"Generated {count} article pages in {ARTICLES_DIR}")
    return True

if __name__ == "__main__":
    success = generate()
    sys.exit(0 if success else 1)