"""Build the standalone Aldar CX Times site (sites/cx-time/) from the hub's index.html.

The page is the hub's own "Aldar Times Live" module, opened on its own with an Aldar CX
Time brand bar, plus only what it needs: the page runtime, the edition data (AT_DATA),
its photo list (AT_IMG) and photo loader, the shared collection store (Save), the Aldar
logo and Poppins. It reuses the hub's bundle shell (unpacker, lazy photo loader), so both
render identically. Re-run after any CX Times change in the hub, then redeploy both sites.
Usage: python3 -I tools/build_cx_time.py
"""
import base64, gzip, json, os, re, shutil

HUB = "index.html"
OUT = "sites/cx-time"
HUB_URL = "https://aldar-signature-experience.netlify.app/"

# manifest assets the page needs, by id prefix
NEED = {
    "runtime": "8023f0d9", "cxb": "d20392ec", "at_data": "9b89dde2",
    "at_img": "87c04e48", "img_loader": "02d0bfd2", "module": "59c00ad5", "logo": "1271cd60",
}

BRAND = """<div class="cxt-bar">
  <a class="cxt-brand" href="./" title="Aldar CX Times">
    <img src="{logo}" alt="Aldar">
    <span><b>Aldar CX Times</b><i>Curated by Group CX</i></span>
  </a>
  <a class="cxt-hub" href="{hub}" target="_blank" rel="noopener"><span class="cxt-long">Signature Experience </span>Hub ↗</a>
</div>
<div class="cxt-page">
"""

BRAND_CSS = """
body{margin:0;background:#F3EFE7;font-family:'Poppins',sans-serif;-webkit-font-smoothing:antialiased}
.cxt-bar{position:sticky;top:0;z-index:60;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:12px 28px;background:#0A1014;border-bottom:1px solid rgba(232,185,106,.22)}
.cxt-brand{display:flex;align-items:center;gap:14px;text-decoration:none;min-width:0}
.cxt-brand img{width:40px;height:40px;object-fit:contain;flex-shrink:0}
.cxt-brand span{display:flex;flex-direction:column;line-height:1.2;min-width:0}
.cxt-brand b{font-size:16px;font-weight:600;color:#F6F3EC;letter-spacing:-.005em;white-space:nowrap}
.cxt-brand i{font-style:normal;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:#E8B96A;margin-top:3px;white-space:nowrap}
.cxt-hub{font-size:11px;font-weight:500;color:#F6F3EC;text-decoration:none;border:1px solid rgba(255,255,255,.28);border-radius:999px;padding:8px 14px;white-space:nowrap}
.cxt-hub:hover{border-color:#E8B96A;color:#E8B96A}
.cxt-page{max-width:1440px;margin:0 auto;overflow-x:clip}
html,body{overflow-x:clip}
@media (max-width:640px){.cxt-bar{padding:10px 16px}.cxt-brand i{display:none}.cxt-hub{padding:7px 11px}}
@media (max-width:400px){.cxt-long{display:none}.cxt-brand img{width:34px;height:34px}}
""" + """
/* Phones and small tablets. The module is laid out with inline styles for the desktop hub,
   so these rules reach it through the data-m hooks that MOBILE_HOOKS adds at build time. */
@media (max-width:700px){
 .atl{border-radius:0!important;min-height:0!important}
 [data-m=pad]{padding:12px 12px 40px!important}
 [data-atl-masthead]{border-radius:16px!important;margin-bottom:18px!important}
 [data-m=mh]{padding:58px 18px 20px!important;min-height:0!important}
 [data-m=mh] [data-atl-edpill] > div > div[style*="absolute"]{right:auto!important;left:50%!important;transform:translateX(-50%);width:min(280px,calc(100vw - 48px))!important}
 [data-m=stats]{gap:10px 22px!important}
 [data-m=strip]{flex-direction:column!important;margin-top:18px!important}
 [data-m=strip] > div{border-right:0!important;border-bottom:1px solid rgba(247,242,233,.12);padding:11px 16px 12px!important}
 [data-m=strip] > div:last-child{border-bottom:0}
 [data-m=shelf]{padding:16px 12px 22px!important;border-radius:16px!important}
 [data-atl-lead]{aspect-ratio:auto!important;min-height:440px!important;display:flex;flex-direction:column;justify-content:flex-end;margin-top:4px!important}
 [data-m=leadchips]{left:14px!important;right:14px!important;top:14px!important;flex-wrap:wrap!important}
 [data-m=leadtx]{position:relative!important;left:auto!important;right:auto!important;bottom:auto!important;padding:84px 18px 20px}
 [data-m=leadtx] > div:last-child{flex-wrap:wrap}
 [data-m=grid]{grid-template-columns:minmax(0,1fr)!important;gap:12px!important}
 [data-m=grid] [data-atl-card]{aspect-ratio:4/5!important}
 [data-atl-row]{grid-template-columns:92px minmax(0,1fr)!important;gap:14px!important;padding:14px 0!important}
 [data-atl-row] > span:last-child{display:none!important}
 [data-atl-row] > div:nth-child(2) > div:nth-child(2){font-size:16px!important}
}
"""

