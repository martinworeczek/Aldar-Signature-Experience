"""Apply the CX Time reader "6a Welcome Home" (docs/cxtime-reader-6a/README.md) to the hub's CX Time
module (manifest asset 59c00ad5): replaces the 5a reader block and adds the values it needs.
Usage: python3 -I tools/apply_reader_6a.py   (idempotent: refuses to run twice)"""
import base64, gzip, json, re, sys

PAGE, ASSET = "index.html", "59c00ad5"

READER = r'''<!-- ============ READER · 6a Welcome Home ============ -->
    <sc-if value="{{ isReader }}" hint-placeholder-val="{{ false }}">
    <div data-atl-reader="1" data-atl-reader6a="1" class="atl-view" key="{{ cur.id }}" style="background:#122216;border-radius:14px;overflow:hidden;color:#FFFFFF;font-family:'Poppins','Helvetica Neue',Arial,sans-serif">

      <div data-atl-rdhero="1" style="position:relative;min-height:min(820px,92vh);overflow:hidden;background:#122216;display:flex;flex-direction:column;justify-content:flex-end">
        <div style="{{ cur.rdHeroImg }}"></div>
        <div style="position:absolute;inset:0;background:linear-gradient(0deg,rgba(18,34,22,.96) 0%,rgba(18,34,22,.84) 34%,rgba(18,34,22,.34) 58%,rgba(18,34,22,0) 78%)"></div>
        <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(18,14,10,.55) 0%,rgba(18,14,10,0) 22%)"></div>

        <button onClick="{{ back }}" title="Back to the library" aria-label="Back to the library" style="position:absolute;left:24px;top:18px;z-index:5;width:52px;height:52px;padding:0;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(18,14,10,.68);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid rgba(243,223,164,.5);color:#F3DFA4;font-family:inherit;font-size:20px;line-height:1;cursor:pointer;box-shadow:0 8px 24px rgba(12,10,8,.25);transition:background .15s" style-hover="background:rgba(217,179,92,.25)">←</button>


        <div data-atl-rdbody="1" style="position:relative;z-index:3;padding:96px clamp(24px,6vw,120px) 28px;display:flex;flex-direction:column;gap:20px">
          <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
            <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 13px;border-radius:999px;border:1px solid rgba(243,223,164,.6);background:rgba(18,14,10,.45);font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:#F3DFA4;white-space:nowrap"><span style="width:7px;height:7px;border-radius:50%;background:#D9B35C;box-shadow:0 0 10px #D9B35C"></span>{{ cur.rdPill }}</span>
            <span style="font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:rgba(243,223,164,.75)">{{ cur.rdMeta }}</span>
          </div>
          <h1 style="margin:0;font-size:clamp(34px,5vw,88px);font-weight:200;line-height:.98;letter-spacing:-.03em;color:#FFFFFF;text-wrap:pretty;max-width:18ch">{{ cur.title }}</h1>
          <div data-atl-rdsplit="1" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:36px clamp(24px,4vw,50px);padding-top:22px;border-top:1px solid rgba(243,223,164,.3)">
            <div style="display:flex;flex-direction:column;gap:12px"><span style="font-size:12px;letter-spacing:.28em;text-transform:uppercase;color:#F3DFA4">The experience</span><span style="font-size:clamp(15px,1.2vw,19px);font-weight:300;line-height:1.55;color:rgba(255,255,255,.92);text-wrap:pretty">{{ cur.rdExperience }}</span>
              <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px"><a href="{{ cur.sourceUrl }}" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:8px;padding:11px 20px;border-radius:999px;background:linear-gradient(90deg,#F7E7BE,#D9B35C);color:#0C1C27;font-size:11px;letter-spacing:.18em;text-transform:uppercase;font-weight:500;text-decoration:none;white-space:nowrap" style-hover="filter:brightness(1.06)">{{ cur.rdCta }} ↗</a><button onClick="{{ cur.onSave }}" title="Save to a collection" style="{{ cur.rdSave }}">{{ cur.saveLabel }}</button></div>
            </div>
            <div data-atl-rdopp="1" style="display:flex;flex-direction:column;gap:12px;padding-left:clamp(0px,3vw,40px);border-left:1px solid rgba(243,223,164,.35)"><span style="font-size:12px;letter-spacing:.28em;text-transform:uppercase;color:#F3DFA4">Signature Experience Opportunity</span><span style="font-size:clamp(17px,1.4vw,22px);font-weight:300;line-height:1.4;color:#F3DFA4;text-wrap:pretty">{{ cur.why }}</span>
              <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px"><sc-for list="{{ cur.rdLines }}" as="ln" hint-placeholder-count="3"><span style="display:inline-flex;align-items:center;gap:7px;font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:rgba(243,223,164,.85);border:1px solid rgba(243,223,164,.3);border-radius:999px;padding:5px 11px;white-space:nowrap"><span style="{{ ln.dot }}"></span>{{ ln.name }}</span></sc-for></div>
            </div>
          </div>
        </div>
      </div>

      <section style="padding:32px clamp(24px,6vw,120px) clamp(40px,6vh,72px)">
        <div style="display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:20px"><span style="font-size:12px;letter-spacing:.28em;text-transform:uppercase;color:#F3DFA4">More in this edition</span><button onClick="{{ back }}" style="margin-left:auto;font-family:inherit;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#F3DFA4;background:transparent;border:1px solid rgba(243,223,164,.35);border-radius:999px;padding:8px 16px;cursor:pointer;white-space:nowrap" style-hover="background:rgba(243,223,164,.1)">{{ allStoriesLabel }}</button></div>
        <div data-atl-rdrail="1" style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:18px">
          <sc-for list="{{ cur.rdRail }}" as="r" hint-placeholder-count="5">
            <div data-atl-card="1" onClick="{{ r.select }}" style="position:relative;aspect-ratio:3/4;border-radius:14px;overflow:hidden;background:#0B1A10;cursor:pointer;transition:transform .3s cubic-bezier(.2,.7,.2,1),box-shadow .3s;box-shadow:0 1px 0 rgba(243,223,164,.08) inset" style-hover="transform:translateY(-6px);box-shadow:0 24px 50px rgba(0,0,0,.35),0 0 0 1px rgba(243,223,164,.35) inset">
              <div style="{{ r.img }}"></div>
              <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.45) 0%,rgba(0,0,0,0) 24%,rgba(0,0,0,0) 38%,rgba(0,0,0,.62) 58%,rgba(0,0,0,.9) 100%)"></div>
              <div style="position:absolute;top:14px;left:14px;right:14px;display:flex;justify-content:space-between;align-items:center"><span style="font-size:10px;font-weight:500;letter-spacing:.2em;text-transform:uppercase;color:#FFFFFF;background:rgba(0,0,0,.62);border:1px solid rgba(255,255,255,.22);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);border-radius:999px;padding:5px 11px;white-space:nowrap">{{ r.fmt }}</span><span style="font-size:11px;font-weight:500;color:#FFFFFF;background:rgba(0,0,0,.62);border:1px solid rgba(255,255,255,.22);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);border-radius:999px;padding:5px 9px">{{ r.n }}</span></div>
              <div style="position:absolute;left:0;right:0;bottom:0;padding:0 18px 20px;display:flex;flex-direction:column;justify-content:flex-end;gap:10px"><div style="width:22px;height:1px;background:#D9B35C"></div><div style="height:69px;font-size:18px;font-weight:400;line-height:23px;letter-spacing:-.01em;color:#FFFFFF;text-wrap:pretty;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden">{{ r.title }}</div><div style="font-size:10px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;color:#F3DFA4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ r.source }}</div></div>
            </div>
          </sc-for>
        </div>
      </section>
    </div>
    </sc-if>
'''

