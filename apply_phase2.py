#!/usr/bin/env python3
"""Phase 2 enhancements: global search, personalization, analytics."""

path = '/home/kevyn/projects/astroaxis/globe.html'

with open(path) as f:
    content = f.read()

changes = []

# ═══════════════════════════════════════════
# 1. GLOBAL SEARCH — works in both Feed + History views
# ═══════════════════════════════════════════

# 1a. Update placeholder to be more generic
old_ph = 'placeholder="🔍 Search history..." aria-label="Search history timeline events"'
new_ph = 'placeholder="🔍 Search articles & events..." aria-label="Search news articles and timeline events"'
content = content.replace(old_ph, new_ph)
changes.append('search placeholder updated')

# 1b. Add CSS for search dropdown (recent searches)
old_css_s = '''    .history-search.no-match { border-color: rgba(239,68,68,0.4); }'''
new_css_s = '''    .history-search.no-match { border-color: rgba(239,68,68,0.4); }
    .search-recent {
      position: absolute; top: 100%; left: 0; right: 0; margin-top: 4px;
      background: rgba(7,10,22,.95); border: 1px solid rgba(136,136,160,.15); border-radius: 10px;
      padding: 6px 0; z-index: 20; display: none; backdrop-filter: blur(12px);
      max-height: 180px; overflow-y: auto;
    }
    .search-recent.open { display: block; }
    .search-recent-item {
      padding: 7px 14px; font-size: 12px; color: rgba(228,228,236,.7); cursor: pointer;
      display: flex; justify-content: space-between; align-items: center;
    }
    .search-recent-item:hover { background: rgba(34,211,238,.08); color: #eef7ff; }
    .search-recent-item .del-recent { color: rgba(136,136,160,.4); font-size: 14px; padding: 2px 6px; }
    .search-recent-item .del-recent:hover { color: #ef4444; }
    .search-wrap { position: relative; }'''
content = content.replace(old_css_s, new_css_s)
changes.append('search dropdown CSS')

# 1c. Wrap search input in a container for dropdown positioning
old_wrap = '''  <input type="text" class="history-search" id="historySearch" placeholder="🔍 Search articles & events..." aria-label="Search news articles and timeline events" autocomplete="off" spellcheck="false">'''
new_wrap = '''  <span class="search-wrap">
    <input type="text" class="history-search" id="historySearch" placeholder="🔍 Search articles & events..." aria-label="Search news articles and timeline events" autocomplete="off" spellcheck="false">
    <div class="search-recent" id="searchRecent"></div>
  </span>'''
content = content.replace(old_wrap, new_wrap)
changes.append('search wrap + dropdown HTML')

# 1d. Rewrite search handler — now triggers feed re-render too
old_handler = '''    // ── History search input ──
    const searchInput = document.getElementById('historySearch');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        const val = searchInput.value.trim().toLowerCase();
        window._searchQuery = val || null;
        // Visual feedback on input border
        searchInput.classList.remove('has-match', 'no-match');
        if (val && window._historyDots) {
          const hasMatch = window._historyDots.some(d => {
            const ev = d.userData._event;
            if (!ev) return false;
            return (ev.title||'').toLowerCase().includes(val) || (ev.desc||'').toLowerCase().includes(val) || String(d.userData._year).includes(val);
          });
          searchInput.classList.add(hasMatch ? 'has-match' : 'no-match');
        }
      });
      // Clear on Escape
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') { searchInput.value = ''; searchInput.dispatchEvent(new Event('input')); searchInput.blur(); e.stopPropagation(); }
      });
    }'''