# Elements the phone CSS needs to reach, tagged by a unique prefix of their opening tag.
# Each hook must match exactly the expected number of times, so a redesign of the module
# fails the build loudly instead of silently losing the mobile layout.
MOBILE_HOOKS = [
    ('<div style="position:relative;z-index:1;max-width:none;margin:0;padding:26px 28px 80px', "pad", 1),
    ('<div style="position:relative;min-height:400px;display:flex;flex-direction:column', "mh", 1),
    ('<div style="display:flex;justify-content:center;gap:28px;flex-wrap:wrap;margin-top:18px', "stats", 1),
    ('<div style="display:flex;width:100%;max-width:760px', "strip", 1),
    ('<div style="background:radial-gradient(1100px 480px', "shelf", 1),
    ('<div style="position:absolute;top:18px;left:18px;display:flex;gap:8px;flex-wrap:nowrap', "leadchips", 1),
    ('<div style="position:absolute;left:28px;right:28px;bottom:26px', "leadtx", 1),
    ('<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px', "grid", 1),
]


def add_mobile_hooks(mod):
    for needle, name, count in MOBILE_HOOKS:
        found = mod.count(needle)
        assert found == count, "mobile hook %r: expected %d, found %d" % (name, count, found)
        mod = mod.replace(needle, '<div data-m="%s" ' % name + needle[len("<div "):])
    return mod


def main():
    html = open(HUB, encoding="utf-8").read()
    mm = re.search(r'(<script type="__bundler/manifest">\s*)(\{.*?\})(\s*</script>)', html, re.S)
    man = json.loads(mm.group(2))
    ids = {k: next(u for u in man if u.startswith(p)) for k, p in NEED.items()}
    e = man[ids["module"]]; raw = base64.b64decode(e["data"])
    mod = (gzip.decompress(raw) if e["compressed"] else raw).decode("utf-8")

    # head: map the module's dev-time paths to bundled assets and add what the hub provided
    mod = mod.replace('<script src="./support.js"></script>',
                      '<title>Aldar CX Times</title>\n<script src="%s"></script>' % ids["runtime"], 1)
    mod = mod.replace('<script src="data/aldar-times-rec.js"></script>',
                      '\n'.join('<script src="%s"></script>' % ids[k] for k in ("cxb", "at_data", "at_img", "img_loader")), 1)
    assert ids["runtime"] in mod and ids["at_data"] in mod
    mod = mod.replace("<style>\n.atl a{", "<style>" + BRAND_CSS + "\n.atl a{", 1)
    mod = add_mobile_hooks(mod)
    # brand bar and page wrapper around the module's own root
    head_end = mod.index("</helmet>") + len("</helmet>")
    body_end = mod.index("</x-dc>")
    mod = (mod[:head_end] + "\n" + BRAND.format(logo=ids["logo"], hub=HUB_URL)
           + mod[head_end:body_end] + "</div>\n" + mod[body_end:])

    # the bundled template form of camelCase event attributes (what the bundler emits)
    mod = re.sub(r'\bon([A-Z][a-z]+)="', lambda m: 'sc-camel-on-' + m.group(1).lower() + '="', mod)
    hub_ext = json.loads(re.search(r'<script type="__bundler/ext_resources">\s*(\[.*?\])\s*</script>', html, re.S).group(1))
    ext = [x for x in hub_ext if "/react" in x["id"]]  # the runtime loads React through these
    keep = {ids[k] for k in NEED if k != "module"} | {x["uuid"] for x in ext}
    sub = {u: man[u] for u in keep}

    out = html
    out = out[:mm.start(2)] + json.dumps(sub, separators=(",", ":")) + out[mm.end(2):]
    out = re.sub(r'(<script type="__bundler/ext_resources">\s*)\[.*?\](\s*</script>)',
                 lambda m: m.group(1) + json.dumps(ext) + m.group(2), out, count=1, flags=re.S)
    tm = re.search(r'(<script type="__bundler/template">\s*)(".*?")(\s*</script>)', out, re.S)
    out = out[:tm.start(2)] + json.dumps(mod).replace("</", "<\\u002F") + out[tm.end(2):]
    # hub-only pieces: saved hub state, the AI endpoint hook, the card title fitter
    out = re.sub(r'<script type="application/json" id="__sig_state">.*?</script>', '', out, flags=re.S)
    out = re.sub(r'<script id="__sig_ai_netlify">.*?</script>\n?', '', out, flags=re.S)
    out = re.sub(r'<script id="__sig_c2_fit">.*?</script>\n?', '', out, flags=re.S)
    out = out.replace("<title>Bundled Page</title>", "<title>Aldar CX Times</title>", 1)

    if os.path.isdir(OUT + "/img"):
        shutil.rmtree(OUT + "/img")
    os.makedirs(OUT + "/img", exist_ok=True)
    refs = set()
    for k in ("at_img", "at_data"):
        a = man[ids[k]]; r = base64.b64decode(a["data"])
        refs |= set(re.findall(r'/img/[0-9a-f]{16}\.(?:webp|jpg|png|gif)', (gzip.decompress(r) if a["compressed"] else r).decode("utf-8")))
    refs |= set(re.findall(r'/img/[0-9a-f]{16}\.(?:webp|jpg|png|gif)', mod))
    for ref in refs:
        shutil.copy(ref[1:], OUT + ref)
    open(OUT + "/index.html", "w", encoding="utf-8").write(out)
    open(OUT + "/netlify.toml", "w").write('[build]\n  publish = "."\n\n[[headers]]\n  for = "/img/*"\n  [headers.values]\n    Cache-Control = "public, max-age=31536000, immutable"\n')
    print("built %s: page %.1f MB, %d photos" % (OUT, len(out) / 1e6, len(refs)))

if __name__ == "__main__":
    main()
