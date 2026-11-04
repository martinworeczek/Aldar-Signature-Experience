"""Customer Stories: template guards for tools/apply_features.py (always on, not a switch).

Data: data/customer-stories.js (window.CS_DATA, 45 records, one hidden). apply_features.py inlines it
into <head> so it is loaded eagerly with the page.

  - the Customer Stories tab (view 'stories'): hero with a three-cell stat bar, line and link filter
    chips, and a wall of read-only cards. "Read in full" lifts one card's clamps.
  - "Stories from the floor": the last numbered chapter in an experience's detail view, shown only
    when the experience has stories. "All stories" opens the tab.
  - a small "N" marker before "Open" on the three 2a card templates (catalogue, Hospitality, pillar).
  - the sidebar entry (Overview group, after Signature Experiences, marked New), the title entry and
    a search (Cmd-K) entry.

Hidden records (hidden: true) are kept out of every count and list. A story links to an experience
through experience.id, which must equal the experience id in the line data.
"""
import json, re

DATA_PATH = "data/customer-stories.js"


def data_js():
    """The CS_DATA assignment for <head>, minified and safe inside a <script> tag."""
    src = open(DATA_PATH, encoding="utf-8").read()
    m = re.search(r"window\.CS_DATA\s*=\s*(\{.*\})\s*;?\s*$", src, re.S)
    assert m, "data/customer-stories.js must assign window.CS_DATA = {...}"
    d = json.loads(m.group(1))
    assert isinstance(d.get("stories"), list), "CS_DATA.stories missing"
    return "window.CS_DATA=" + json.dumps(d, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/") + ";"


# ---------------------------------------------------------------------------------------------
WALL = """  <!-- ===================== CUSTOMER STORIES ===================== -->
  <sc-if value="{{ vStories }}" hint-placeholder-val="{{ false }}">
  <section style="max-width:none;padding:26px 28px 0">
    <div data-cs-hero="1" style="position:relative;height:400px;background:#0A1014;overflow:hidden;border-radius:20px;border:1px solid rgba(232,185,106,.26);box-shadow:0 30px 70px -34px rgba(0,0,0,.85);display:flex;flex-direction:column;justify-content:flex-end">
      <div style="position:absolute;inset:0;background:radial-gradient(circle at 50% 54%,#16212B,#090E12 72%)"></div>
      <div style="position:absolute;inset:0;overflow:hidden">
        <sc-for list="{{ cs.heroMarks }}" as="g" hint-placeholder-count="6"><span style="{{ g.css }}">&#10077;</span></sc-for>
      </div>
      <div style="position:absolute;inset:0;background:radial-gradient(44% 42% at 50% 52%,rgba(9,14,18,.9),rgba(9,14,18,.5) 64%,transparent)"></div>
      <div style="position:relative;padding:40px 48px 26px;text-align:center">
        <div style="display:inline-flex;align-items:center;gap:9px"><span style="width:7px;height:7px;border-radius:50%;background:#E8B96A"></span><span style="font-size:10.5px;font-weight:700;letter-spacing:.24em;text-transform:uppercase;color:#E8B96A">Aldar &middot; Customer Stories</span></div>
        <div style="font-family:'Poppins',sans-serif;font-size:clamp(30px,3.2vw,42px);font-weight:300;line-height:1.12;letter-spacing:-.015em;color:#FFFFFF;margin:16px auto 0;max-width:26ch;text-wrap:pretty">Signature experiences, as our customers lived them</div>
        <div style="font-family:'Poppins',sans-serif;font-size:15px;font-weight:300;color:#C6CDD2;line-height:1.6;margin:12px auto 0;max-width:54ch;text-wrap:pretty">Moments told by the colleagues who made them &mdash; each one an expression of a Signature Experience in the field.</div>
        <div data-cs-bar="1" style="display:flex;max-width:620px;margin:22px auto 0;background:rgba(10,16,20,.6);border:1px solid rgba(232,185,106,.34);border-radius:12px;overflow:hidden;backdrop-filter:blur(7px)">
          <sc-for list="{{ cs.heroBar }}" as="d" hint-placeholder-count="3">
            <div style="{{ d.cellCss }}">
              <div style="font-size:7.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#E8B96A">{{ d.kicker }}</div>
              <div style="font-size:12px;font-weight:500;color:#F6F3EC;margin-top:4px;line-height:1.25">{{ d.label }}</div>
            </div>
          </sc-for>
        </div>
      </div>
    </div>
  </section>
  <section data-cs-wall="1" style="max-width:none;padding:20px 40px 40px">
    <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;background:var(--panel);border:1px solid var(--line);border-radius:16px;box-shadow:0 16px 40px rgba(74,56,26,.13);padding:11px 18px">
      <sc-for list="{{ cs.lineChips }}" as="c" hint-placeholder-count="6"><button sc-camel-on-click="{{ c.onClick }}" style="{{ c.css }}"><span style="width:7px;height:7px;border-radius:50%;background:{{ c.dot }};flex-shrink:0"></span>{{ c.label }}<span style="opacity:.6">{{ c.n }}</span></button></sc-for>
      <span style="width:1px;height:22px;background:var(--line);margin:0 6px"></span>
      <sc-for list="{{ cs.linkChips }}" as="c" hint-placeholder-count="2"><button sc-camel-on-click="{{ c.onClick }}" style="{{ c.css }}">{{ c.label }}<span style="opacity:.6">{{ c.n }}</span></button></sc-for>
      <span style="margin-left:auto;font-size:12px;color:var(--faint);padding-right:4px">{{ cs.countLabel }}</span>
    </div>
    <div style="padding:22px 0 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(320px,100%),1fr));gap:18px">
      <sc-for list="{{ cs.cards }}" as="s" hint-placeholder-count="9">
        <div data-cs-card="1" style="position:relative;background:var(--panel);border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;transition:transform .25s cubic-bezier(.2,.7,.2,1),box-shadow .25s" style-hover="transform:translateY(-4px);box-shadow:0 22px 48px rgba(40,30,10,.14)">
          <div style="position:relative;aspect-ratio:16/7;background:{{ s.grad }};background-size:cover;background-position:center">
            <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.2),rgba(0,0,0,0) 40%)"></div>
            <span style="position:absolute;top:12px;left:12px;display:inline-flex;align-items:center;gap:7px;background:rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.22);color:#fff;border-radius:999px;padding:5px 11px;font-size:10px;font-weight:500;letter-spacing:.16em;text-transform:uppercase"><span style="width:6px;height:6px;border-radius:50%;background:{{ s.dot }}"></span>{{ s.line }}</span>
          </div>
          <div style="padding:20px 22px 22px;display:flex;flex-direction:column;gap:12px;flex:1">
            <div style="{{ s.titleCss }}">{{ s.title }}</div>
            <div style="{{ s.storyCss }}">{{ s.story }}</div>
            <div style="margin-top:2px;padding-top:14px;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:6px"><span style="font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);font-weight:600">What made it memorable</span><span style="{{ s.memCss }}">{{ s.memorable }}</span></div>
            <div style="margin-top:auto;padding-top:12px;display:flex;justify-content:space-between;align-items:center;gap:10px">
              <button sc-camel-on-click="{{ s.toggle }}" style="font-family:inherit;font-size:11px;font-weight:500;color:var(--gold);background:transparent;border:0;padding:0;cursor:pointer;letter-spacing:.04em;white-space:nowrap">{{ s.moreLabel }}</button>
              <span style="{{ s.linkCss }}">{{ s.linkLabel }}</span>
            </div>
          </div>
        </div>
      </sc-for>
    </div>
  </section>
  </sc-if>

  <!-- ===================== PAGE HEADER (non-dashboard views) ===================== -->"""

CHAPTER = """Submit &amp; review</b>.</div></sc-if>
        </div>
      </div>

      <sc-if value="{{ modal.hasStories }}" hint-placeholder-val="{{ false }}">
      <div data-cs-chapter="1" class="{{ modal.ch.stories.cls }}"><div><div class="d3-ch-head"><div class="d3-num">{{ modal.ch.stories.n }}</div><div class="d3-lbl">Stories from the floor</div></div><div style="font-size:12px;color:rgba(255,255,255,.55);margin-top:6px;line-height:1.5">How colleagues have brought this experience to life for a real customer.</div><button sc-camel-on-click="{{ modal.csAll }}" style="display:inline-flex;align-items:center;gap:8px;margin-top:16px;padding:9px 14px;border-radius:999px;border:1px solid rgba(232,185,106,.5);background:transparent;color:#E8B96A;font-family:inherit;font-size:11px;letter-spacing:.12em;text-transform:uppercase;cursor:pointer;white-space:nowrap" style-hover="background:rgba(232,185,106,.1)">All stories &#8594;</button></div>
        <div style="min-width:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(240px,100%),1fr));gap:12px;align-content:start">
          <sc-for list="{{ modal.stories }}" as="s" hint-placeholder-count="0">
            <div style="background:#1E1E1E;border:1px solid rgba(255,255,255,.08);border-radius:12px;overflow:hidden;display:flex;flex-direction:column">
              <div style="height:6px;background:{{ s.grad }}"></div>
              <div style="padding:16px 18px 18px;display:flex;flex-direction:column;gap:8px"><div style="font-size:10.5px;color:rgba(255,255,255,.5);letter-spacing:.06em">{{ s.place }}</div><div style="font-size:16px;font-weight:500;line-height:1.25;color:#fff">{{ s.title }}</div><div style="font-size:12.5px;line-height:1.55;color:rgba(255,255,255,.72);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden">{{ s.story }}</div><div style="font-size:12px;line-height:1.45;color:#E8B96A;font-style:italic;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">{{ s.memorable }}</div><div style="font-size:11px;color:rgba(255,255,255,.5);margin-top:2px">{{ s.who }}</div></div>
            </div>
          </sc-for>
        </div>
      </div>
      </sc-if>
"""

OPEN_SPAN = '<span style="font-size:11px;font-weight:500;color:#E8B96A;white-space:nowrap;text-shadow:none">Open →</span>'
MARKER = ('<span style="display:flex;align-items:center;gap:10px"><sc-if value="{{ card.c2HasStories }}" hint-placeholder-val="{{ false }}">'
          '<span title="Customer stories" style="display:inline-flex;align-items:center;gap:5px;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#E8B96A;border:1px solid rgba(232,185,106,.5);border-radius:999px;padding:3px 9px;white-space:nowrap;text-shadow:none">&#10077; {{ card.c2StoryN }}</span></sc-if>'
          + OPEN_SPAN + '</span>')

METHODS = r"""  // ===== Customer stories (data/customer-stories.js -> window.CS_DATA) =====
  _csAll() { return ((window.CS_DATA && window.CS_DATA.stories) || []).filter(s => s && !s.hidden); }
  _csFor(expId) { return expId ? this._csAll().filter(s => s.experience && s.experience.id === expId) : []; }
  _csDeco(s) {
    const LC = { Development: '#C9A24A', Estates: '#A5443A', Hospitality: '#D08A4C', Retail: '#D9786A', Education: '#5A82B5', Corporate: '#4FB58C' };
    const G = { Development: 'linear-gradient(160deg,#5A4A22,#1A1508)', Estates: 'linear-gradient(160deg,#5E2A24,#1B0D0B)', Hospitality: 'linear-gradient(160deg,#5E3F22,#1C130A)', Retail: 'linear-gradient(160deg,#5B3330,#1C0F0E)', Education: 'linear-gradient(160deg,#2E4160,#0E141E)', Corporate: 'linear-gradient(160deg,#24473A,#0B1A14)' };
    const who = s.colleagues ? String(s.colleagues).split(/·|\n/)[0].replace(/^Aldar colleague:\s*/, '').trim().slice(0, 60) : (s.category || '');
    const ex = s.experience;
    const linkBase = { display: 'inline-block', padding: '6px 12px', borderRadius: '999px', fontSize: '11px', fontWeight: 500, whiteSpace: 'nowrap', maxWidth: '62%', overflow: 'hidden', textOverflow: 'ellipsis' };
    // fixed line boxes keep every card in a row aligned; "Read in full" lifts the clamps for that card only
    const open = !!(this.state.csExp && this.state.csExp[s.id]);
    const clamp = (n, lh) => open ? {} : { height: (n * lh) + 'px', display: '-webkit-box', WebkitLineClamp: n, WebkitBoxOrient: 'vertical', overflow: 'hidden' };
    const titleCss = Object.assign({ fontFamily: "'Fraunces',serif", fontSize: '23px', lineHeight: '26px', letterSpacing: '-.01em', color: 'var(--ink)', textWrap: 'pretty' }, clamp(2, 26));
    const storyCss = Object.assign({ fontSize: '13px', lineHeight: '21px', color: 'var(--muted)', textWrap: 'pretty' }, clamp(5, 21));
    const memCss = Object.assign({ fontSize: '13.5px', lineHeight: '21px', color: 'var(--ink)', textWrap: 'pretty' }, clamp(3, 21));
    const photo = s.photo ? 'url("' + s.photo + '"), ' : '';
    return Object.assign({}, s, { place: s.place || s.category || '', who: who, dot: LC[s.line] || '#E8B96A', grad: photo + (G[s.line] || G.Corporate), titleCss, storyCss, memCss,
      moreLabel: open ? 'Show less' : 'Read in full',
      toggle: (e) => { if (e && e.stopPropagation) e.stopPropagation(); const m = Object.assign({}, this.state.csExp || {}); m[s.id] = !open; this.setState({ csExp: m }); },
      linkLabel: ex ? (ex.sure ? '↗ ' + ex.name : '? ' + ex.name) : '+ Link to an experience',
      linkCss: Object.assign(linkBase, ex ? { border: '1px solid #C9A24A', background: ex.sure ? '#FBF4E2' : 'transparent', color: '#8A6A1F' } : { border: '1px dashed #BDB5A3', background: 'transparent', color: 'var(--muted)' }) });
  }
  _csVM(S) {
    const all = this._csAll();
    const lines = ['Development', 'Estates', 'Hospitality', 'Retail', 'Education'];
    const LC = { Development: '#C9A24A', Estates: '#A5443A', Hospitality: '#D08A4C', Retail: '#D9786A', Education: '#5A82B5' };
    const line = S.csLine || 'all', link = S.csLink || 'all';
    const chip = (on) => ({ fontFamily: 'inherit', display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '8px 14px', borderRadius: '999px', fontSize: '12px', cursor: 'pointer', whiteSpace: 'nowrap', transition: '.15s', border: '1px solid ' + (on ? 'var(--ink)' : 'var(--line)'), background: on ? 'var(--ink)' : 'var(--panel)', color: on ? '#F6F3EC' : 'var(--ink)' });
    const lineChips = [{ label: 'All lines', n: all.length, dot: line === 'all' ? '#E8B96A' : '#1A1A1A', css: chip(line === 'all'), onClick: () => this.setState({ csLine: 'all' }) }]
      .concat(lines.map(l => ({ label: l, n: all.filter(s => s.line === l).length, dot: LC[l], css: chip(line === l), onClick: () => this.setState({ csLine: l }) })));
    const nLinked = all.filter(s => s.experience).length;
    const linkChips = [{ label: 'Linked to an experience', n: nLinked, css: chip(link === 'linked'), onClick: () => this.setState({ csLink: link === 'linked' ? 'all' : 'linked' }) }, { label: 'Awaiting a link', n: all.length - nLinked, css: chip(link === 'open'), onClick: () => this.setState({ csLink: link === 'open' ? 'all' : 'open' }) }];
    const f = all.filter(s => (line === 'all' || s.line === line) && (link === 'all' || (link === 'linked' ? !!s.experience : !s.experience)));
    const heroMarks = [[6, 10, 150, .07], [20, 70, 90, .05], [40, 28, 220, .06], [62, 76, 120, .05], [78, 14, 170, .07], [90, 60, 80, .05]].map(m => ({ css: { position: 'absolute', left: m[0] + '%', top: m[1] + '%', fontFamily: "'Fraunces',serif", fontSize: m[2] + 'px', lineHeight: 1, color: '#E8B96A', opacity: m[3], transform: 'translate(-50%,-50%)', userSelect: 'none', pointerEvents: 'none' } }));
    const cell = (i) => ({ flex: 1, padding: '12px 14px', textAlign: 'center', borderLeft: i ? '1px solid rgba(232,185,106,.22)' : 0 });
    const heroBar = [{ kicker: 'Stories', label: all.length + ' told by colleagues' }, { kicker: 'Business lines', label: lines.filter(l => all.some(s => s.line === l)).length + ' represented' }, { kicker: 'Linked', label: nLinked + ' to a Signature Experience' }].map((d, i) => Object.assign(d, { cellCss: cell(i) }));
    return { lineChips, linkChips, cards: f.map(s => this._csDeco(s)), countLabel: f.length === all.length ? all.length + ' stories' : f.length + ' of ' + all.length + ' stories', heroMarks, heroBar };
  }

  // ===== Portfolio Discovery helpers =====
"""

CH_OLD = "      // chapters: number only those that render, in display order\n"
CH_NEW = ("      // customer stories: the last chapter, only when this experience has some\n"
          "      { const _st = this._csFor(S.selected); modal.hasStories = _st.length > 0; modal.stories = _st.map(s => this._csDeco(s)); modal.csAll = () => this.go('stories'); }\n"
          + CH_OLD)

GUARDS = [
    ("  <!-- ===================== PAGE HEADER (non-dashboard views) ===================== -->", WALL, 1),
    ("Submit &amp; review</b>.</div></sc-if>\n        </div>\n      </div>\n", CHAPTER, 1),
    (OPEN_SPAN, MARKER, 3),
    ("  // ===== Portfolio Discovery helpers =====\n", METHODS, 1),
    (CH_OLD, CH_NEW, 1),
    ("      modal.ch = {};\n", "      if (modal.hasStories) _ch.push(['stories', true]);\n      modal.ch = {};\n", 1),
    ("['scope', 'deploy', 'progress', 'benefits', 'tp', 'audit', 'assets', 'photos'].forEach", "['scope', 'deploy', 'progress', 'benefits', 'tp', 'audit', 'assets', 'photos', 'stories'].forEach", 1),
    ("c2Defining: !!c.defining, c2NotDefining: !c.defining });", "c2Defining: !!c.defining, c2NotDefining: !c.defining, c2HasStories: this._csFor(c.id).length > 0, c2StoryN: this._csFor(c.id).length });", 1),
    ("vDashboard: V === 'dashboard', ", "vDashboard: V === 'dashboard', vStories: V === 'stories', ", 1),
    ("vHeader: V !== 'activity' && ", "vHeader: V !== 'stories' && V !== 'activity' && ", 1),
    ("    return Object.assign({\n      cmd: cmd,\n", "    return Object.assign({\n      cs: this._csVM(S),\n      cmd: cmd,\n", 1),
    ("iconItem('⌕', 'Signature Experiences', 'catalogue'), ", "iconItem('⌕', 'Signature Experiences', 'catalogue'), newItem(iconItem('❝', 'Customer Stories', 'stories')), ", 1),
    ("assistant: ['Overview', (window.__SIG_OFF", "stories: ['Overview', 'Customer Stories', ''], assistant: ['Overview', (window.__SIG_OFF", 1),
    ("['catalogue', 'All Signature Experiences', 'Every experience, filterable'],\n", "['catalogue', 'All Signature Experiences', 'Every experience, filterable'],\n      ['stories', 'Customer Stories', 'Moments told by the colleagues who made them'],\n", 1),
]
