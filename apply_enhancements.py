#!/usr/bin/env python3
"""Apply all 4 UI enhancements to globe.html: thumbnails, data viz, animations, share."""

path = '/home/kevyn/projects/astroaxis/globe.html'

with open(path) as f:
    content = f.read()

changes = []

# ═══════════════════════════════════════════
# 1. THUMBNAILS - Add topic-color gradient placeholder images to feed cards
# ═══════════════════════════════════════════

# 1a. CSS for card thumbnails
old_css1 = '''    .feed-card .card-meta { display: flex; justify-content: space-between; font-size: 12px; color: rgba(136,136,160,0.6); border-top: 1px solid rgba(136,136,160,0.08); padding-top: 8px; }'''
new_css1 = '''    .feed-card { overflow: hidden; }
    .feed-card .card-thumb {
      width: 100%; height: 120px; object-fit: cover; border-radius: 8px; margin-bottom: 10px;
      display: block; background: var(--thumb-bg, rgba(15,23,42,0.5));
    }
    .feed-card .card-thumb.placeholder {
      display: flex; align-items: center; justify-content: center;
      font-size: 32px; opacity: 0.5;
    }
    .feed-card .card-meta { display: flex; justify-content: space-between; font-size: 12px; color: rgba(136,136,160,0.6); border-top: 1px solid rgba(136,136,160,0.08); padding-top: 8px; }'''
content = content.replace(old_css1, new_css1)
changes.append('thumb CSS added')

# 1b. Topic → gradient color map for thumbnail placeholders
topic_colors_js = '''
    const TOPIC_GRADIENTS = {
      'AI': ['#1e3a5f','#3b82f6'], 'Bitcoin': ['#3d2e0a','#f97316'],
      'Regulation': ['#3d1a1a','#ef4444'], 'DeFi': ['#1a3d1a','#22c55e'],
      'Crypto': ['#2d1a5f','#818cf8'], 'Finance': ['#1a3d2e','#10b981'],
      'Tech': ['#1a2a5f','#6366f1'], 'Policy': ['#3d2a0a','#f59e0b'],
      'Macro': ['#2d1a3d','#a855f7'], 'Trading': ['#1a3d3d','#06b6d4'],
      'Ethereum': ['#1a1a3d','#8b5cf6'], 'Science': ['#1a3d1a','#84cc16'],
    };
    function topicGradient(topic) {
      const g = TOPIC_GRADIENTS[topic] || ['#1a1a2e','#8892b6'];
      return `linear-gradient(135deg, ${g[0]}, ${g[1]}40)`;
    }
'''

# Insert before renderFeed
old_js1 = "    function renderFeed() {"
new_js1 = topic_colors_js + "\n    function renderFeed() {"
content = content.replace(old_js1, new_js1)
changes.append('topic gradient map added')

# 1c. Add thumbnail HTML to card template
old_card = '''        html += `<div class="feed-card">
          <div class="card-top">
            <span class="card-topic" style="color:#${a.topic === 'AI' ? '3b82f6' : a.topic === 'Bitcoin' ? 'f97316' : a.topic === 'Regulation' ? 'ef4444' : a.topic === 'DeFi' ? '22c55e' : '818cf8'}">${a.topic || 'General'}</span>'''
new_card = '''        const thumbBg = topicGradient(a.topic || 'General');
        html += `<div class="feed-card" style="--thumb-bg:${thumbBg}">
          <div class="card-thumb placeholder" aria-hidden="true" style="background:${thumbBg}">${(a.topic||'G')[0]}</div>
          <div class="card-top">
            <span class="card-topic" style="color:#${a.topic === 'AI' ? '3b82f6' : a.topic === 'Bitcoin' ? 'f97316' : a.topic === 'Regulation' ? 'ef4444' : a.topic === 'DeFi' ? '22c55e' : '818cf8'}">${a.topic || 'General'}</span>'''
