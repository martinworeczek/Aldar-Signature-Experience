"""Hook the hub page (index.html) up to hub submissions (/sx/).

1. In <head>: load /sx/sx-apply.js, start fetching /api/sx/published, and wrap the seven
   line data globals (CP_DATA ... PP_DATA) so approved records are applied the moment each
   data set loads.
2. In the bundle loader: wait (at most 2.5 s) for that fetch before the page renders, so the
   first render already includes them. If the fetch fails the hub renders as before.
3. A "Submit & review" item in the sidebar, under Overview, linking to /sx/.

Idempotent: re-running replaces the previous hook. Usage: python3 tools/apply_sx_hook.py
"""
import re

PATH = "index.html"
HOOK = r"""<script id="__sig_sx" src="/sx/sx-apply.js"></script>
<script id="__sig_sx_boot">(function(){
  var MAP={CP_DATA:'cp',HP_DATA:'hp',RP_DATA:'rp',EDU_DATA:'edu',DEV_DATA:'dev',EST_DATA:'est',PP_DATA:'pp'};
  var recs=null;
  if(/^https?:$/.test(location.protocol)){
    window.__SX_READY=Promise.race([
      fetch('/api/sx/published',{credentials:'omit'}).then(function(r){return r.ok?r.json():null}).then(function(j){recs=j&&Array.isArray(j.records)?j.records:null}).catch(function(){}),
      new Promise(function(r){setTimeout(r,2500)})
    ]);
  }
  Object.keys(MAP).forEach(function(g){
    var v=window[g];
    try{Object.defineProperty(window,g,{configurable:true,enumerable:true,
      get:function(){return v},
      set:function(x){v=x;try{if(recs&&recs.length&&window.SX_APPLY)window.SX_APPLY.apply(MAP[g],x,recs,window)}catch(e){console.warn('[sx]',e)}}
    })}catch(e){}
  });
  // sidebar entry: its own block between the menu and the profile footer, outside the
  // runtime-rendered menu list (inserting into that list makes the runtime clone it)
  function addNav(){
    if(document.getElementById('__sx_nav'))return;
    var nav=document.querySelector('aside nav');if(!nav||!nav.parentNode)return;
    var w=document.createElement('div');w.id='__sx_nav';w.style.cssText='padding:4px 12px 10px';
    w.innerHTML='<a href="/sx/" title="Submit & review" style="display:flex;align-items:center;gap:11px;padding:10px 12px 10px 15px;border-radius:10px;font-size:12.5px;color:#ebd9ae;text-decoration:none;border:1px solid rgba(201,162,74,.35);background:rgba(201,162,74,.08);font-weight:500"><span style="width:18px;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px;color:#c9a24a">&#xFF0B;</span><span class="nav-label" style="flex:1 1 0%;min-width:0">Submit &amp; review</span></a>';
    nav.parentNode.insertBefore(w,nav.nextSibling);
  }
  var t=null;new MutationObserver(function(){if(t)return;t=setTimeout(function(){t=null;addNav()},120)}).observe(document,{childList:true,subtree:true});
})();</script>
"""
AWAIT = "    try { if (window.__SX_READY) await window.__SX_READY; } catch (e) {} /* __sx_wait: approved hub submissions */\n"
ANCHOR = "    const doc = new DOMParser().parseFromString(template, 'text/html');"

html = open(PATH, encoding="utf-8").read()
html = re.sub(r'<script id="__sig_sx" src="/sx/sx-apply\.js"></script>\n<script id="__sig_sx_boot">[\s\S]*?</script>\n', "", html)
html = html.replace(AWAIT, "")
edition = re.search(r'<script id="__sig_edition">.*?</script>\n?', html)
assert edition, "edition hook not found"
html = html[: edition.end()] + HOOK + html[edition.end():]
assert html.count(ANCHOR) == 1, "loader anchor not found exactly once"
html = html.replace(ANCHOR, AWAIT + ANCHOR)
open(PATH, "w", encoding="utf-8").write(html)
print("sx hook applied")
