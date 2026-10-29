"""Apply the "2a Full-bleed Portrait" catalogue card (see docs/card-2a-README.md).

Visual-only: adds display fields (card.c2*) and outline-pill styles for the existing
Compare/Save actions, then swaps the three grid card templates (catCards grid mode,
hpCards, hpCatCards). Data, filtering, click handlers and list mode are untouched.
Idempotent: refuses to run twice.
"""
import json, re

PAGE = "index.html"

CARD = '''<div sc-camel-on-click="{{ card.open }}" style="position:relative;aspect-ratio:3/4;border-radius:10px;overflow:hidden;background:#000;cursor:pointer;box-shadow:0 16px 36px rgba(21,38,50,.16);transition:transform .2s,box-shadow .2s" style-hover="transform:translateY(-4px);box-shadow:0 28px 56px rgba(21,38,50,.26)">
          <div style="{{ card.c2Img }}"></div>
          <sc-if value="{{ card.c2NoImage }}" hint-placeholder-val="{{ false }}"><div style="position:absolute;inset:0;background:radial-gradient(60% 40% at 50% 38%,rgba(232,185,106,.14),transparent 70%)"></div><div style="position:absolute;top:38%;left:50%;transform:translate(-50%,-50%);text-align:center;color:rgba(246,243,236,.5)"><div style="font-size:30px;color:rgba(232,185,106,.5);line-height:1">◎</div><div style="font-size:10px;letter-spacing:.16em;text-transform:uppercase;margin-top:10px;white-space:nowrap">Imagery coming soon</div></div></sc-if>
          <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.32) 0%,rgba(0,0,0,0) 18%,rgba(0,0,0,0) 36%,rgba(0,0,0,.58) 54%,rgba(0,0,0,.84) 72%,rgba(0,0,0,.92) 100%)"></div>
          <div style="position:absolute;top:16px;left:16px;right:16px;display:flex;justify-content:space-between;align-items:center;gap:8px">
            <sc-if value="{{ card.c2Defining }}" hint-placeholder-val="{{ false }}"><span style="flex-shrink:0;font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#0A1014;background:#E8B96A;border-radius:999px;padding:4px 10px;display:inline-flex;align-items:center;gap:6px"><span style="font-size:9px">✦</span>Defining</span></sc-if>
            <sc-if value="{{ card.c2NotDefining }}" hint-placeholder-val="{{ true }}"><span></span></sc-if>
            <span style="font-size:10px;font-weight:500;letter-spacing:.1em;text-transform:uppercase;color:#FFF;background:rgba(0,0,0,.66);border:1px solid rgba(255,255,255,.18);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);border-radius:999px;padding:4px 10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:60%">{{ card.c2Group }}</span>
          </div>
          <div style="position:absolute;left:0;right:0;bottom:0;padding:0 20px 18px;color:#FFF;text-shadow:0 1px 2px rgba(0,0,0,.6),0 0 18px rgba(0,0,0,.5)">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#FFF;text-shadow:0 1px 3px rgba(0,0,0,.85),0 0 10px rgba(0,0,0,.6)"><span style="flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ card.c2Pillar }}</span><span style="flex-shrink:0;display:inline-flex;align-items:center;gap:7px;white-space:nowrap;color:#FFF"><span style="width:7px;height:7px;border-radius:50%;background:{{ card.c2StageDot }};box-shadow:0 0 0 2px rgba(0,0,0,.35)"></span>{{ card.c2Stage }}</span></div>
            <div style="height:57px;margin-top:10px;display:flex;flex-direction:column;justify-content:flex-end;overflow:hidden"><div style="display:block;width:100%;min-width:0"><div data-c2-title="1" style="font-family:'Fraunces',serif;font-size:26px;font-weight:400;line-height:1.08;max-height:2.16em;text-wrap:pretty;color:#FFF;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere">{{ card.name }}</div></div></div>
            <div style="font-size:12px;font-weight:400;line-height:1.5;height:36px;color:#FFF;margin-top:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden">{{ card.essence }}</div>
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:16px;padding-top:14px;border-top:1px solid rgba(246,243,236,.18)">
              <div style="display:flex;gap:6px;flex-wrap:nowrap">
                <button sc-camel-on-click="{{ card.act.onCmp }}" style="{{ card.act.c2CmpCss }}" style-hover="background:rgba(246,243,236,.12)">{{ card.act.cmpLabel }}</button>
                <button sc-camel-on-click="{{ card.act.onSave }}" style="{{ card.act.c2SaveCss }}" style-hover="background:rgba(246,243,236,.12)">{{ card.act.saveLabel }}</button>
              </div>
              <span style="font-size:11px;font-weight:500;color:#E8B96A;white-space:nowrap;text-shadow:none">Open →</span>
            </div>
          </div>
        </div>'''

GRID = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:18px">'

