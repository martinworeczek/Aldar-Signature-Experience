"""Apply the "3a Continuous Portrait" experience detail view (docs/detail-3a-README.md).

Visual change plus one removal: the Implementation progress / Progress log block is no
longer rendered (its data and handlers stay). Dark-ground colours are added to the
view-model as d3* fields next to the light ones; nothing existing is renamed or removed.
Idempotent: refuses to run twice.
"""
import json, re

PAGE = "index.html"

CSS_ANCHOR = "@keyframes mKen {"
CSS = r""".d3-ch{display:grid;grid-template-columns:150px minmax(0,1fr);gap:28px;padding:30px 0;border-bottom:1px solid rgba(255,255,255,.14)}
.d3-ch.d3-last{border-bottom:none;padding-bottom:0}
.d3-num{font-family:'Poppins',sans-serif;font-size:28px;font-weight:300;letter-spacing:-.02em;color:#E8B96A;line-height:1}
.d3-lbl{font-size:11px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.7);margin-top:9px}
.d3-sub{font-size:11px;color:rgba(255,255,255,.5);margin-top:8px;line-height:1.5}
.d3-field{width:100%;box-sizing:border-box;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:10px;color:#FFF;font-family:'Poppins',sans-serif;font-size:13px;padding:10px 12px;outline:none;line-height:1.5}
.d3-field::placeholder{color:rgba(255,255,255,.4)}
.d3-field:focus{border-color:#E8B96A}
.d3-pill{font-family:'Poppins',sans-serif;font-size:11px;font-weight:500;border-radius:999px;padding:8px 16px;cursor:pointer;white-space:nowrap;transition:.15s}
.d3-modal a{color:#E8B96A}
@media (max-width:760px){
  .d3-ch{grid-template-columns:minmax(0,1fr);gap:14px}
  .d3-ch-head{display:flex;align-items:baseline;gap:12px}
  .d3-ch-head .d3-lbl{margin-top:0}
  .d3-scope{grid-template-columns:repeat(2,minmax(0,1fr)) !important}
  .d3-two{grid-template-columns:minmax(0,1fr) !important}
  .d3-life{grid-template-columns:repeat(2,minmax(0,1fr)) !important;row-gap:12px}
  .d3-hero-txt{left:24px !important;right:24px !important}
  .d3-body{padding-left:24px !important;padding-right:24px !important}
}
"""

VM_ANCHOR = "eyebrow: eyebrow, showRag: !isLines, showLog: !isLines,"
VM_ADD = "d3Line: _lineLbl, d3Essence: (tgt.essence && String(tgt.essence).trim()) || '', d3StKey: st.key, "

