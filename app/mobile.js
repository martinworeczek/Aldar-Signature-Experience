/* Phone layer for the hub: adds the menu button and keeps app/mobile.css attached after the
   bundle swaps in its own document. Loaded from index.html (__sig_mobile hook). */
(function () {
  function ensure() {
    var h = document.head, b = document.body; if (!h || !b) return;
    if (!document.getElementById("sx-mobile-css")) { var l = document.createElement("link"); l.id = "sx-mobile-css"; l.rel = "stylesheet"; l.href = "/app/mobile.css?v=1"; h.appendChild(l); }
    if (!document.getElementById("sx-burger")) {
      var btn = document.createElement("button"); btn.id = "sx-burger"; btn.type = "button"; btn.setAttribute("aria-label", "Menu"); btn.innerHTML = "&#9776;";
      btn.onclick = function () { document.documentElement.classList.toggle("sx-nav-open"); btn.innerHTML = document.documentElement.classList.contains("sx-nav-open") ? "&#10005;" : "&#9776;"; };
      b.appendChild(btn);
    }
    // the backdrop sits next to the sidebar (same stacking layer), just beneath it
    var aside = document.querySelector("aside");
    if (aside && !(document.getElementById("sx-scrim") && document.getElementById("sx-scrim").nextSibling === aside)) {
      var old = document.getElementById("sx-scrim"); if (old) old.remove();
      var sc = document.createElement("div"); sc.id = "sx-scrim"; sc.onclick = close;
      aside.parentNode.insertBefore(sc, aside);
    }
  }
  function close() { document.documentElement.classList.remove("sx-nav-open"); var b = document.getElementById("sx-burger"); if (b) b.innerHTML = "&#9776;"; }
  // choosing a page in the menu closes it
  document.addEventListener("click", function (e) { var t = e.target; if (t && t.closest && t.closest("aside") && t.closest("aside div[title], aside a, aside nav > div")) setTimeout(close, 60); }, true);
  // phones: measure each layout block once (by its template id) and add a phone-only rule
  // for the ones that don't fit: oversized min-widths, wide side padding, rows of narrow columns
  var seen = {}, rules = [], sheet = null;
  function tune() {
    if (window.innerWidth > 700) return;
    var W = window.innerWidth, add = [];
    var els = document.querySelectorAll(".main-col [data-dc-tpl]");
    for (var i = 0; i < els.length; i++) {
      var e = els[i], id = e.getAttribute("data-dc-tpl"); if (seen[id]) continue;
      var r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
      seen[id] = 1;
      if (e.closest(".bv-track,.hero-marquee,.sn-shell,.main-col[style*='sticky'],[style*='overflow-x: auto'],[style*='overflow: auto']")) continue;
      var cs = getComputedStyle(e), sel = 'html .main-col [data-dc-tpl="' + id + '"]', d = [];
      var mw = parseFloat(cs.minWidth); if (mw > W * 0.6) d.push("min-width:0");
      var w = parseFloat((e.getAttribute("style") || "").replace(/.*?(?:^|;)\s*width:\s*(\d+)px.*/, "$1")); if (w > W) d.push("width:auto", "max-width:100%");
      var pl = parseFloat(cs.paddingLeft), pr = parseFloat(cs.paddingRight); if ((pl > 22 || pr > 22) && r.width > W * 0.7) d.push("padding-left:" + Math.min(pl, 16) + "px", "padding-right:" + Math.min(pr, 16) + "px");
      var kids = e.children;
      if ((cs.display === "flex" && cs.flexDirection === "row" && cs.flexWrap === "nowrap") || cs.display === "grid") {
        var narrow = 0, txt = 0;
        for (var k = 0; k < kids.length; k++) { var kr = kids[k].getBoundingClientRect(); if (kr.width > 0 && kr.width < 105 && kr.height > 48 && !/^(BUTTON|A)$/.test(kids[k].tagName)) narrow++; if ((kids[k].innerText || "").length > 12) txt++; }
        if (kids.length >= 3 && narrow >= 3 && txt >= 3) d.push(cs.display === "grid" ? "grid-template-columns:minmax(0,1fr)" : "flex-direction:column", "gap:10px");
      }
      if (d.length) add.push(sel + "{" + d.map(function (x) { return x + "!important"; }).join(";") + "}");
    }
    if (add.length) {
      rules = rules.concat(add);
      if (!sheet || !document.head.contains(sheet)) { sheet = document.createElement("style"); sheet.id = "sx-mobile-dyn"; document.head.appendChild(sheet); }
      sheet.textContent = "@media (max-width:700px){" + rules.join("") + "}";
    } else if (sheet && !document.head.contains(sheet) && rules.length) { document.head.appendChild(sheet); }
  }
  var t = null; new MutationObserver(function () { if (t) return; t = setTimeout(function () { t = null; ensure(); try { tune(); } catch (e) {} }, 250); }).observe(document, { childList: true, subtree: true });
})();