new_handler = '''    // ── Global search input (history + feed) ──
    const searchInput = document.getElementById('historySearch');
    const searchRecent = document.getElementById('searchRecent');

    function getRecentSearches() {
      try { return JSON.parse(localStorage.getItem('astroaxis_searches') || '[]'); } catch(e) { return []; }
    }
    function saveRecentSearch(q) {
      if (!q || q.length < 2) return;
      let recents = getRecentSearches().filter(r => r !== q);
      recents.unshift(q);
      if (recents.length > 8) recents.pop();
      localStorage.setItem('astroaxis_searches', JSON.stringify(recents));
    }
    function renderRecentSearches() {
      if (!searchRecent) return;
      const recents = getRecentSearches();
      if (!recents.length) { searchRecent.classList.remove('open'); return; }
      searchRecent.innerHTML = recents.map((r, i) =>
        `<div class="search-recent-item" data-q="${r.replace(/"/g,'&quot;')}"><span>🕐 ${r}</span><span class="del-recent" data-idx="${i}">×</span></div>`
      ).join('');
      searchRecent.classList.add('open');
    }

    if (searchInput) {
      searchInput.addEventListener('focus', () => renderRecentSearches());
      searchInput.addEventListener('blur', () => setTimeout(() => searchRecent?.classList.remove('open'), 200));

      searchInput.addEventListener('input', () => {
        const val = searchInput.value.trim().toLowerCase();
        window._searchQuery = val || null;
        searchInput.classList.remove('has-match', 'no-match');

        // Trigger Feed re-render when in feed view
        const feedView = document.getElementById('feed-view');
        if (feedView && feedView.classList.contains('active')) {
          renderFeed();
        }

        // Visual feedback
        if (!val) { searchRecent?.classList.remove('open'); return; }
        // Check history dots
        let hasMatch = false;
        if (window._historyDots) {
          hasMatch = window._historyDots.some(d => {
            const ev = d.userData?._event;
            if (!ev) return false;
            return (ev.title||'').toLowerCase().includes(val) || (ev.desc||'').toLowerCase().includes(val) || String(d.userData._year).includes(val);
          });
        }
        // Also check feed articles
        const articles = NEWS_DATA.articles || [];
        if (!hasMatch) {
          hasMatch = articles.some(a =>
            (a.title||'').toLowerCase().includes(val) || (a.ai_summary||'').toLowerCase().includes(val) || (a.source||'').toLowerCase().includes(val)
          );
        }
        searchInput.classList.add(hasMatch ? 'has-match' : 'no-match');
      });

      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          searchInput.value = ''; searchInput.dispatchEvent(new Event('input')); searchInput.blur(); e.stopPropagation();
        }
        if (e.key === 'Enter') {
          const val = searchInput.value.trim();
          if (val) saveRecentSearch(val);
          searchRecent?.classList.remove('open');
        }
      });
    }

    // Recent search click handler
    if (searchRecent) {
      searchRecent.addEventListener('mousedown', (e) => {
        const item = e.target.closest('.search-recent-item');
        if (!item) return;
        if (e.target.classList.contains('del-recent')) {
          const idx = parseInt(e.target.dataset.idx);
          let recents = getRecentSearches();
          recents.splice(idx, 1);
          localStorage.setItem('astroaxis_searches', JSON.stringify(recents));
          renderRecentSearches();
          return;
        }
        const q = item.dataset.q;
        if (q) { searchInput.value = q; searchInput.dispatchEvent(new Event('input')); }
      });
    }'''
content = content.replace(old_handler, new_handler)
changes.append('global search handler')

# 1e. Add search filter to renderFeed
old_feed_filter = '''      // Apply active filters (topic & time)
      const filtered = articles.filter(a => {
        // Topic filter
        if (activeFilters.topic !== 'All' && a.topic !== activeFilters.topic) return false;
        // Time filter
        if (activeFilters.time !== 'all') {
          if (!a.published) return false;
          const hoursAgo = (Date.now() - Date.parse(a.published)) / (1000 * 60 * 60);
          if (activeFilters.time === '6h' && hoursAgo > 6) return false;
          if (activeFilters.time === '24h' && hoursAgo > 24) return false;
        }
        return true;
      });'''