DARK_ANCHOR = "\n\n    return Object.assign({\n      cmd: cmd,\n      col: col,"
DARK = r"""
    // ---- 3a detail view: dark-ground variants (visual only; the light fields stay as they are) ----
    if (modal) {
      const D3 = { live: '#B5EBBE', prog: '#F5CD85', rev: '#EFE2C6', park: 'rgba(255,255,255,.85)', red: '#F2A391' };
      const d3Of = k => (k === 'live' || k === 'audited') ? D3.live : (k === 'impl' ? D3.prog : ((k === 'dep' || k === 'disc') ? D3.park : D3.rev));
      const tint = (c, a) => { const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(c); return m ? 'rgba(' + parseInt(m[1], 16) + ',' + parseInt(m[2], 16) + ',' + parseInt(m[3], 16) + ',' + a + ')' : 'rgba(255,255,255,' + a + ')'; };
      const sc = d3Of(modal.d3StKey);
      modal.d3StageColor = sc;
      modal.d3Tag = { display: 'inline-flex', alignItems: 'center', fontSize: '11px', fontWeight: 600, letterSpacing: '.06em', textTransform: 'uppercase', color: sc, background: tint(sc, .12), border: '1px solid ' + tint(sc, .4), borderRadius: '4px', padding: '5px 10px', whiteSpace: 'nowrap' };
      // hero
      const _src = (/url\((['"]?)(.*?)\1\)/.exec((modal.imageStyle || {}).backgroundImage || '') || [])[2] || '';
      modal.d3HeroImg = _src
        ? { position: 'absolute', inset: 0, backgroundImage: 'url("' + _src + '")', backgroundSize: 'cover', backgroundPosition: 'center 40%', animation: 'mKen 16s ease-out both' }
        : { position: 'absolute', inset: 0, background: 'radial-gradient(60% 40% at 50% 34%,rgba(232,185,106,.14),transparent 70%),linear-gradient(160deg,#2B3136 0%,#171E23 60%,#0E1418 100%)' };
      modal.d3HeroBox = { position: 'relative', overflow: 'hidden', background: '#000', height: _src ? 'min(520px,62vh)' : 'auto', minHeight: _src ? '420px' : '380px' };
      const _shadow = '0 1px 2px rgba(0,0,0,.6),0 0 18px rgba(0,0,0,.5)';
      modal.d3HeroTxt = _src ? { position: 'absolute', left: '40px', right: '40px', bottom: '30px', textShadow: _shadow, zIndex: 1 }
        : { position: 'relative', padding: '200px 40px 30px', textShadow: _shadow, zIndex: 1 };
      // lifecycle
      const ci = (modal.life || []).findIndex(s => s.txt && s.txt.fontWeight === 700);
      modal.d3Life = (modal.life || []).map((s, i) => {
        const cur = i === ci, done = ci > -1 && i < ci;
        return { label: s.label,
          row: Object.assign({ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', minWidth: 0 }, cur ? { color: sc, fontWeight: 500 } : { color: done ? 'rgba(255,255,255,.75)' : 'rgba(255,255,255,.5)' }),
          dot: cur ? { width: '8px', height: '8px', borderRadius: '50%', background: sc, boxShadow: '0 0 0 4px ' + tint(sc, .2), flexShrink: 0 }
            : { width: '8px', height: '8px', borderRadius: '50%', boxSizing: 'border-box', flexShrink: 0, background: done ? 'rgba(255,255,255,.75)' : 'transparent', border: done ? 'none' : '1px solid rgba(255,255,255,.45)' } };
      });
      modal.d3LifeGrid = { display: 'grid', gridTemplateColumns: 'repeat(' + Math.max(1, modal.d3Life.length) + ',minmax(0,1fr))', borderTop: '1px solid rgba(255,255,255,.14)', borderBottom: '1px solid rgba(255,255,255,.14)', padding: '18px 0', marginTop: '28px', columnGap: '12px' };
      // scope & attributes (Estates vertical first, when present)
      const _dim = v => v == null || v === '' || v === '—' || v === 'N/A' || v === 'TBC';
      const _tgtC = v => _dim(v) ? 'rgba(255,255,255,.5)' : (v === 'Already live' ? D3.live : ((v === 'Parked to 2027' || v === 'Discontinued') ? D3.park : D3.prog));
      modal.d3Scope = (modal.hasVertical ? [{ k: 'Estates vertical', v: modal.scopeVertical }] : []).concat([
        { k: 'Pillar', v: modal.scopePillar }, { k: 'Journey stage', v: modal.scopeJourney }, { k: 'User segment', v: modal.scopeSegment },
        { k: 'Tier', v: modal.scopeTier }, { k: 'Cadence', v: modal.scopeCadence }, { k: 'Target go-live', v: modal.scopeTarget, tgt: true }
      ]).map(c => ({ k: c.k, v: (c.v == null || c.v === '') ? '—' : c.v, color: c.tgt ? _tgtC(c.v) : (_dim(c.v) ? 'rgba(255,255,255,.5)' : '#FFFFFF') }));
      // deployment
      modal.d3LiveBar = modal.deployLiveBar ? { width: modal.deployLiveBar.width, background: D3.live } : { width: '0%' };
      (modal.deployGroups || []).forEach(g => (g.assets || []).forEach(a => {
        a.d3Color = !a.inScope ? 'rgba(255,255,255,.55)' : (a.stateLabel === 'Live' ? D3.live : D3.prog);
        a.d3Name = !a.inScope ? 'rgba(255,255,255,.55)' : '#FFFFFF';
      }));
      const _gap = String(modal.auditGapColor || '').toUpperCase();
      modal.d3AuditGap = _gap === '#5F7A5B' ? D3.live : (_gap === '#A8503C' ? D3.red : D3.prog);
      // RAG strip
      const _rc = ({ R: D3.red, A: D3.prog, G: D3.live })[modal.ragLetter] || D3.park;
      modal.d3RagBar = { width: '3px', borderRadius: '2px', alignSelf: 'stretch', background: _rc, flexShrink: 0 };
      modal.d3RagBadge = { width: '22px', height: '22px', borderRadius: '50%', background: _rc, color: '#0A1014', fontSize: '11px', fontWeight: 600, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 };
      // buttons (labels and selected states come from col; recoloured for dark)
      const _out = { color: '#FFFFFF', background: 'transparent', border: '1px solid rgba(255,255,255,.35)' };
      modal.d3SaveCss = { color: '#0A1014', background: '#E8B96A', border: '1px solid #E8B96A' };
      const _cl = String((col && col.cmpLabel) || '');
      modal.d3CmpCss = /^✓/.test(_cl) ? { color: '#FFFFFF', background: '#7B916C', border: '1px solid #7B916C' }
        : (/full/i.test(_cl) ? Object.assign({}, _out, { opacity: .45, cursor: 'not-allowed' }) : _out);
      modal.d3OutCss = _out;
      // chapters: number only those that render, in display order
      const _ch = [['scope', true], ['deploy', !!modal.showDeploy], ['progress', !!modal.hasProgress], ['benefits', !!modal.hasBenefits], ['tp', !!modal.hasTP], ['audit', true], ['assets', true], ['photos', !!modal.hasPhotos]].filter(c => c[1]);
      modal.ch = {};
      _ch.forEach((c, i) => { modal.ch[c[0]] = { n: (i + 1 < 10 ? '0' : '') + (i + 1), cls: 'd3-ch' + (i === _ch.length - 1 ? ' d3-last' : '') }; });
      ['scope', 'deploy', 'progress', 'benefits', 'tp', 'audit', 'assets', 'photos'].forEach(k => { if (!modal.ch[k]) modal.ch[k] = { n: '', cls: 'd3-ch' }; });
      // assets
      (modal.assetShots || []).forEach(sh => { sh.d3 = Object.assign({}, sh.css, { borderRadius: '6px', border: '1px solid rgba(255,255,255,.1)', boxShadow: 'none', backgroundColor: '#1A1A1A' }); });
      modal.d3MoreCss = Object.assign({}, modal.assetMoreCss || {}, { border: '1px solid rgba(255,255,255,.2)', background: 'transparent', color: 'rgba(255,255,255,.7)', borderRadius: '6px' });
      (modal.assetWall || []).forEach(tw => { tw.d3 = Object.assign({}, tw.css, { background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.1)', boxShadow: 'none', borderRadius: '6px' }); });
      (modal.photos || []).forEach(p => { p.d3 = Object.assign({}, p.bg, { borderRadius: '8px' }); });
    }
"""

