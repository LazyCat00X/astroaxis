#!/usr/bin/env python3
"""Phase 3: error handling, accessibility, SEO."""

path = '/home/kevyn/projects/astroaxis/globe.html'

with open(path) as f:
    content = f.read()

changes = []

# ═══════════════════════════════════════════
# 1. ERROR HANDLING — Three.js fail, structured logging
# ═══════════════════════════════════════════

# 1a. Three.js load failure graceful degradation
old_body = '<body tabindex="-1">'
new_body = '''<body tabindex="-1">
<noscript>
  <div style="background:#03040c;color:#eef7ff;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:Inter,sans-serif;text-align:center;padding:40px">
    <div>
      <div style="font-size:48px;margin-bottom:16px">🌍</div>
      <h1 style="font-size:24px;margin-bottom:8px">AstroAxis</h1>
      <p style="color:rgba(238,247,255,.6)">JavaScript is required to view the 3D globe and news feed.</p>
      <p style="color:rgba(136,146,182,.5);font-size:13px;margin-top:12px">Please enable JavaScript in your browser settings.</p>
    </div>
  </div>
</noscript>'''
content = content.replace(old_body, new_body)
changes.append('noscript fallback')

# 1b. Three.js CDN failure detection (after the Three.js script tags)
old_three_check = '    <script>\n    // ── View switching ──'
new_three_check = '''    <script>
    // ── Three.js load check ──
    if (typeof THREE === 'undefined') {
      document.body.innerHTML = `<div style="background:#03040c;color:#eef7ff;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:Inter,sans-serif;text-align:center;padding:40px">
        <div>
          <div style="font-size:48px;margin-bottom:16px">⚠️</div>
          <h1 style="font-size:22px;margin-bottom:8px">Failed to load 3D engine</h1>
          <p style="color:rgba(238,247,255,.6);max-width:400px;line-height:1.6">The 3D globe library (Three.js) could not be loaded. This may be due to a network issue or content blocker.</p>
          <p style="color:rgba(136,146,182,.5);font-size:13px;margin-top:12px">Try disabling your ad blocker or refreshing the page.</p>
        </div>
      </div>`;
      throw new Error('Three.js failed to load');
    }

    // ── Structured error logger ──
    const _errors = [];
    window._logError = function(category, msg, detail) {
      const entry = { time: new Date().toISOString(), category, msg, detail: String(detail||'').slice(0,200) };
      _errors.push(entry);
      if (_errors.length > 50) _errors.shift();
      console.warn('[AstroAxis:'+category+']', msg, detail||'');
    };
    window.addEventListener('error', (e) => {
      window._logError('uncaught', e.message, e.filename + ':' + e.lineno);
    });
    window.addEventListener('unhandledrejection', (e) => {
      window._logError('promise', String(e.reason).slice(0,100));
    });

    // ── View switching ──'''
content = content.replace(old_three_check, new_three_check)
changes.append('Three.js fail + error logger')


# ═══════════════════════════════════════════
# 2. ACCESSIBILITY
# ═══════════════════════════════════════════

# 2a. Skip-to-content link (first element after body)
old_skip = '<nav class="top-nav"'
new_skip = '''<a href="#globe-view" class="skip-link" aria-label="Skip to main content">Skip to content</a>
<nav class="top-nav"'''
content = content.replace(old_skip, new_skip)
changes.append('skip-to-content link')

# CSS for skip link
old_skip_css = '    .top-nav {'
new_skip_css = '''    .skip-link {
      position: fixed; top: -100px; left: 12px; z-index: 999;
      background: #22d3ee; color: #03040c; padding: 10px 18px; border-radius: 8px;
      font-size: 14px; font-weight: 700; text-decoration: none;
      transition: top .2s;
    }
    .skip-link:focus { top: 12px; }
    .top-nav {'''
content = content.replace(old_skip_css, new_skip_css)
changes.append('skip link CSS')

# 2b. Enhanced screen reader announcements for search results
old_a11y = '''    // ── A11y announcement helper ──
    function a11yAnnounce(msg) {
      const el = document.getElementById('a11y-live');
      if (!el) return;
      el.textContent = '';
      requestAnimationFrame(() => { el.textContent = msg; });
    }'''

