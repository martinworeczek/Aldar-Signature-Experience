"""Revision 2 of the 3a detail view (docs/detail-3a-README.md, updated spec).

Chapters become raised panels; each fact appears once (pillar/journey in the hero eyebrow,
status in hero + lifecycle, target go-live in Scope only). Run after apply_detail_3a.py.
"""
import json, re

PAGE = "index.html"

def sub(t, old, new, count=1):
    assert t.count(old) == count, (t.count(old), old[:80])
    return t.replace(old, new)

def main():
    html = open(PAGE, encoding="utf-8").read()
    m = re.search(r'(<script type="__bundler/template">\s*)(".*?")(\s*</script>)', html, re.S)
    t = json.loads(m.group(2))
    assert 'd3Eyebrow' not in t, "revision 2 already applied"

    # --- styles: panel chapters, sentence-case labels ---
    t = sub(t, ".d3-ch{display:grid;grid-template-columns:150px minmax(0,1fr);gap:28px;padding:30px 0;border-bottom:1px solid rgba(255,255,255,.14)}\n.d3-ch.d3-last{border-bottom:none;padding-bottom:0}\n.d3-num{font-family:'Poppins',sans-serif;font-size:28px;font-weight:300;letter-spacing:-.02em;color:#E8B96A;line-height:1}\n.d3-lbl{font-size:11px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.7);margin-top:9px}",
        ".d3-ch{display:grid;grid-template-columns:170px minmax(0,1fr);gap:32px;padding:28px 32px;background:#161616;border:1px solid rgba(255,255,255,.08);border-radius:14px;margin-top:16px}\n.d3-num{font-family:'Poppins',sans-serif;font-size:34px;font-weight:300;letter-spacing:-.02em;color:#E8B96A;line-height:1}\n.d3-lbl{font-family:'Poppins',sans-serif;font-size:15px;font-weight:500;color:#FFFFFF;margin-top:10px;line-height:1.3}")
    t = sub(t, "  .d3-ch{grid-template-columns:minmax(0,1fr);gap:14px}", "  .d3-ch{grid-template-columns:minmax(0,1fr);gap:16px;padding:22px 20px}")
    t = sub(t, "  .d3-body{padding-left:24px !important;padding-right:24px !important}", "  .d3-body{padding-left:16px !important;padding-right:16px !important}\n  .d3-life{padding:16px 20px !important}")

    # --- template ---
    t = sub(t, '<div class="d3-body" style="padding:6px 40px 44px">', '<div class="d3-body" style="padding:6px 32px 36px">')
    t = sub(t, '<span>{{ modal.eyebrow }}</span><span style="display:inline-flex;align-items:center;gap:7px;white-space:nowrap">',
               '<span>{{ modal.d3Eyebrow }}</span><span style="display:inline-flex;align-items:center;gap:7px;white-space:nowrap">')
    t = sub(t, '<div style="font-size:11px;color:rgba(255,255,255,.55)">{{ c.k }}</div><div style="font-size:14px;margin-top:4px;color:{{ c.color }}">{{ c.v }}</div>',
               '<div style="font-size:11px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;color:rgba(255,255,255,.5)">{{ c.k }}</div><div style="font-size:14px;margin-top:5px;color:{{ c.color }}">{{ c.v }}</div>')
    t = sub(t, '''          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;font-size:12px">
            <div style="display:flex;align-items:center;gap:14px;flex-wrap:nowrap;flex-shrink:0"><span style="{{ modal.d3Tag }}">{{ modal.deployStatusLabel }}</span><span style="color:rgba(255,255,255,.7);white-space:nowrap">Rollout <b style="color:#FFFFFF;font-weight:500">{{ modal.deployRollout }}</b></span></div>
            <span style="color:rgba(255,255,255,.7)">{{ modal.deploySummary }}</span>
          </div>''',
               '''          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;font-size:12px">
            <span style="font-size:14px;color:#FFFFFF">{{ modal.d3DeploySummary }}</span>
            <span style="color:rgba(255,255,255,.6);white-space:nowrap">{{ modal.d3DeployPct }}</span>
          </div>''')

    # --- view-model ---
    t = sub(t, "d3Line: _lineLbl, ", "d3Line: _lineLbl, d3Type: isDev ? ((((xd && xd.tracks) || {})[tgt.type] || {}).label || '') : '', d3Group: tgt.group || '', ")
    t = sub(t, "      modal.d3LifeGrid = { display: 'grid', gridTemplateColumns: 'repeat(' + Math.max(1, modal.d3Life.length) + ',minmax(0,1fr))', borderTop: '1px solid rgba(255,255,255,.14)', borderBottom: '1px solid rgba(255,255,255,.14)', padding: '18px 0', marginTop: '28px', columnGap: '12px' };",
               "      modal.d3LifeGrid = { display: 'grid', gridTemplateColumns: 'repeat(' + Math.max(1, modal.d3Life.length) + ',minmax(0,1fr))', gap: '12px', padding: '20px 32px', marginTop: '28px', background: '#161616', border: '1px solid rgba(255,255,255,.08)', borderRadius: '14px' };")
    old_scope = t[t.index("      modal.d3Scope = (modal.hasVertical"):t.index("      // deployment\n")]
    new_scope = """      // pillar and journey stage live in the hero eyebrow only
      const _jr = modal.scopeJourney;
      modal.d3Eyebrow = (modal.eyebrow || '') + ((!_dim(_jr) && String(modal.eyebrow || '').toLowerCase().indexOf(String(_jr).toLowerCase()) === -1) ? ' \\u00b7 ' + _jr : '');
      // scope & attributes: target go-live first, then scope; no pillar / journey cells
      modal.d3Scope = [{ k: 'Target go-live', v: modal.scopeTarget, tgt: true }, { k: 'Scope', v: modal.d3Group }, { k: 'User segment', v: modal.scopeSegment },
        { k: 'Tier', v: modal.scopeTier }, { k: 'Cadence', v: modal.scopeCadence }]
        .concat(modal.hasVertical ? [{ k: 'Estates vertical', v: modal.scopeVertical }] : [])
        .concat(modal.d3Type ? [{ k: 'Project type', v: modal.d3Type }] : [])
        .map(c => ({ k: c.k, v: (c.v == null || c.v === '') ? '\\u2014' : c.v, color: c.tgt ? _tgtC(c.v) : (_dim(c.v) ? 'rgba(255,255,255,.5)' : '#FFFFFF') }));
"""
    t = t.replace(old_scope, new_scope, 1)
    t = sub(t, "      modal.d3LiveBar = modal.deployLiveBar",
            """      // deployment header: the asset count and % live only (status and target date are shown elsewhere)
      const _dm = /^(\\d+) of (\\d+)/.exec(modal.deploySummary || ''), _ds = /^(\\d+) asset/.exec(modal.deploySummary || '');
      modal.d3DeploySummary = _dm ? (_dm[1] + ' of ' + _dm[2] + ' asset' + (_dm[2] === '1' ? '' : 's') + ' in scope ' + (_dm[2] === '1' ? 'is' : 'are') + ' live')
        : (_ds ? (_ds[1] + ' asset' + (_ds[1] === '1' ? '' : 's') + ' in scope') : '');
      modal.d3DeployPct = _dm ? (Math.round(+_dm[1] / Math.max(1, +_dm[2]) * 100) + '% live') : (_ds ? '0% live' : '');
      modal.d3LiveBar = modal.deployLiveBar""")
    out = html[:m.start(2)] + json.dumps(t).replace('</', '<\\u002F') + html[m.end(2):]
    open(PAGE, "w", encoding="utf-8").write(out)
    print("applied revision 2")

if __name__ == "__main__":
    main()