def ch_open(key, label, sub=""):
    return ('<div class="{{ modal.ch.%s.cls }}"><div class="d3-ch-head"><div class="d3-num">{{ modal.ch.%s.n }}</div><div class="d3-lbl">%s</div>%s</div>'
            % (key, key, label, sub))

TPL = ('''<sc-if value="{{ showModal }}" hint-placeholder-val="{{ false }}">
<div sc-camel-on-click="{{ closeModal }}" style="position:fixed;inset:0;z-index:200;background:rgba(21,38,50,.42);backdrop-filter:blur(5px);display:flex;justify-content:center;overflow-y:auto;padding:40px 20px">
  <div class="d3-modal" sc-camel-on-click="{{ stop }}" style="position:relative;width:min(940px,100%);height:max-content;background:#0A0A0A;border-radius:14px;overflow:hidden;box-shadow:0 40px 90px rgba(0,0,0,.45);color:#FFFFFF;font-family:'Poppins',sans-serif;animation:mzoom .3s cubic-bezier(.2,.7,.2,1) both;margin:auto 0">

    <div style="{{ modal.d3HeroBox }}">
      <div style="{{ modal.d3HeroImg }}"></div>
      <sc-if value="{{ modal.noImage }}" hint-placeholder-val="{{ false }}"><div style="position:absolute;top:34%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none"><div style="font-size:30px;color:rgba(232,185,106,.5);line-height:1">◎</div><div style="font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:rgba(246,243,236,.5);margin-top:10px;white-space:nowrap">Imagery coming soon</div></div></sc-if>
      <sc-if value="{{ modal.hasImage }}" hint-placeholder-val="{{ false }}"><div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 40%,rgba(0,0,0,.6) 62%,rgba(0,0,0,.9) 82%,#0A0A0A 100%)"></div></sc-if>
      <div style="position:absolute;top:22px;left:28px;right:28px;display:flex;justify-content:space-between;align-items:center;gap:12px;z-index:2">
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:nowrap;flex-shrink:0">
          <sc-if value="{{ modal.defining }}" hint-placeholder-val="{{ false }}"><span style="flex-shrink:0;font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#0A1014;background:#E8B96A;border-radius:999px;padding:5px 11px;white-space:nowrap">✦ Defining moment</span></sc-if>
          <span style="font-size:10px;font-weight:500;letter-spacing:.1em;text-transform:uppercase;color:#FFFFFF;background:rgba(0,0,0,.66);border:1px solid rgba(255,255,255,.18);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);border-radius:999px;padding:5px 11px;white-space:nowrap">{{ modal.d3Line }}</span>
        </div>
        <div style="display:flex;align-items:center;margin-left:auto">
          <button sc-camel-on-click="{{ closeModal }}" style="flex-shrink:0;width:34px;height:34px;border-radius:50%;border:1px solid rgba(255,255,255,.3);background:rgba(0,0,0,.4);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);color:#FFFFFF;font-size:15px;line-height:1;cursor:pointer" style-hover="border-color:#E8B96A">✕</button>
        </div>
      </div>
      <div class="d3-hero-txt" style="{{ modal.d3HeroTxt }}">
        <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase"><span>{{ modal.eyebrow }}</span><span style="display:inline-flex;align-items:center;gap:7px;white-space:nowrap"><span style="width:7px;height:7px;border-radius:50%;background:{{ modal.d3StageColor }};box-shadow:0 0 0 2px rgba(0,0,0,.35)"></span>{{ modal.deployStatusLabel }}</span></div>
        <div style="font-size:clamp(36px,4.6vw,48px);font-weight:300;line-height:1.05;letter-spacing:-.015em;margin-top:14px;max-width:16ch;text-wrap:pretty;overflow-wrap:normal;word-break:normal;hyphens:manual">{{ modal.name }}</div>
        <sc-if value="{{ modal.d3Essence }}" hint-placeholder-val="{{ true }}"><div style="font-size:14px;line-height:1.55;color:#FFFFFF;margin-top:12px;max-width:60ch">{{ modal.d3Essence }}</div></sc-if>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:20px;text-shadow:none">
          <button class="d3-pill" sc-camel-on-click="{{ col.onPrimary }}" title="{{ col.btnTitle }}" style="{{ modal.d3SaveCss }}" style-hover="background:#F0CE93">{{ col.label }}</button>
          <button class="d3-pill" sc-camel-on-click="{{ col.onCmp }}" title="Compare with other experiences — AI-assisted" style="{{ modal.d3CmpCss }}" style-hover="background:rgba(255,255,255,.12)">{{ col.cmpLabel }}</button>
          <sc-if value="{{ ix.has }}" hint-placeholder-val="{{ false }}"><button class="d3-pill" sc-camel-on-click="{{ ix.onGo }}" title="{{ ix.title }}" style="{{ modal.d3OutCss }}" style-hover="background:rgba(255,255,255,.12)">{{ ix.label }}</button></sc-if>
        </div>
      </div>
    </div>

    <div class="d3-body" style="padding:6px 40px 44px">
      <sc-if value="{{ modal.showRag }}" hint-placeholder-val="{{ false }}">
      <div style="display:flex;gap:14px;align-items:center;padding:16px 0;border-bottom:1px solid rgba(255,255,255,.14)">
        <div style="{{ modal.d3RagBar }}"></div>
        <div style="flex:1;min-width:0;display:flex;align-items:center;gap:14px;flex-wrap:wrap">
          <span style="display:inline-flex;align-items:center;gap:9px"><span style="{{ modal.d3RagBadge }}">{{ modal.ragLetter }}</span><span style="font-size:14px;font-weight:600;color:#FFFFFF;white-space:nowrap">{{ modal.ragTitle }}</span></span>
          <span style="font-size:12.5px;color:rgba(255,255,255,.72);line-height:1.45">{{ modal.ragReason }}</span>
          <span style="margin-left:auto;display:inline-flex;align-items:center;gap:8px;flex-wrap:wrap"><span style="font-size:10.5px;color:#FFFFFF;border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:4px 10px;white-space:nowrap">{{ modal.ragPriority }}</span><span style="font-size:10.5px;color:#FFFFFF;border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:4px 10px;white-space:nowrap">{{ modal.ragAction }}</span></span>
          <sc-if value="{{ modal.hasSecondaryActions }}" hint-placeholder-val="{{ false }}">
          <div style="flex-basis:100%;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <span style="font-size:10px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55)">Also needed</span>
            <sc-for list="{{ modal.secondaryActions }}" as="s" hint-placeholder-count="2"><span style="font-size:10.5px;color:#FFFFFF;border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:4px 10px;white-space:nowrap">{{ s.label }}</span></sc-for>
          </div>
          </sc-if>
        </div>
      </div>
      </sc-if>

      <div style="font-size:18px;font-weight:300;line-height:1.6;color:rgba(255,255,255,.9);max-width:62ch;margin-top:14px;text-wrap:pretty">{{ modal.narrative }}</div>

      <div class="d3-life" style="{{ modal.d3LifeGrid }}">
        <sc-for list="{{ modal.d3Life }}" as="s" hint-placeholder-count="4"><div style="{{ s.row }}"><span style="{{ s.dot }}"></span><span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ s.label }}</span></div></sc-for>
      </div>

      ''' + ch_open('scope', 'Scope &amp; attributes') + '''
        <div class="d3-scope" style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px 24px">
          <sc-for list="{{ modal.d3Scope }}" as="c" hint-placeholder-count="6"><div style="min-width:0"><div style="font-size:11px;color:rgba(255,255,255,.55)">{{ c.k }}</div><div style="font-size:14px;margin-top:4px;color:{{ c.color }}">{{ c.v }}</div></div></sc-for>
        </div>
      </div>

      <sc-if value="{{ modal.showDeploy }}" hint-placeholder-val="{{ false }}">
      ''' + ch_open('deploy', 'Deployment') + '''
        <div style="min-width:0">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;font-size:12px">
            <div style="display:flex;align-items:center;gap:14px;flex-wrap:nowrap;flex-shrink:0"><span style="{{ modal.d3Tag }}">{{ modal.deployStatusLabel }}</span><span style="color:rgba(255,255,255,.7);white-space:nowrap">Rollout <b style="color:#FFFFFF;font-weight:500">{{ modal.deployRollout }}</b></span></div>
            <span style="color:rgba(255,255,255,.7)">{{ modal.deploySummary }}</span>
          </div>
          <sc-if value="{{ modal.deployShowBar }}" hint-placeholder-val="{{ false }}"><div style="height:3px;background:rgba(255,255,255,.14);margin:12px 0 20px;display:flex"><span style="{{ modal.d3LiveBar }}"></span></div></sc-if>
          <sc-if value="{{ modal.hasLiveDate }}" hint-placeholder-val="{{ false }}">
          <div style="display:flex;align-items:center;gap:18px;flex-wrap:wrap;font-size:12px;color:rgba(255,255,255,.7);margin:12px 0 18px">
            <sc-if value="{{ modal.liveDateKnown }}" hint-placeholder-val="{{ true }}">
            <span>Went live <b style="color:#FFFFFF;font-weight:500">{{ modal.liveDate }}</b> · {{ modal.liveDays }} days ago</span>
            <sc-if value="{{ modal.showAudit }}" hint-placeholder-val="{{ true }}"><span>Audit due <b style="color:#FFFFFF;font-weight:500">{{ modal.auditDue }}</b></span></sc-if>
            </sc-if>
            <sc-if value="{{ modal.liveDateNotKnown }}" hint-placeholder-val="{{ false }}"><span>Deployed &amp; Live — <b style="color:#FFFFFF;font-weight:500">go-live date not yet captured</b>. Add it to start the 30-day audit clock.</span></sc-if>
            <sc-if value="{{ modal.showAudit }}" hint-placeholder-val="{{ true }}"><span style="margin-left:auto;display:inline-flex;align-items:center;gap:7px;color:{{ modal.d3AuditGap }}"><span style="width:7px;height:7px;border-radius:50%;background:{{ modal.d3AuditGap }}"></span>{{ modal.auditGap }}</span></sc-if>
          </div>
          </sc-if>
          <sc-if value="{{ modal.hasDeploy }}" hint-placeholder-val="{{ true }}">
          <div style="margin-top:14px">
          <sc-for list="{{ modal.deployGroups }}" as="g" hint-placeholder-count="2">
            <div style="font-size:10px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:4px">{{ g.type }}</div>
            <div style="margin-bottom:14px">
              <sc-for list="{{ g.assets }}" as="a" hint-placeholder-count="2"><div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.1)"><span style="width:8px;height:8px;border-radius:50%;flex-shrink:0;background:{{ a.d3Color }}"></span><span style="flex:1;min-width:0;font-size:13px;color:{{ a.d3Name }}">{{ a.name }}</span><span style="font-size:11px;color:{{ a.d3Color }};white-space:nowrap">{{ a.stateLabel }}</span></div></sc-for>
            </div>
          </sc-for>
          <sc-if value="{{ modal.hasOutScope }}" hint-placeholder-val="{{ false }}"><div style="font-size:12px;color:rgba(255,255,255,.55);line-height:1.6">{{ modal.outScopeText }}</div></sc-if>
          </div>
          </sc-if>
          <sc-if value="{{ modal.noDeploy }}" hint-placeholder-val="{{ false }}"><div style="font-size:13px;color:rgba(255,255,255,.7);line-height:1.6;margin-top:14px">{{ modal.deployNote }}</div></sc-if>
        </div>
      </div>
      </sc-if>

      <sc-if value="{{ modal.hasProgress }}" hint-placeholder-val="{{ false }}">
      ''' + ch_open('progress', 'Progress summary', '<div class="d3-sub">Updated {{ modal.progressDate }}</div>') + '''
        <div style="font-size:13px;line-height:1.65;color:rgba(255,255,255,.88)">{{ modal.progress }}</div>
      </div>
      </sc-if>

      <sc-if value="{{ modal.hasBenefits }}" hint-placeholder-val="{{ false }}">
      ''' + ch_open('benefits', 'Why it matters', '<div class="d3-sub">Moment of truth · {{ modal.moment }}</div>') + '''
        <div class="d3-two" style="display:grid;grid-template-columns:1fr 1fr;gap:28px">
          <div><div style="font-size:10px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-bottom:8px">For the customer</div><div style="font-size:13px;line-height:1.6;color:rgba(255,255,255,.88)">{{ modal.customerBenefit }}</div></div>
          <div><div style="font-size:10px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-bottom:8px">For Aldar</div><div style="font-size:13px;line-height:1.6;color:rgba(255,255,255,.88)">{{ modal.aldarBenefit }}</div></div>
        </div>
      </div>
      </sc-if>

      <sc-if value="{{ modal.hasTP }}" hint-placeholder-val="{{ false }}">
      ''' + ch_open('tp', 'Touchpoints') + '''
        <div class="d3-two" style="display:grid;grid-template-columns:1fr 1fr;gap:10px 28px">
          <sc-for list="{{ modal.tp }}" as="t" hint-placeholder-count="4"><div style="display:flex;gap:10px"><span style="color:#E8B96A;font-size:12px;margin-top:1px">—</span><span style="font-size:13px;color:rgba(255,255,255,.88);line-height:1.55">{{ t }}</span></div></sc-for>
        </div>
      </div>
      </sc-if>

      ''' + ch_open('audit', 'Audit intelligence') + '''
        <div style="min-width:0">
          <sc-if value="{{ modal.showAuditBtn }}" hint-placeholder-val="{{ false }}"><div style="display:flex;justify-content:flex-end;margin-bottom:14px"><button class="d3-pill" sc-camel-on-click="{{ modal.toggleAudit }}" style="color:#FFFFFF;background:transparent;border:1px solid rgba(255,255,255,.35)" style-hover="background:rgba(255,255,255,.12)">{{ modal.auditBtnLabel }}</button></div></sc-if>
          <sc-if value="{{ modal.editing }}" hint-placeholder-val="{{ false }}">
          <div class="d3-two" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
            <div><div style="font-size:10px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-bottom:6px">eNPS</div><input class="d3-field" value="{{ modal.draftEnps }}" sc-camel-on-change="{{ modal.onEnps }}" placeholder="e.g. 38"></div>
            <div><div style="font-size:10px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-bottom:6px">CSAT (%)</div><input class="d3-field" value="{{ modal.draftCsat }}" sc-camel-on-change="{{ modal.onCsat }}" placeholder="e.g. 88"></div>
          </div>
          <div style="font-size:10px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-bottom:6px">Executive summary — why this score</div>
          <textarea class="d3-field" value="{{ modal.draftSummary }}" sc-camel-on-change="{{ modal.onSummary }}" placeholder="Key reasons behind the score…" style="min-height:76px;resize:vertical"></textarea>
          <div style="font-size:10px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin:12px 0 6px">Full audit report link</div>
          <input class="d3-field" value="{{ modal.draftReport }}" sc-camel-on-change="{{ modal.onReport }}" placeholder="https://…sharepoint…">
          <button sc-camel-on-click="{{ modal.saveAudit }}" style="margin-top:14px;font-family:'Poppins',sans-serif;font-size:11.5px;font-weight:600;color:#0A1014;background:#E8B96A;border:none;border-radius:999px;padding:10px 18px;cursor:pointer;white-space:nowrap">Save audit</button>
          </sc-if>
          <sc-if value="{{ modal.showScore }}" hint-placeholder-val="{{ false }}">
          <div style="display:flex;gap:24px;align-items:stretch;flex-wrap:wrap">
            <div style="flex-shrink:0;padding-right:24px;border-right:1px solid rgba(255,255,255,.14);display:flex;gap:26px;align-items:center">
              <div style="text-align:center"><div style="font-size:44px;font-weight:300;color:#E8B96A;line-height:.95">{{ modal.enps }}</div><div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-top:6px">eNPS</div></div>
              <div style="text-align:center"><div style="font-size:44px;font-weight:300;color:#E8B96A;line-height:.95">{{ modal.csat }}</div><div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-top:6px">CSAT</div></div>
            </div>
            <div style="flex:1;min-width:220px"><div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-bottom:6px">Why this score · {{ modal.auditedWhen }}</div><div style="font-size:13px;color:rgba(255,255,255,.88);line-height:1.6">{{ modal.auditSummary }}</div><sc-if value="{{ modal.hasReport }}" hint-placeholder-val="{{ false }}"><a href="{{ modal.reportUrl }}" target="_blank" style="display:inline-block;font-size:12px;font-weight:500;color:#E8B96A;margin-top:12px;cursor:pointer">View full audit report ↗</a></sc-if></div>
          </div>
          </sc-if>
          <sc-if value="{{ modal.showPending }}" hint-placeholder-val="{{ true }}"><div style="font-size:13px;color:rgba(255,255,255,.7);line-height:1.6">Not yet audited. Use <b style="color:#FFFFFF;font-weight:500">Record audit</b> to add the eNPS/CSAT scores and an executive summary once this experience has been reviewed after go-live.</div></sc-if>
          <sc-if value="{{ modal.showLocked }}" hint-placeholder-val="{{ false }}"><div style="font-size:13px;color:rgba(255,255,255,.7);line-height:1.6">Auditing opens once this experience is <b style="color:#FFFFFF;font-weight:500">Deployed &amp; Live</b>. eNPS/CSAT scores are captured after go-live.</div></sc-if>
        </div>
      </div>

      ''' + ch_open('assets', 'Assets') + '''
        <div style="min-width:0">
          <div style="display:flex;justify-content:space-between;align-items:baseline;gap:16px"><div style="font-size:14px;color:rgba(255,255,255,.88);line-height:1.4">{{ modal.assetHead }}</div><span style="font-size:11px;color:rgba(255,255,255,.5);white-space:nowrap">SharePoint</span></div>
          <sc-if value="{{ modal.hasAssets }}" hint-placeholder-val="{{ false }}">
          <div style="background:rgba(255,255,255,.04);border-radius:10px;padding:20px;margin-top:16px">
            <div style="font-size:10px;font-weight:500;letter-spacing:.14em;text-transform:uppercase;color:#E8B96A">{{ modal.assetLibLabel }}</div>
            <div style="font-size:24px;font-weight:300;color:#FFFFFF;margin-top:8px;line-height:1.2">{{ modal.assetFolderName }}</div>
            <div style="font-size:12.5px;color:rgba(255,255,255,.7);margin-top:6px;line-height:1.5">{{ modal.assetPreviewLine }}</div>
            <div style="display:flex;gap:12px;align-items:flex-end;margin-top:18px">
              <sc-if value="{{ modal.assetHasShots }}" hint-placeholder-val="{{ false }}">
              <sc-for list="{{ modal.assetShots }}" as="sh" hint-placeholder-count="1"><div style="{{ sh.d3 }}"></div></sc-for>
              <sc-if value="{{ modal.assetHasMore }}" hint-placeholder-val="{{ true }}">
              <a href="{{ modal.assetUrl }}" target="_blank" style="{{ modal.d3MoreCss }}" style-hover="border-color:#E8B96A">
                <span style="font-size:22px;font-weight:300;color:#FFFFFF">{{ modal.assetMore }}</span>
                <span style="font-size:9.5px;letter-spacing:.11em;text-transform:uppercase">{{ modal.assetMoreLabel }}</span>
              </a>
              </sc-if>
              </sc-if>
              <sc-if value="{{ modal.assetWallShow }}" hint-placeholder-val="{{ true }}">
              <sc-for list="{{ modal.assetWall }}" as="tw" hint-placeholder-count="3">
                <div style="{{ tw.d3 }}">
                  <img alt="" ref="{{ tw.imgRef }}" style="{{ tw.imgCss }}">
                  <span data-tw-scrim="1" style="{{ tw.scrimCss }}"></span>
                  <span data-tw-n="1" style="position:relative;font-size:26px;font-weight:300;color:#FFFFFF;line-height:1">{{ tw.n }}</span>
                  <span data-tw-k="1" style="position:relative;font-size:9.5px;font-weight:500;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.55);margin-top:5px">{{ tw.kind }}</span>
                  <span data-tw-s="1" style="position:relative;font-size:10.5px;color:rgba(255,255,255,.5);margin-top:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%">{{ tw.sample }}</span>
                </div>
              </sc-for>
              </sc-if>
            </div>
            <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:18px">
              <a href="{{ modal.assetUrl }}" target="_blank" style="font-size:11.5px;font-weight:600;color:#0A1014;background:#E8B96A;border-radius:999px;padding:10px 18px;text-decoration:none;white-space:nowrap" style-hover="background:#F0CE93">Browse the full library ↗</a>
              <span style="font-size:11px;color:rgba(255,255,255,.5)">Opens the folder in SharePoint — permissions apply.</span>
            </div>
          </div>
          </sc-if>
        </div>
      </div>

      <sc-if value="{{ modal.hasPhotos }}" hint-placeholder-val="{{ false }}">
      ''' + ch_open('photos', 'Implementation photos') + '''
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <sc-for list="{{ modal.photos }}" as="p" hint-placeholder-count="0"><div style="{{ p.d3 }}"></div></sc-for>
        </div>
      </div>
      </sc-if>
    </div>
  </div>
</div>
</sc-if>''')