CSS = '''
  /* 6a reader. Its layout follows the reader's own width (a container query), not the window:
     in the hub the sidebar narrows it, so window breakpoints would misjudge it.
     - five cards across while there is room; narrower, they become a swipeable row
     - once the two columns stack, the opportunity column takes a top rule instead of a left one
     - once stacked, the hero's green fade climbs higher, because the text makes the hero tall */
  [data-atl-reader6a] { container-type: inline-size; }
  @container (max-width: 980px) {
    [data-atl-rdrail] { grid-template-columns: none !important; grid-auto-flow: column; grid-auto-columns: minmax(190px, 31%); overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 8px; -webkit-overflow-scrolling: touch; }
    [data-atl-rdrail] > div { scroll-snap-align: start; }
  }
  @container (max-width: 880px) {
    [data-atl-rdopp] { border-left: 0 !important; padding-left: 0 !important; border-top: 1px solid rgba(243,223,164,.2); padding-top: 22px; }
    [data-atl-rdhero] > div:nth-child(2) { background: linear-gradient(0deg, rgba(18,34,22,.97) 0%, rgba(18,34,22,.9) 48%, rgba(18,34,22,.62) 68%, rgba(18,34,22,0) 90%) !important; }
  }
  @container (max-width: 640px) {
    [data-atl-rdbody] { padding-top: 240px !important; }
    [data-atl-rdrail] { grid-auto-columns: 62%; }
  }
</style>
</helmet>'''

