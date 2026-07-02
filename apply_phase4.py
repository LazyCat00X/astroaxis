#!/usr/bin/env python3
"""Phase 4: performance monitoring, pipeline health, user analytics."""

path = '/home/kevyn/projects/astroaxis/globe.html'

with open(path) as f:
    content = f.read()

changes = []

# ═══════════════════════════════════════════
# 1. PERFORMANCE MONITORING — Core Web Vitals
# ═══════════════════════════════════════════

old_perf = '''    // ── Structured error logger ──'''
new_perf = '''    // ── Performance monitoring (Core Web Vitals) ──
    window._perfMetrics = {};
    try {
      // LCP (Largest Contentful Paint)
      new PerformanceObserver(function(list) {
        var entries = list.getEntries();
        if (entries.length) {
          window._perfMetrics.lcp = entries[entries.length-1].renderTime || entries[entries.length-1].loadTime;
        }
      }).observe({type: 'largest-contentful-paint', buffered: true});

      // FCP (First Contentful Paint)
      new PerformanceObserver(function(list) {
        var entries = list.getEntries();
        if (entries.length) window._perfMetrics.fcp = entries[0].startTime;
      }).observe({type: 'paint', buffered: true});

      // CLS (Cumulative Layout Shift)
      var clsValue = 0;
      new PerformanceObserver(function(list) {
        list.getEntries().forEach(function(entry) {
          if (!entry.hadRecentInput) clsValue += entry.value;
        });
        window._perfMetrics.cls = clsValue;
      }).observe({type: 'layout-shift', buffered: true});

      // TTFB
      var nav = performance.getEntriesByType('navigation')[0];
      if (nav) window._perfMetrics.ttfb = nav.responseStart - nav.requestStart;

      // Log after page stabilizes
      setTimeout(function() {
        var m = window._perfMetrics;
        console.log('%c⚡ AstroAxis Perf %cLCP:' + (m.lcp||0).toFixed(0) + 'ms FCP:' + (m.fcp||0).toFixed(0) + 'ms CLS:' + (m.cls||0).toFixed(3) + ' TTFB:' + (m.ttfb||0).toFixed(0) + 'ms',
          'color:#67e8f9;font-weight:bold', 'color:#8892b6');
        // Store for analytics
        try {
          var hist = JSON.parse(localStorage.getItem('astroaxis_perf') || '[]');
          hist.push({time: Date.now(), lcp: m.lcp, fcp: m.fcp, cls: m.cls, ttfb: m.ttfb});
          if (hist.length > 20) hist = hist.slice(-20);
          localStorage.setItem('astroaxis_perf', JSON.stringify(hist));
        } catch(e) {}
      }, 5000);
    } catch(e) { window._logError('perf', 'PerformanceObserver failed', e); }

    // ── Structured error logger ──'''
content = content.replace(old_perf, new_perf)
changes.append('Core Web Vitals monitoring')


# ═══════════════════════════════════════════
# 2. PIPELINE HEALTH — status indicator in Feed
# ═══════════════════════════════════════════

old_pipeline = '      const sourceSet = new Set(filtered.map(a => a.source));'
new_pipeline = '''      const allArticles = NEWS_DATA.articles || [];
      const sourceSet = new Set(filtered.map(a => a.source));
      const allSourceSet = new Set(allArticles.map(a => a.source));
      // Pipeline health: check data freshness
      const newestArticle = allArticles.reduce(function(max, a) {
        if (!a.published) return max;
        return Math.max(max, new Date(a.published).getTime());
      }, 0);
      const hoursSinceUpdate = newestArticle ? (Date.now() - newestArticle) / 3600000 : 999;
      const pipelineStatus = hoursSinceUpdate < 6 ? '🟢' : hoursSinceUpdate < 24 ? '🟡' : '🔴';
      const pipelineLabel = hoursSinceUpdate < 6 ? 'Live' : hoursSinceUpdate < 24 ? 'Stale (' + Math.floor(hoursSinceUpdate) + 'h)' : 'Offline';
      const pipelineColor = hoursSinceUpdate < 6 ? '#22c55e' : hoursSinceUpdate < 24 ? '#f59e0b' : '#ef4444';
      // Source coverage
      const configuredSources = 35; // from source_locs.json
      const activeSources = allSourceSet.size;
      const sourceHealth = activeSources >= 20 ? '🟢' : activeSources >= 10 ? '🟡' : '🔴';'''

content = content.replace(old_pipeline, new_pipeline)
changes.append('pipeline health data')

# Add pipeline health chip to stats bar
old_health_stats = '''      html += `<div class="stats-bar">
        <div class="stat-chip">📰 ${filtered.length} articles</div>
        <div class="stat-chip">📡 ${sourceSet.size} sources</div>'''
new_health_stats = '''      html += `<div class="stats-bar">
        <div class="stat-chip">${pipelineStatus} <span style="color:${pipelineColor}">${pipelineLabel}</span></div>
        <div class="stat-chip">📰 ${filtered.length} articles</div>
        <div class="stat-chip">${sourceHealth} ${activeSources}/${configuredSources} sources</div>'''
