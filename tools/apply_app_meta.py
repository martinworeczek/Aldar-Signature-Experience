"""Home-screen app + link previews for the hub (index.html) and Submit & review (sx/index.html).

- Title, description, Open Graph / Twitter tags (what WhatsApp, Teams, LinkedIn, iMessage read),
  placed at the very top of <head> so link crawlers find them in the first bytes of a large page.
- Web app manifest, icons and theme colour, so "Add to Home Screen" / "Install app" uses the
  Aldar logo and opens full-screen.
- The hub's bundle replaces the whole document when it renders, which drops these tags from the
  live page; a small script puts the manifest, icons, theme colour and title back afterwards.

Idempotent. Usage: python3 tools/apply_app_meta.py   (also run by the Netlify build)
"""
import html as H
import re

SITE = "https://aldar-signature-experience.netlify.app"


def tags(title, desc, url, image, alt):
    t, d = H.escape(title, quote=True), H.escape(desc, quote=True)
    return f"""<!-- __sig_app:start -->
<meta charset="utf-8">
<title>{H.escape(title)}</title>
<meta name="description" content="{d}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Aldar Signature Experience Hub">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}{image}">
<meta property="og:image:secure_url" content="{SITE}{image}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{H.escape(alt, quote=True)}">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{SITE}{image}">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#070c10">
<link rel="icon" type="image/png" sizes="32x32" href="/app/favicon-32.png">
<link rel="icon" type="image/png" sizes="48x48" href="/app/favicon-48.png">
<link rel="apple-touch-icon" sizes="180x180" href="/app/apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Aldar SX Hub">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<link rel="canonical" href="{url}">
<!-- __sig_app:end -->
"""


# re-adds the app tags after the hub's bundle swaps in its own <head>
RESTORE = """<script id="__sig_app_restore">(function(){
  var T=document.title||'Aldar Signature Experience Hub';
  var L=[['link',{rel:'manifest',href:'/manifest.webmanifest'}],['meta',{name:'theme-color',content:'#070c10'}],
    ['link',{rel:'icon',type:'image/png',sizes:'32x32',href:'/app/favicon-32.png'}],['link',{rel:'apple-touch-icon',sizes:'180x180',href:'/app/apple-touch-icon.png'}],
    ['meta',{name:'apple-mobile-web-app-capable',content:'yes'}],['meta',{name:'mobile-web-app-capable',content:'yes'}],
    ['meta',{name:'apple-mobile-web-app-title',content:'Aldar SX Hub'}],['meta',{name:'apple-mobile-web-app-status-bar-style',content:'black'}]];
  function fix(){var h=document.head;if(!h)return;
    if(!document.title)document.title=T;
    L.forEach(function(x){var a=x[1],k=a.rel?'link[rel="'+a.rel+'"]':'meta[name="'+a.name+'"]';if(!h.querySelector(k)){var e=document.createElement(x[0]);for(var n in a)e.setAttribute(n,a[n]);h.appendChild(e);}});}
  var t=null;new MutationObserver(function(){if(t)return;t=setTimeout(function(){t=null;fix()},150)}).observe(document,{childList:true,subtree:true});
})();</script>
"""


# phone layer: burger menu + full-width layout below 700px (app/mobile.js adds app/mobile.css)
MOBILE = '<script id="__sig_mobile" src="/app/mobile.js"></script>\n'


def apply(path, block, restore=False, drop_title=None):
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<!-- __sig_app:start -->[\s\S]*?<!-- __sig_app:end -->\n", "", s)
    s = re.sub(r'<script id="__sig_app_restore">[\s\S]*?</script>\n', "", s)
    if drop_title:
        s = s.replace(drop_title, "")
    else:  # page's own <title> is replaced by ours
        s = re.sub(r"<title>[^<]*</title>\n?", "", s, count=1)
    m = re.search(r"<head[^>]*>\n?", s)
    assert m, "no <head> in " + path
    s = re.sub(r'<script id="__sig_mobile"[^>]*></script>\n', "", s)
    s = s[: m.end()] + block + (RESTORE + MOBILE if restore else "") + s[m.end():]
    open(path, "w", encoding="utf-8").write(s)
    print("app meta applied:", path)


apply("index.html",
      tags("Aldar Signature Experience Hub",
           "Every signature experience across Aldar's seven business lines, with global benchmarks, Aldar CX Times and the Idea Exchange. Curated by Group CX.",
           SITE + "/", "/app/og-hub.jpg", "Aldar Signature Experience Hub"),
      restore=True, drop_title="  <title>Bundled Page</title>\n")
apply("sx/index.html",
      tags("Submit & review · Aldar Signature Experience Hub",
           "Business-line leads submit new signature experiences and updates. Group CX reviews each one before it goes live on the hub.",
           SITE + "/sx/", "/app/og-submit.jpg", "Submit and review signature experiences"))