new_a11y = '''    // ── A11y announcement helper ──
    function a11yAnnounce(msg, priority) {
      const liveRegion = document.getElementById('a11y-live');
      if (!liveRegion) return;
      if (priority === 'assertive') liveRegion.setAttribute('aria-live', 'assertive');
      liveRegion.textContent = '';
      requestAnimationFrame(() => {
        liveRegion.textContent = msg;
        if (priority === 'assertive') {
          setTimeout(() => liveRegion.setAttribute('aria-live', 'polite'), 1000);
        }
      });
    }

    // Announce search results for screen readers
    const _origRenderFeedSR = renderFeed;
    renderFeed = function() {
      _origRenderFeedSR();
      const cards = document.querySelectorAll('#feed-content .feed-card');
      const sq = window._searchQuery;
      if (sq) {
        a11yAnnounce(cards.length + ' article' + (cards.length !== 1 ? 's' : '') + ' found for "' + sq + '"');
      }
    };

    // Announce view switches
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        a11yAnnounce('Switched to ' + btn.textContent.trim() + ' view');
      });
    });

    // Focus visible enhancement for keyboard users
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Tab') {
        document.body.classList.add('keyboard-user');
      }
    }, {capture: true});
    document.addEventListener('mousedown', function() {
      document.body.classList.remove('keyboard-user');
    }, {capture: true});'''
content = content.replace(old_a11y, new_a11y)
changes.append('enhanced a11y announcements')

# CSS for keyboard-user focus
old_focus_css = '    .nav-btn:focus-visible,'
new_focus_css = '''    .keyboard-user :focus-visible {
      outline: 2px solid #22d3ee !important; outline-offset: 2px;
    }
    .nav-btn:focus-visible,'''    
content = content.replace(old_focus_css, new_focus_css)
changes.append('keyboard focus indicator')

# 2c. Add ARIA labels to feed cards and stats
old_card_aria = '        html += `<div class="feed-card"'
new_card_aria = '        html += `<article class="feed-card" role="article" aria-label="${a.title.replace(/"/g,\'&quot;\')}"'
content = content.replace(old_card_aria, new_card_aria)
changes.append('article role + aria-label')

# 2d. Add aria-live region to search dropdown
old_recent_div = '<div class="search-recent" id="searchRecent"></div>'
new_recent_div = '<div class="search-recent" id="searchRecent" role="listbox" aria-label="Recent searches"></div>'
content = content.replace(old_recent_div, new_recent_div)
changes.append('search dropdown ARIA')

# Update search-recent-item to have role
old_item_div = '<div class="search-recent-item"'
new_item_div = '<div class="search-recent-item" role="option"'
content = content.replace(old_item_div, new_item_div)
changes.append('search items role=option')


# ═══════════════════════════════════════════
# 3. SEO — JSON-LD structured data + dynamic meta
# ═══════════════════════════════════════════

old_seo = '  <meta property="og:title" conten'
new_seo = '''  <meta property="og:title" content="AstroAxis — AI-powered world news aggregator" />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="https://lazycat00x.github.io/astroaxis-site/og-image.png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="AstroAxis — AI-powered world news aggregator" />
  <meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large" />
  <meta property="og:title" conten'''
content = content.replace(old_seo, new_seo)
changes.append('enhanced meta tags')

# JSON-LD structured data — injected after opening <head>
old_jsonld = '  <link rel="canonical"'
new_jsonld = '''  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "AstroAxis",
    "url": "https://lazycat00x.github.io/astroaxis-site/",
    "description": "AI-powered world news aggregator with 3D globe visualization",
    "potentialAction": {
      "@type": "SearchAction",
      "target": "https://lazycat00x.github.io/astroaxis-site/?q={search_term_string}",
      "query-input": "required name=search_term_string"
    }
  }
  </script>
  <script type="application/ld+json" id="news-jsonld">
  {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "itemListElement": []
  }
  </script>
  <link rel="canonical"'''
content = content.replace(old_jsonld, new_jsonld)
changes.append('JSON-LD structured data')

# Dynamic NewsArticle JSON-LD update after feed render
old_jsonld_update = '      document.getElementById(\'feed-content\').innerHTML = html;\n      // Stagger card entrance animation'
new_jsonld_update = '''      document.getElementById('feed-content').innerHTML = html;
      // Update JSON-LD with current articles
      try {
        const newsLD = document.getElementById('news-jsonld');
        if (newsLD) {
          const ld = JSON.parse(newsLD.textContent);
          ld.itemListElement = filtered.slice(0, 10).map((a, i) => ({
            "@type": "ListItem", "position": i + 1,
            "item": {
              "@type": "NewsArticle",
              "headline": a.title,
              "url": a.url,
              "datePublished": a.published || '',
              "description": (a.ai_summary || '').slice(0, 160)
            }
          }));
          newsLD.textContent = JSON.stringify(ld, null, 2);
        }
      } catch(e) {}
      // Stagger card entrance animation'''
content = content.replace(old_jsonld_update, new_jsonld_update)
changes.append('dynamic NewsArticle JSON-LD')

# Write back
with open(path, 'w') as f:
    f.write(content)

print(f"Applied {len(changes)} changes:")
for c in changes:
    print(f"  ✓ {c}")
print(f"Total lines: {len(content.split(chr(10)))}")