content = content.replace(old_health_stats, new_health_stats)
changes.append('pipeline health chip')


# ═══════════════════════════════════════════
# 3. USER ANALYTICS — page views + session (localStorage, no tracking)
# ═══════════════════════════════════════════

old_analytics = '''    window.addEventListener('unhandledrejection', function(e) {
      window._logError('promise', String(e.reason||'').slice(0,100));
    });'''

new_analytics = '''    window.addEventListener('unhandledrejection', function(e) {
      window._logError('promise', String(e.reason||'').slice(0,100));
    });

    // ── Privacy-respecting analytics (localStorage only, no external tracking) ──
    (function() {
      try {
        var analytics = JSON.parse(localStorage.getItem('astroaxis_analytics') || '{"visits":0,"firstVisit":null,"lastVisit":null,"totalSeconds":0,"sessions":[]}');
        var now = Date.now();
        analytics.visits = (analytics.visits || 0) + 1;
        analytics.firstVisit = analytics.firstVisit || now;
        analytics.lastVisit = now;
        // Session timer
        var sessionStart = now;
        setInterval(function() {
          analytics.totalSeconds = (analytics.totalSeconds || 0) + 30;
          if (analytics.totalSeconds % 300 < 30) { // save every ~5 min
            localStorage.setItem('astroaxis_analytics', JSON.stringify(analytics));
          }
        }, 30000);
        // Save on page unload
        window.addEventListener('beforeunload', function() {
          analytics.sessions = analytics.sessions || [];
          analytics.sessions.push({start: sessionStart, end: Date.now(), duration: Math.round((Date.now()-sessionStart)/1000)});
          if (analytics.sessions.length > 30) analytics.sessions = analytics.sessions.slice(-30);
          localStorage.setItem('astroaxis_analytics', JSON.stringify(analytics));
        });
        localStorage.setItem('astroaxis_analytics', JSON.stringify(analytics));
        // Console summary
        setTimeout(function() {
          var a = JSON.parse(localStorage.getItem('astroaxis_analytics') || '{}');
          var mins = Math.round((a.totalSeconds||0)/60);
          console.log('%c📊 AstroAxis %c' + (a.visits||0) + ' visits · ' + mins + ' min total',
            'color:#a78bfa;font-weight:bold', 'color:#8892b6');
        }, 2000);
      } catch(e) {}
    })();'''
content = content.replace(old_analytics, new_analytics)
changes.append('privacy analytics')


# ═══════════════════════════════════════════
# 4. CACHE HEADERS — set in HTML meta
# ═══════════════════════════════════════════

old_meta_end = '  <meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large" />'
new_meta_end = '''  <meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large" />
  <meta http-equiv="Cache-Control" content="public, max-age=300, stale-while-revalidate=600" />'''
content = content.replace(old_meta_end, new_meta_end)
changes.append('cache-control meta')


# ═══════════════════════════════════════════
# 5. PERF DASHBOARD — accessible via console: window._dashboard()
# ═══════════════════════════════════════════

old_dash_end = '    // ── View switching ──'
new_dash_end = '''    // ── Dev dashboard (type window._dashboard() in console) ──
    window._dashboard = function() {
      var d = {
        perf: window._perfMetrics || {},
        errors: (typeof _errors !== 'undefined') ? _errors : [],
        analytics: (function(){try{return JSON.parse(localStorage.getItem('astroaxis_analytics')||'{}');}catch(e){return{};}})(),
        searches: (function(){try{return JSON.parse(localStorage.getItem('astroaxis_searches')||'[]');}catch(e){return[];}})(),
        interests: (function(){try{return JSON.parse(localStorage.getItem('astroaxis_interests')||'{}');}catch(e){return{};}})(),
        bookmarks: (function(){try{return JSON.parse(localStorage.getItem('astroaxis_bookmarks')||'[]');}catch(e){return[];}})(),
        articles: (NEWS_DATA && NEWS_DATA.articles) ? NEWS_DATA.articles.length : 0,
        memory: (performance.memory) ? {used: Math.round(performance.memory.usedJSHeapSize/1048576)+'MB', limit: Math.round(performance.memory.jsHeapSizeLimit/1048576)+'MB'} : 'N/A'
      };
      console.table(d);
      console.log('%c💡 %cwindow._dashboard() %c— AstroAxis diagnostics',
        'color:#67e8f9', 'color:#a78bfa', 'color:#8892b6');
      return d;
    };

    // ── View switching ──'''
content = content.replace(old_dash_end, new_dash_end)
changes.append('dev dashboard')


# Write back
with open(path, 'w') as f:
    f.write(content)

print(f"Applied {len(changes)} changes:")
for c in changes:
    print(f"  ✓ {c}")
print(f"Total lines: {len(content.split(chr(10)))}")