ACT_ANCHOR = "        return {\n          cmpLabel: inC ? '\\u2713 In compare' : '\\u2726 Compare',"
ACT_ADD = """        // 2a card: the same Compare/Save as outline pills on the photograph, selected states kept
        const c2Base = { fontFamily: 'inherit', fontSize: '11px', fontWeight: 500, color: '#FFFFFF', background: 'transparent', border: '1px solid rgba(246,243,236,.3)', borderRadius: '999px', padding: '6px 13px', cursor: 'pointer', whiteSpace: 'nowrap', transition: '.15s', textShadow: 'none' };
        const c2CmpCss = Object.assign({}, c2Base, inC ? { background: 'var(--sage,#7B916C)', border: '1px solid var(--sage,#7B916C)' } : {});
        const c2SaveCss = Object.assign({}, c2Base, inB ? { color: '#0A1014', background: '#E8B96A', border: '1px solid #E8B96A' } : {});
"""

DECO_ANCHOR = """        rowImageStyle: { position: 'absolute', inset: 0, backgroundImage: (c.imageStyle || {}).backgroundImage, backgroundSize: 'cover', backgroundPosition: 'center 32%' }
      }));
"""
DECO_ADD = """      // ---- 2a full-bleed portrait card: display-only fields for the three grid lists ----
      const _c2Dot = (label) => {
        const s = String(label || '').toLowerCase();
        if (/live|implemented|audit/.test(s)) return '#B5EBBE';
        if (/implementation|progress|flagged/.test(s)) return '#F5CD85';
        if (/park|depriorit|backlog|discontinu|2027|hold/.test(s)) return 'rgba(255,255,255,.85)';
        return '#EFE2C6';
      };
      const _c2Img = (src) => ({ position: 'absolute', inset: 0, backgroundSize: 'cover', backgroundPosition: 'center 35%', backgroundImage: src ? 'url("' + src + '")' : 'linear-gradient(160deg,#2B3136 0%,#171E23 60%,#0E1418 100%)' });
      const _c2Src = (bg) => { const m = /url\\((['"]?)(.*?)\\1\\)/.exec(bg || ''); return m ? m[2] : ''; };
      const _c2 = (c, src, group, pillar, stage) => Object.assign({}, c, { c2Img: _c2Img(src), c2NoImage: !src, c2Group: group || '', c2Pillar: pillar || '', c2Stage: stage || '', c2StageDot: _c2Dot(stage), c2Defining: !!c.defining, c2NotDefining: !c.defining });
      hpExtra.catCards = hpExtra.catCards.map(c => _c2(c, c.hasImage ? _c2Src((c.imageStyle || {}).backgroundImage) : '', c.badgeLabel, c.pillarEyebrow, c.stageLabel));
      hpExtra.hpCards = hpExtra.hpCards.map(c => _c2(c, c.image, c.group || 'Hospitality', c.pillarName, c.statusLabel));
      hpExtra.hpCatCards = hpExtra.hpCatCards.map(c => _c2(c, c.image, c.group || 'Hospitality', c.pillarName, c.statusLabel));
"""

def replace_card(t, list_name, start_marker):
    """Swap the grid wrapper + card <div> inside the sc-for over list_name, after start_marker."""
    a = t.index(start_marker)
    f = t.index('<sc-for list="{{ %s }}"' % list_name, a)
    g = t.rindex('<div style="display:grid', max(0, a - 600), f)
    ge = t.index('>', g) + 1
    t = t[:g] + GRID + t[ge:]
    f = t.index('<sc-for list="{{ %s }}"' % list_name, a)
    cs = t.index('<div sc-camel-on-click="{{ card.open }}"', f)
    ce = t.index('</sc-for>', cs)
    return t[:cs] + CARD + '\n      ' + t[ce:]

def main():
    html = open(PAGE, encoding="utf-8").read()
    m = re.search(r'(<script type="__bundler/template">\s*)(".*?")(\s*</script>)', html, re.S)
    t = json.loads(m.group(2))
    assert 'c2StageDot' not in t, "card 2a already applied"
    assert t.count(ACT_ANCHOR) == 1 and t.count(DECO_ANCHOR) == 1
    t = t.replace(ACT_ANCHOR, ACT_ADD + ACT_ANCHOR + "\n          c2CmpCss, c2SaveCss,", 1)
    t = t.replace(DECO_ANCHOR, DECO_ANCHOR + DECO_ADD, 1)
    # the Hospitality line page rebuilds hpCards later in renderVals, so decorate it there too
    HP_ANCHOR = "        hpExtra.hpCards = hpExtra.hpCards.map(c => Object.assign({}, c, { act: _actFor(c.id) }));\n"
    assert t.count(HP_ANCHOR) == 1
    t = t.replace(HP_ANCHOR, HP_ANCHOR + "        // 2a card fields too — this list is rebuilt after the shared decoration above\n        hpExtra.hpCards = hpExtra.hpCards.map(c => _c2(c, c.image, c.group || 'Hospitality', c.pillarName, c.statusLabel));\n", 1)
    t = replace_card(t, 'catCards', '<sc-if value="{{ catIsGrid }}"')
    t = replace_card(t, 'hpCatCards', '{{ hpCatCount }} experiences')
    t = replace_card(t, 'hpCards', '<sc-for list="{{ hpCards }}"')
    out = html[:m.start(2)] + json.dumps(t).replace('</', '<\\u002F') + html[m.end(2):]
    open(PAGE, "w", encoding="utf-8").write(out)
    print("applied; template", len(t))

if __name__ == "__main__":
    main()
