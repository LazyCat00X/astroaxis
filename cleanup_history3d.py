#!/usr/bin/env python3
"""Remove standalone history3d view — rings already merged into globe."""

import re

path = '/home/kevyn/projects/astroaxis/globe.html'

with open(path, 'r') as f:
    content = f.read()

changes = []

# 1. Remove nav button (line 637)
old = '  <button class="nav-btn" data-view="history3d" data-i18n="nav.history3d" role="tab" aria-selected="false" tabindex="-1">3D History</button>\n'
assert old in content, "nav button not found"
content = content.replace(old, '')
changes.append('nav button removed')

# 2. Remove history3d-view HTML panel (lines 721-737)
old = '''
<!-- 3D History Timeline Panel -->
<div id="history3d-view" class="view-panel" role="tabpanel" aria-label="3D History timeline view">
  <div id="history3d-loading" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:2;pointer-events:none">
    <div style="text-align:center">
      <div style="font-size:32px;margin-bottom:10px">🔄</div>
      <div style="color:rgba(238,247,255,.5);font-size:13px;letter-spacing:.06em">Loading 3D History...</div>
    </div>
  </div>
  <canvas id="history3d-canvas" role="application" aria-label="Interactive 3D history timeline. Use scroll to zoom, drag to rotate."></canvas>
  <div id="history3d-tooltip" class="article-tooltip" role="status" aria-live="polite"></div>
  <div id="history3d-hud" style="position:absolute;top:60px;left:20px;z-index:5;pointer-events:none">
    <div id="history3d-year-label" style="font-size:14px;color:#8892b6;font-weight:600;letter-spacing:.08em"></div>
  </div>
  <div style="position:absolute;bottom:30px;left:50%;transform:translateX(-50%);z-index:5;font-size:11px;color:rgba(136,136,160,0.5);letter-spacing:.06em;pointer-events:none" data-i18n="history3d.hint">
    DRAG TO ROTATE · SCROLL TO ZOOM · HOVER FOR DETAILS
  </div>
</div>
'''
assert old in content, "history3d panel not found"
content = content.replace(old, '')
changes.append('history3d panel HTML removed')

# 3. Remove CSS for #history3d-canvas
old = '''    /* 3D History canvas */
    #history3d-canvas {
      position: absolute; inset: 0; width: 100%; height: 100%; display: block;
      cursor: grab; touch-action: none;
    }
    #history3d-canvas:active { cursor: grabbing; }
'''
assert old in content, "CSS not found"
content = content.replace(old, '')
changes.append('CSS removed')

# 4. Remove I18N entries for history3d
# nav.history3d
content = re.sub(r"'nav\.history3d':'[^']*',?", '', content)
content = re.sub(r'  \n', '\n', content)  # Clean double spaces from regex
changes.append('I18N nav.history3d removed')

# history3d.hint
content = re.sub(r"'history3d\.hint':'[^']*',?", '', content)
changes.append('I18N history3d.hint removed')

# history3d.label
content = re.sub(r"'history3d\.label':'[^']*',?", '', content)
changes.append('I18N history3d.label removed')

# 5. Update hint.drag: 1-4 → 1-3 for en, zh-HK, zh-CN
content = content.replace("1-4 VIEWS'", "1-3 VIEWS'")
content = content.replace("1-4切換'", "1-3切換'")
content = content.replace("1-4切换'", "1-3切换'")
changes.append('hint.drag 1-4→1-3 (en,zh-HK,zh-CN)')

# 6. Update hint HTML (line 702)
content = content.replace('🖱 DRAG · A/D ←→ SPIN · W/S ↑↓ TILT · Q/E ZOOM · 1-4 VIEWS',
                          '🖱 DRAG · A/D ←→ SPIN · W/S ↑↓ TILT · Q/E ZOOM · 1-3 VIEWS')
changes.append('hint HTML updated 1-4→1-3')

