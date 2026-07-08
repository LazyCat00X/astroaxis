#!/usr/bin/env python3
"""AstroAxis summarizer v2: single-pass summarize + translate, quality-gated."""
import json, logging, os, time
from pathlib import Path
import requests

DATA_DIR = Path(__file__).parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"
log = logging.getLogger("pipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

API_URL = "https://models.inference.ai.azure.com/chat/completions"
MODEL = "gpt-4o-mini"
MAX_PER_RUN = int(os.environ.get("MAX_ARTICLES_PER_RUN", "30"))
RATE_LIMIT_DELAY = 1.0  # GitHub Models allows 20k req/min, but safe at 1s

def get_api_key():
    KEY = ""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("MODELS_API_TOKEN="):
                KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("GITHUB_MODELS_TOKEN="):
                KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not KEY:
        KEY = os.environ.get("MODELS_API_TOKEN", "") or os.environ.get("GITHUB_MODELS_TOKEN", "")
    return KEY

API_KEY = get_api_key()

def call(system, user, temp=0.3, max_tok=800):
    if not API_KEY:
        log.error("No API key found")
        return None
    payload = {
        "model": MODEL,
        "temperature": temp,
        "max_tokens": max_tok,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=60)
            if r.status_code == 429:
                wait = 5 * (attempt + 1)
                log.warning("Rate limited, waiting %ds", wait)
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if content and content.strip():
                return content.strip()
            log.warning("Empty content (attempt %d/3)", attempt + 1)
            time.sleep(2)
        except Exception as e:
            log.warning("API error (attempt %d/3): %s", attempt + 1, e)
            time.sleep(3)
    return None

# Single-pass: summarize + translate in one call (saves 2 API calls per article)
SUMMARY_PROMPT = """You are a neutral news editor. Read the article and write a concise summary.

Rules:
- 3-4 bullet points (use • prefix)
- Strictly factual, no opinions, no loaded language
- Cover: who, what, when, where, why — only confirmed facts, NO speculation or prediction
- Output in Traditional Chinese (繁體中文，使用香港常用用語)
- Use 特朗普 (not 川普), 網絡 (not 網路), 資訊 (not 資訊保持), 警方 (not 警察一般)
- Output ONLY the bullets, no preamble

Example output:
• 蘋果公司公佈2024年Q3營收達815億美元，同比增長5%
• iPhone銷量佔總營收的49%，服務業務增長14%
• CEO庫克表示AI功能將推動下一波增長
• 分析師預計Q4前景樂觀，但中國市場仍面臨挑戰"""

def summarize_article(title, text):
    t = text[:3000] if text else ""
    if not t.strip():
        return None
    result = call(SUMMARY_PROMPT, f"Title: {title}\n\n{t}", 0.3, 400)
    if not result:
        return None
    # Quality check
    result = result.strip()
    if len(result) < 30:
        log.warning("Summary too short (%d chars), discarding", len(result))
        return None
    if "•" not in result:
        # Add bullets if missing
        lines = [l.strip() for l in result.split("\n") if l.strip() and not l.strip().startswith("#")]
        result = "\n".join(f"• {l}" for l in lines[:4])
    return result

def translate_to_langs(zh_summary, title):
    """Translate zh-HK summary to en, zh-CN, ja, ko in one call."""
    result = call(
        "Translate the following news summary into 4 languages. Keep bullet format.\n\n[EN]\n[zh-CN]\n[JA]\n[KO]\n\nOutput ALL 4, each section prefixed with [XX].",
        f"Title: {title}\n\nSummary:\n{zh_summary}",
        0.2, 600
    )
    if not result:
        return {}
    langs = {}
    cur = None
    for line in result.split("\n"):
        ls = line.strip()
        if ls.startswith("[EN]"): cur = "en"
        elif ls.startswith("[zh-CN]"): cur = "zh-CN"
        elif ls.startswith("[JA]"): cur = "ja"
        elif ls.startswith("[KO]"): cur = "ko"
        elif cur and ls:
            langs[cur] = (langs.get(cur, "") + "\n" + ls).strip()
    return langs

def load_articles():
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE) as f:
            return json.load(f)
    return []

def save_articles(articles):
    ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTICLES_FILE, "w") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

def run():
    articles = load_articles()
    if not articles:
        return 0

    # Reset bad summaries — expand detection
    reset_count = 0
    for a in articles:
        s = a.get("ai_summary", "")
        title = a.get("title", "").lower()
        # Known bad patterns: wrong content, placeholders, too-short
        bad_patterns = ["(neutralize failed)", "(no content)", "浙江省宣傳部門"]
        is_bad = any(bad in s for bad in bad_patterns) or (s.startswith("[Skipped:") and len(s) < 30)
        # Also reset if summary is way too short or doesn't reference article lang
        if not is_bad and s and len(s) < 30:
            is_bad = True
        if is_bad:
            a["summarized"] = False
            a["ai_summary"] = ""
            a["summaries"] = {}
            reset_count += 1
    if reset_count:
        log.info("Reset %d bad summaries for reprocessing", reset_count)

    pending = [a for a in articles if not a.get("summarized")]
    pending.sort(key=lambda a: a.get("published", ""), reverse=True)
    pending = pending[:MAX_PER_RUN]
    if not pending:
        log.info("All done, nothing to summarize")
        return 0

    count = 0
    for art in pending:
        text = art.get("full_text", "") or art.get("summary", "")
        title = art.get("title", "")
        if not text or len(text.strip()) < 20:
            art["summarized"] = True
            art["ai_summary"] = "• 此文章內容不足，無法生成摘要"
            art["summaries"] = {"zh-HK": art["ai_summary"]}
            save_articles(articles)
            count += 1
            continue

        log.info("── %s ──", title[:50])

        # Step 1: Summarize (single pass, zh-HK)
        zh_summary = summarize_article(title, text)
        if not zh_summary:
            log.warning("  Summary failed, skipping (will retry next run)")
            continue
        log.info("  [OK] Summary (%d chars)", len(zh_summary))

        # Step 2: Translate to other languages
        time.sleep(RATE_LIMIT_DELAY)
        other_langs = translate_to_langs(zh_summary, title)
        if other_langs:
            log.info("  [OK] Translations: %s", list(other_langs.keys()))

        # Save
        art["summarized"] = True
        art["ai_summary"] = zh_summary
        art["summaries"] = {"zh-HK": zh_summary, **other_langs}
        art.pop("needs_multilang", None)
        count += 1

        # Save after each article (crash-safe)
        save_articles(articles)
        time.sleep(RATE_LIMIT_DELAY)

    log.info("Done: %d articles", count)
    return count

if __name__ == "__main__":
    run()