LOGIC_ANCHOR = "    const _relFirst = (base.related || []).map(id => byId[id]).filter(Boolean);"
LOGIC = r'''    // ---- 6a Welcome Home reader values
    {
      const FMT6 = { read: 'Article', watch: 'Video', listen: 'Podcast' };
      const ACT6 = { read: 'Read the article', watch: 'Watch the video', listen: 'Listen to the episode' };
      const LC6 = { Corporate: '#4FB58C', Development: '#C9A35A', Education: '#8FB7C4', Estates: '#D9786A', Hospitality: '#E0AE82', Retail: '#E0927C', 'All lines': '#E8B96A' };
      const norm6 = l => /PM|Community|Estates/i.test(l) ? 'Estates' : l;
      const num6 = {}; rows.forEach((it, k) => { num6[it.id] = String(k + 1).padStart(2, '0'); });
      const relIds6 = (base.related || []).filter(id => byId[id] && id !== base.id);
      const railIds6 = relIds6.concat(rows.map(i => i.id).filter(id => id !== base.id && relIds6.indexOf(id) < 0)).slice(0, 5);
      const nx6 = relIds6[0] ? byId[relIds6[0]] : null;
      const sum6 = (base.summary || []).filter(Boolean);
      let saved6 = false; try { saved6 = !!(window.CXB && window.CXB.has('times', base.id)); } catch (e) {}
      Object.assign(cur, {
        rdHeroImg: this.imgObj(base, '55% 35%'),
        rdPill: base.lead ? 'Signal of the week' : (FMT6[base.format] || 'Article') + ' · ' + (base.tag || ''),
        rdMeta: [base.source, base.published, base.meta].filter(Boolean).join('  ·  '),
        // the dek can echo the title, so the column carries the first summary paragraph only
        rdExperience: sum6.length ? sum6[0] : (base.dek || ''),
        rdCta: ACT6[base.format] || 'Read the story',
        rdLines: [...new Set((base.lines || []).map(norm6))].map(n => ({ name: n,
          dot: { width: '6px', height: '6px', borderRadius: '50%', flexShrink: 0, background: LC6[n] || '#E8B96A' } })),
        rdHasNext: !!nx6,
        rdNext: nx6 ? { img: this.imgObj(nx6, '50% 45%'), n: num6[nx6.id], title: nx6.title, select: () => this.pick(nx6.id) } : { select: () => {} },
        rdRail: railIds6.map(id => byId[id]).map(r => ({ img: this.imgObj(r, '50% 40%'), fmt: FMT6[r.format] || 'Article',
          n: num6[r.id], source: r.sourceShort || r.source, title: r.title, select: () => this.pick(r.id) })),
        // Save keeps the platform's own save flow (cur.onSave); unsaved is a pale-gold outline,
        // saved is solid gold
        rdSave: Object.assign({ fontFamily: 'inherit', fontSize: '11px', letterSpacing: '.18em', textTransform: 'uppercase',
          borderRadius: '999px', padding: '11px 18px', cursor: 'pointer', whiteSpace: 'nowrap', transition: '.15s' },
          saved6 ? { color: '#0C1C27', background: '#D9B35C', border: '1px solid #D9B35C' }
                 : { color: '#F3DFA4', background: 'transparent', border: '1px solid rgba(243,223,164,.45)' }),
      });
    }
'''


def main():
    html = open(PAGE, encoding="utf-8").read()
    mm = re.search(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', html, re.S)
    man = json.loads(mm.group(2))
    key = next(k for k in man if k.startswith(ASSET))
    e = man[key]
    raw = base64.b64decode(e["data"])
    mod = (gzip.decompress(raw) if e["compressed"] else raw).decode("utf-8")
    if "data-atl-reader6a" in mod:
        sys.exit("6a reader already applied")
    a = mod.index("<!-- ============ READER · 5a Continuous Portrait ============ -->")
    b = mod.rindex("</sc-if>", a, mod.index("</x-dc>")) + len("</sc-if>\n")
    mod = mod[:a] + READER + mod[b:]
    assert mod.count("</style>\n</helmet>") == 1
    mod = mod.replace("</style>\n</helmet>", CSS, 1)
    assert mod.count(LOGIC_ANCHOR) == 1
    mod = mod.replace(LOGIC_ANCHOR, LOGIC + LOGIC_ANCHOR, 1)
    r = mod.encode("utf-8")
    e["data"] = base64.b64encode(gzip.compress(r, 9) if e["compressed"] else r).decode()
    html = html[:mm.start(2)] + json.dumps(man, separators=(",", ":")) + html[mm.end(2):]
    open(PAGE, "w", encoding="utf-8").write(html)
    print("applied 6a reader")


if __name__ == "__main__":
    main()