# 7. Remove initHistory3D() function — find its boundaries
start_marker = "    // ── 3D History Timeline ──\n    let history3D = null;\n\n    function initHistory3D() {"
end_marker = "    // Deactivate 3D history when leaving view\n    function stopHistory3D() {"

assert start_marker in content, "initHistory3D start not found"
assert end_marker in content, "stopHistory3D not found"

idx_start = content.index(start_marker)
idx_end = content.index(end_marker)

old_block = content[idx_start:idx_end]
content = content[:idx_start] + content[idx_end:]
changes.append(f'initHistory3D() removed ({len(old_block)} chars)')

# 8. Remove stopHistory3D() function
stop_start = "    function stopHistory3D() {"
# Find where stopHistory3D ends (next function or block)
# The next line after stopHistory3D ends is the nav click handler comment
nav_comment = "    // Update nav click handler to init/stop 3D History"
assert stop_start in content, "stopHistory3D start not found"
assert nav_comment in content, "nav handler comment not found"

idx_s = content.index(stop_start)
idx_e = content.index(nav_comment)

old_block2 = content[idx_s:idx_e]
content = content[:idx_s] + content[idx_e:]
changes.append(f'stopHistory3D() removed ({len(old_block2)} chars)')

# 9. Update nav click handler — remove history3d init/stop
old_nav = '''        if (btn.dataset.view === 'history3d') { initHistory3D(); }
        else { stopHistory3D(); }'''
assert old_nav in content, "nav history3d handler not found"
content = content.replace(old_nav, '')
changes.append('nav click handler cleaned')

# 10. Update the nav comment
content = content.replace(
    "    // Update nav click handler to init/stop 3D History",
    "    // Update nav click handler"
)
changes.append('nav comment updated')

# 11. Update viewMap: remove '4': 'history3d', add '4' as zoom-to-history
old_map = "      const viewMap = { '1': 'globe', '2': 'timeline', '3': 'feed', '4': 'history3d' };"
new_map = "      const viewMap = { '1': 'globe', '2': 'timeline', '3': 'feed' };"
assert old_map in content, "viewMap not found"
content = content.replace(old_map, new_map)
changes.append('viewMap updated (4 removed)')

# 12. Update comment: "1-4" → "1-3"
content = content.replace("      // Number keys 1-4: switch views", "      // Number keys 1-3: switch views")
changes.append('comment 1-4→1-3')

# 13. Add key '4' as zoom-to-history shortcut
# Insert after the viewMap check block, before Escape handler
insert_before = '''
      // Escape'''
insert_code = '''
      // Key 4: zoom out to history rings distance
      if (e.key === '4' && !e.ctrlKey && !e.metaKey && !e.altKey && globeView && globeView.classList.contains('active')) {
        const center = new THREE.Vector3(0, -0.4, 0);
        const dir = camera.position.clone().sub(center).normalize();
        const TARGET_DIST = 20;
        const duration = 800;
        const startDist = camera.position.distanceTo(center);
        const startTime = performance.now();
        function zoomAnim(now) {
          const elapsed = now - startTime;
          const t = Math.min(1, elapsed / duration);
          const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
          const dist = startDist + (TARGET_DIST - startDist) * eased;
          camera.position.copy(center.clone().add(dir.clone().multiplyScalar(dist)));
          camera.lookAt(center);
          controls.target.copy(center);
          controls.update();
          renderer.render(scene, camera);
          if (t < 1) requestAnimationFrame(zoomAnim);
        }
        requestAnimationFrame(zoomAnim);
        pauseAutoRotate();
        e.preventDefault(); return;
      }'''

assert insert_before in content, "Escape marker not found"
content = content.replace(insert_before, insert_code + insert_before)
changes.append('key 4 zoom-to-history shortcut added')

# Write back
with open(path, 'w') as f:
    f.write(content)

print(f"Total lines now: {len(content.split(chr(10)))}")
for c in changes:
    print(f"  ✓ {c}")
print("Done!")