new_feed_filter = '''      // Apply active filters (topic, time) + global search
      const sq = window._searchQuery;
      const filtered = articles.filter(a => {
        // Global search filter
        if (sq) {
          const haystack = ((a.title||'') + ' ' + (a.ai_summary||'') + ' ' + (a.source||'')).toLowerCase();
          if (!haystack.includes(sq)) return false;
        }
        // Topic filter
        if (activeFilters.topic !== 'All' && a.topic !== activeFilters.topic) return false;
        // Time filter
        if (activeFilters.time !== 'all') {
          if (!a.published) return false;
          const hoursAgo = (Date.now() - Date.parse(a.published)) / (1000 * 60 * 60);
          if (activeFilters.time === '6h' && hoursAgo > 6) return false;
          if (activeFilters.time === '24h' && hoursAgo > 24) return false;
        }
        return true;
      });'''
content = content.replace(old_feed_filter, new_feed_filter)
changes.append('search filter in feed')


# ═══════════════════════════════════════════
# 2. PERSONALIZATION — "For You" section
# ═══════════════════════════════════════════

# 2a. Add "For You" section after stats bar in renderFeed
old_foryou = '''      // Stats bar: topic distribution'''
new_foryou = '''      // ── Personalization: "For You" based on reading history ──
      const interests = (()=>{ try{return JSON.parse(localStorage.getItem('astroaxis_interests')||'{}');}catch(e){return{};} })();
      const topInterest = Object.entries(interests).sort((a,b)=>b[1]-a[1])[0];
      if (topInterest && topInterest[1] >= 1 && activeFilters.topic === 'All' && !sq) {
        const recs = articles.filter(a => a.topic === topInterest[0] && !a.summarized === false).slice(0, 2);
        if (recs.length) {
          html += `<div style="margin-bottom:18px;max-width:900px;margin-left:auto;margin-right:auto">
            <div style="font-size:13px;color:rgba(136,146,182,.6);margin-bottom:8px;letter-spacing:.04em">⭐ For You · ${topInterest[0]}</div>
            <div class="feed-grid">`;
          recs.forEach(a => {
            const bullets = ((a.summaries && a.summaries[currentLang]) || (a.summaries && a.summaries['zh-HK']) || a.ai_summary || '').split('\\\\n').filter(l => l.includes('•')).map(l => l.replace(/^[•\\\\s]+/,'').trim()).filter(Boolean).slice(0, 3);
            const tb = topicGradient(a.topic||'General');
            html += `<div class="feed-card rec-card" style="--thumb-bg:${tb};border-color:rgba(245,158,11,.2)">
              <h3><a href="${a.url}" target="_blank" rel="noopener">${a.title}</a></h3>
              <div class="card-summary"><ul>${bullets.map(b => `<li>${b}</li>`).join('')}</ul></div>
              <div class="card-meta"><span>${a.source}</span><span>${a.published ? new Date(a.published).toLocaleDateString() : ''}</span></div>
            </div>`;
          });
          html += `</div></div>`;
        }
      }

      // Stats bar: topic distribution'''
content = content.replace(old_foryou, new_foryou)
changes.append('For You section')

# Add CSS for rec-card
old_rec_css = '''    .feed-card:hover { border-color: rgba(99,102,241,0.35); transform: translateY(-2px); }'''
new_rec_css = '''    .feed-card:hover { border-color: rgba(99,102,241,0.35); transform: translateY(-2px); }
    .rec-card { border-color: rgba(245,158,11,.15) !important; }
    .rec-card:hover { border-color: rgba(245,158,11,.4) !important; }'''
content = content.replace(old_rec_css, new_rec_css)
changes.append('rec-card CSS')


# ═══════════════════════════════════════════
# 3. DATA ANALYTICS — Trend arrows + hot topic cloud
# ═══════════════════════════════════════════