content = content.replace(old_card, new_card)
changes.append('card thumbnail HTML added')

# Mobile: smaller thumb
old_mob = '''      .nav-btn{font-size:10px;padding:5px 9px}'''
new_mob = '''      .nav-btn{font-size:10px;padding:5px 9px}
      .feed-card .card-thumb{height:90px}'''
content = content.replace(old_mob, new_mob)
changes.append('mobile thumb size')


# ═══════════════════════════════════════════
# 2. DATA VIZ - Stats bar at top of Feed
# ═══════════════════════════════════════════

# CSS for stats bar
old_css2 = '''    .feed-grid { display: grid; grid-template-columns: 1fr; gap: 14px; max-width: 900px; margin: 0 auto; }'''
new_css2 = '''    .feed-grid { display: grid; grid-template-columns: 1fr; gap: 14px; max-width: 900px; margin: 0 auto; }
    .stats-bar {
      display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; max-width: 900px; margin-left: auto; margin-right: auto;
    }
    .stat-chip {
      background: rgba(7,10,22,.6); border: 1px solid rgba(136,136,160,.12); border-radius: 10px;
      padding: 8px 14px; display: flex; align-items: center; gap: 8px; font-size: 12px; color: rgba(228,228,236,.7);
      min-width: 0;
    }
    .stat-chip .stat-bar-bg { flex:1; height:4px; border-radius:2px; background:rgba(136,136,160,.1); overflow:hidden; min-width:40px; }
    .stat-chip .stat-bar-fill { height:100%; border-radius:2px; transition: width .4s ease; }
    @media(max-width:768px){ .stats-bar{gap:6px} .stat-chip{font-size:10px;padding:5px 10px} }'''
content = content.replace(old_css2, new_css2)
changes.append('stats bar CSS added')

# Stats bar generation function inserted before feed-grid in renderFeed
old_stats = '''      html += `<div class="feed-grid">`;'''
new_stats = '''      // Stats bar: topic distribution
      const topicCounts = {}; filtered.forEach(a => { const t = a.topic || 'Other'; topicCounts[t] = (topicCounts[t]||0)+1; });
      const topTopics = Object.entries(topicCounts).sort((a,b) => b[1]-a[1]).slice(0,4);
      const maxCount = topTopics[0]?.[1] || 1;
      const sourceSet = new Set(filtered.map(a => a.source));
      html += `<div class="stats-bar">
        <div class="stat-chip">📰 ${filtered.length} articles</div>
        <div class="stat-chip">📡 ${sourceSet.size} sources</div>
        ${topTopics.map(([t,c]) => {
          const pct = Math.round(c/maxCount*100);
          const tc = t==='AI'?'#3b82f6':t==='Bitcoin'?'#f97316':t==='Regulation'?'#ef4444':t==='DeFi'?'#22c55e':t==='Crypto'?'#818cf8':t==='Finance'?'#10b981':t==='Tech'?'#6366f1':'#8892b6';
          return `<div class="stat-chip"><span style="color:${tc};font-weight:600">${t}</span> ${c}<span class="stat-bar-bg"><span class="stat-bar-fill" style="width:${pct}%;background:${tc}"></span></span></div>`;
        }).join('')}
      </div>`;
      html += `<div class="feed-grid">`;'''
content = content.replace(old_stats, new_stats)
changes.append('stats bar HTML added')


# ═══════════════════════════════════════════
# 3. TRANSITION ANIMATIONS - Stagger entrance + filter fade
# ═══════════════════════════════════════════

old_css3 = '''    .feed-card:hover { border-color: rgba(99,102,241,0.35); }'''
new_css3 = '''    .feed-card {
      animation: cardIn .4s ease-out both;
      opacity: 0; transform: translateY(12px);
    }
    @keyframes cardIn { to { opacity:1; transform:translateY(0); } }
    .feed-card:hover { border-color: rgba(99,102,241,0.35); transform: translateY(-2px); }
    .feed-content-wrap { transition: opacity .2s ease; }
    .feed-content-wrap.filtering { opacity: 0.5; }'''
