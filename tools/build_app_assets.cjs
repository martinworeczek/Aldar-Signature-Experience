// Build the home-screen app icons and the link-preview images (WhatsApp, Teams, etc.).
//
// Inputs: app/aldar-logo.png (the white Aldar mark with its frame, from the hub's splash),
// the splash photos in img/, and the Poppins faces embedded in index.html.
// Outputs (committed): app/icon-*.png, app/apple-touch-icon.png, app/favicon-*.png,
// app/og-hub.jpg, app/og-submit.jpg.
//
// Run locally (needs Playwright's Chromium): node tools/build_app_assets.cjs
const fs = require("fs"), zlib = require("zlib"), path = require("path");
const { chromium } = require("playwright");

const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "app");
const BG = "#070c10", GOLD = "#c9a24a";
const logo = "data:image/png;base64," + fs.readFileSync(path.join(OUT, "aldar-logo.png")).toString("base64");
const SPLASH = ["1b22f900cc75705f", "ed4c77f231802f04", "4b0fb4e6dec95b00", "01b00a1cb85b9197", "a4fc52b3f93678aa", "1c4a8641d5289b90"]
  .map((h) => "data:image/webp;base64," + fs.readFileSync(path.join(ROOT, "img", h + ".webp")).toString("base64"));

// Poppins (latin, upright) exactly as the hub embeds it
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const manifest = JSON.parse(html.match(/<script type="__bundler\/manifest">\s*(\{[\s\S]*?\})\s*<\/script>/)[1]);
const ext = JSON.parse(html.match(/<script type="__bundler\/ext_resources">\s*([\s\S]*?)\s*<\/script>/)[1]);
const cssId = ext.find((r) => /family=Poppins/.test(r.id)).uuid;
let cssBuf = Buffer.from(manifest[cssId].data, "base64"); if (manifest[cssId].compressed) cssBuf = zlib.gunzipSync(cssBuf);
const fonts = cssBuf.toString().split(/(?=\/\* [a-z-]+ \*\/)/).filter((x) => /^\/\* latin \*\//.test(x) && /font-style: normal/.test(x)).join("\n");

const icon = (size, scale) => `<html><body style="margin:0;width:${size}px;height:${size}px;background:${BG};display:grid;place-items:center">
  <img src="${logo}" style="width:${Math.round(size * scale)}px;height:${Math.round(size * scale)}px"></body></html>`;

const og = (kicker, title1, title2, sub) => `<html><head><style>${fonts}
  *{box-sizing:border-box} body{margin:0;width:1200px;height:630px;background:${BG};font-family:Poppins,sans-serif;color:#fff;overflow:hidden;position:relative}
  .tiles{position:absolute;inset:0;display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(2,1fr);gap:18px;padding:18px;opacity:.38}
  .tiles div{border-radius:18px;background-size:cover;background-position:center}
  .shade{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 50%,rgba(7,12,16,.55) 0%,rgba(7,12,16,.9) 62%,rgba(7,12,16,.97) 100%)}
  .c{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
  .logo{width:150px;height:150px;margin-bottom:26px}
  .k{font-size:15px;font-weight:600;letter-spacing:.32em;text-transform:uppercase;color:${GOLD};margin-bottom:14px}
  h1{margin:0;font-size:64px;line-height:1.08;font-weight:300;letter-spacing:-.01em}
  h1 b{font-weight:600}
  p{margin:18px 0 0;font-size:22px;color:#c8d0d6;font-weight:300;max-width:860px}
  </style></head><body>
  <div class="tiles">${SPLASH.map((s) => `<div style="background-image:url(${s})"></div>`).join("")}</div><div class="shade"></div>
  <div class="c"><img class="logo" src="${logo}"><div class="k">${kicker}</div><h1>${title1} <b>${title2}</b></h1><p>${sub}</p></div></body></html>`;

(async () => {
  const b = await chromium.launch();
  const shot = async (doc, w, h, file, type = "png") => {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.setContent(doc, { waitUntil: "load" }); await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(OUT, file), type, ...(type === "jpeg" ? { quality: 86 } : {}) });
    await p.close(); console.log("wrote app/" + file);
  };
  // "any" icons: the framed mark fills most of the tile; maskable keeps it inside the 80% safe zone
  await shot(icon(192, 0.74), 192, 192, "icon-192.png");
  await shot(icon(512, 0.74), 512, 512, "icon-512.png");
  await shot(icon(512, 0.56), 512, 512, "icon-maskable-512.png");
  await shot(icon(180, 0.70), 180, 180, "apple-touch-icon.png");
  await shot(icon(48, 0.80), 48, 48, "favicon-48.png");
  await shot(icon(32, 0.84), 32, 32, "favicon-32.png");
  await shot(og("Aldar · Group CX", "Signature Experience", "Hub", "Every signature experience across Aldar's seven business lines, with global benchmarks, Aldar CX Time and the Idea Exchange."), 1200, 630, "og-hub.jpg", "jpeg");
  await shot(og("Aldar · Group CX", "Submit &amp;", "Review", "Business-line leads submit new signature experiences and updates. Group CX reviews each one before it goes live on the hub."), 1200, 630, "og-submit.jpg", "jpeg");
  await b.close();
})();