# 3a. Add trend calculation and topic cloud in stats bar
old_stats_end = '''      html += `<div class="feed-grid">`;'''
new_stats_end = '''      // Trend: compare 24h vs 48h
      const now = Date.now();
      const recent24 = articles.filter(a => { if(!a.published) return false; return (now - Date.parse(a.published)) < 86400000; });
      const prev48 = articles.filter(a => { if(!a.published) return false; const h = (now - Date.parse(a.published))/3600000; return h >= 24 && h < 48; });
      const trend24 = recent24.length;
      const trend48 = prev48.length;
      const trendPct = trend48 > 0 ? Math.round((trend24 - trend48) / trend48 * 100) : 0;
      const trendIcon = trendPct > 10 ? '📈' : trendPct < -10 ? '📉' : '📊';
      const trendColor = trendPct > 10 ? '#22c55e' : trendPct < -10 ? '#ef4444' : '#8892b6';
      html += `<div class="stats-bar">
        <div class="stat-chip">📰 ${filtered.length} articles</div>
        <div class="stat-chip">📡 ${sourceSet.size} sources</div>
        <div class="stat-chip" style="color:${trendColor}">${trendIcon} 24h trend ${trendPct > 0 ? '+' : ''}${trendPct}%</div>
        ${topTopics.map(([t,c]) => {
          const pct = Math.round(c/maxCount*100);
          const tc = t==='AI'?'#3b82f6':t==='Bitcoin'?'#f97316':t==='Regulation'?'#ef4444':t==='DeFi'?'#22c55e':t==='Crypto'?'#818cf8':t==='Finance'?'#10b981':t==='Tech'?'#6366f1':'#8892b6';
          return `<div class="stat-chip"><span style="color:${tc};font-weight:600">${t}</span> ${c}<span class="stat-bar-bg"><span class="stat-bar-fill" style="width:${pct}%;background:${tc}"></span></span></div>`;
        }).join('')}
      </div>`;
      // Hot topic cloud
      if (!sq && activeFilters.topic === 'All') {
        const allTopics = {}; articles.forEach(a => { const t = a.topic || 'Other'; allTopics[t] = (allTopics[t]||0)+1; });
        const hotTopics = Object.entries(allTopics).sort((a,b) => b[1]-a[1]).slice(0, 12);
        if (hotTopics.length > 1) {
          const maxHot = hotTopics[0][1];
          html += `<div style="max-width:900px;margin:0 auto 16px;display:flex;flex-wrap:wrap;gap:6px;align-items:center">
            <span style="font-size:11px;color:rgba(136,146,182,.5);margin-right:4px">🔥</span>`;
          hotTopics.forEach(([t,c]) => {
            const size = Math.max(11, 11 + (c/maxHot)*10);
            const tc = t==='AI'?'#3b82f6':t==='Bitcoin'?'#f97316':t==='Regulation'?'#ef4444':t==='DeFi'?'#22c55e':'#8892b6';
            html += `<span class="topic-tag" style="font-size:${size}px;color:${tc};cursor:pointer;padding:2px 8px;border-radius:999px;background:rgba(136,136,160,.06);border:1px solid rgba(136,136,160,.1);transition:all .2s" data-topic="${t}" onclick="document.querySelector('.filter-btn[data-filter-value=\\\\'${t}\\\\']')?.click()">${t} ${c}</span>`;
          });
          html += `</div>`;
        }
      }
      html += `<div class="feed-grid">`;'''
content = content.replace(old_stats_end, new_stats_end)
changes.append('trend + topic cloud')

# Add CSS for topic-tag hover
old_tag_css = '''    .feed-content-wrap.filtering { opacity: 0.5; }'''
new_tag_css = '''    .feed-content-wrap.filtering { opacity: 0.5; }
    .topic-tag:hover { border-color: rgba(34,211,238,.4) !important; background: rgba(34,211,238,.08) !important; }'''
content = content.replace(old_tag_css, new_tag_css)
changes.append('topic tag hover CSS')

# Write back
with open(path, 'w') as f:
    f.write(content)

print(f"Applied {len(changes)} changes:")
for c in changes:
    print(f"  ✓ {c}")
print(f"Total lines: {len(content.split(chr(10)))}")