content = content.replace(old_css3, new_css3)
changes.append('card animation CSS')

# Stagger the animation delay in renderFeed (after cards are rendered)
old_stagger = '''      document.getElementById('feed-content').innerHTML = html;
    }'''
new_stagger = '''      document.getElementById('feed-content').innerHTML = html;
      // Stagger card entrance animation
      const cards = document.querySelectorAll('#feed-content .feed-card');
      cards.forEach((c, i) => { c.style.animationDelay = (i * 0.04) + 's'; });
    }'''
content = content.replace(old_stagger, new_stagger)
changes.append('card stagger animation')

# Filter transition: wrap in filtering class
old_filter = '''    function renderFeed() {
      const articles = NEWS_DATA.articles || [];
      // Apply active filters (topic & time)'''
new_filter = '''    function renderFeed() {
      const articles = NEWS_DATA.articles || [];
      const wrap = document.getElementById('feed-content');
      if(wrap) wrap.classList.add('filtering');
      // Apply active filters (topic & time)'''
content = content.replace(old_filter, new_filter)
changes.append('filter transition start')

old_filter2 = '''      document.getElementById('feed-content').innerHTML = html;
      // Stagger card entrance animation'''
new_filter2 = '''      document.getElementById('feed-content').innerHTML = html;
      if(wrap) { requestAnimationFrame(() => { wrap.classList.remove('filtering'); }); }
      // Stagger card entrance animation'''
content = content.replace(old_filter2, new_filter2)
changes.append('filter transition end')


# ═══════════════════════════════════════════
# 4. SHARE ENHANCEMENT - Better toast + Web Share API
# ═══════════════════════════════════════════

old_share = '''    function shareArticle(url, title) {
      if(navigator.share){ navigator.share({title,url}); }
      else { navigator.clipboard.writeText(url).then(() => { const t=document.createElement('div');t.textContent='📋 Link copied!';t.style.cssText='position:fixed;bottom:100px;left:50%;transform:translateX(-50%);background:rgba(34,211,238,.2);border:1px solid #67e8f9;border-radius:12px;padding:10px 20px;color:#eaffff;z-index:100;font-size:13px;font-weight:600';document.body.appendChild(t);setTimeout(()=>t.remove(),1500); }).catch(()=>{ window.open(url,'_blank'); }); }
    }'''
new_share = '''    function showToast(msg) {
      const t = document.getElementById('share-toast') || (()=>{ const e=document.createElement('div');e.id='share-toast';e.style.cssText='position:fixed;bottom:100px;left:50%;transform:translateX(-50%);background:rgba(34,211,238,.15);border:1px solid #67e8f9;border-radius:999px;padding:10px 22px;color:#eaffff;z-index:100;font-size:13px;font-weight:600;backdrop-filter:blur(12px);pointer-events:none;opacity:0;transition:opacity .25s';document.body.appendChild(e);return e;})();
      t.textContent = msg; t.style.opacity = '1';
      clearTimeout(t._tid); t._tid = setTimeout(()=>{ t.style.opacity = '0'; }, 1800);
    }
    function shareArticle(url, title) {
      if(navigator.share){ navigator.share({title,url}).catch(()=>{}); }
      else if(navigator.clipboard){ navigator.clipboard.writeText(url).then(()=>{ showToast('📋 Link copied!'); }).catch(()=>{ window.open(url,'_blank'); }); }
      else { window.open(url,'_blank'); }
    }'''
content = content.replace(old_share, new_share)
changes.append('share enhanced with toast')

# Write back
with open(path, 'w') as f:
    f.write(content)

print(f"Applied {len(changes)} changes:")
for c in changes:
    print(f"  ✓ {c}")
print(f"Total lines: {len(content.split(chr(10)))}")