def main():
    html = open(PAGE, encoding="utf-8").read()
    m = re.search(r'(<script type="__bundler/template">\s*)(".*?")(\s*</script>)', html, re.S)
    t = json.loads(m.group(2))
    assert 'd3HeroImg' not in t, "detail 3a already applied"
    # template: replace the whole showModal block
    a = t.index('<sc-if value="{{ showModal }}"')
    depth = 0
    for mm in re.finditer(r'<sc-if\b|</sc-if>', t[a:]):
        depth += 1 if mm.group(0).startswith('<sc-if') else -1
        if depth == 0:
            b = a + mm.end(); break
    old = t[a:b]
    assert 'modal.showLog' in old and 'modal.assetWall' in old
    t = t[:a] + TPL + t[b:]
    # styles, view-model
    assert t.count(CSS_ANCHOR) == 1 and t.count(VM_ANCHOR) == 1 and t.count(DARK_ANCHOR) == 1
    t = t.replace(CSS_ANCHOR, CSS + CSS_ANCHOR, 1)
    t = t.replace(VM_ANCHOR, VM_ADD + VM_ANCHOR, 1)
    t = t.replace(DARK_ANCHOR, "\n" + DARK + DARK_ANCHOR[1:], 1)
    out = html[:m.start(2)] + json.dumps(t).replace('</', '<\\u002F') + html[m.end(2):]
    open(PAGE, "w", encoding="utf-8").write(out)
    print("applied; template", len(t))

if __name__ == "__main__":
    main()
