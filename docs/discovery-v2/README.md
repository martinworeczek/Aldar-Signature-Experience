# Handoff: Portfolio Discovery v2 — Signature Experience Hub

## Overview
Portfolio Discovery is the Hub's landing tab. It has been rebuilt to match the Benchmark v3 and catalogue 2a card family: dark chapter panels, gold numbered chapters, Poppins + Fraunces, photo-led cards. Five chapters:

- **Hero** (unchanged frame; three-cell stat bar)
- **01 Showreel** — cinematic reel of the defining moments
- **02 Curated stories** — three collections as tabs, five cards each
- **03 Benchmark repository** — six highlight cards
- **04 Aldar CX Time** — latest edition: Signal of the Week + three stories
- **05 The journey** — the Hub's existing stage-column pattern, restyled dark

The **wall / Full collection mosaic** and the **CX Academy placeholder** are removed.

## Files
- `source/discovery-v2.extract.html` — the exact template and logic lifted from the live Hub (`Corporate Plus Experience Repository.dc.html`). This is the reference implementation; it is already live.
- `source/Portfolio Discovery Uplift.dc.html` — the exploration canvas. **3a** at the top is the approved design; Turns 2 and 1 below are rejected alternatives, kept for context only.
- Pre-change copy of the Hub: `build/Corporate Plus Experience Repository pre-discovery-v2.dc.html` (project root, not in this folder).

## Fidelity
**High-fidelity, approved by the client (5 Nov 2026).**

## Client decisions (do not undo)
- **No wall / mosaic.** The showreel, shelf cards, Benchmark and CX Time already carry the imagery.
- **Curated stories are tabs, not stacked shelves** — one row of five cards for the active tab. The third tab is **"Theme of the week"** (currently arrival & welcome; the theme rotates).
- **Shelf cards show the short description (essence), not the pillar.**
- **"See all N →" opens the existing collection overlay** (`disc.collection`, Cards/List + line chips) — the same thing the old rails' "View all" did.
- **The journey keeps the Hub's own pattern** (stage columns → chip/toggle row → tile grid), not a new card design. The repeated stage headline ("In implementation · In delivery · 38 experiences") is removed; the columns already say it. No inner box: the grid sits directly on the panel.
- **No black panels.** Chapter tones: 02 slate `#1A2230` · 03 graphite `#161A1E` · 04 umber `#1C1814` · 05 aubergine `#1A151D`. Hero and showreel stay on the Hub's navy/black.
- **Hero stat bar has three cells maximum** (Experiences · Defining · Live). The Watch / Browse / Follow row is gone.

## Layout

### Hero (`#sec-showreel`, 400px)
Unchanged frame (navy radial, drifting dots, gold vignette). Content is bottom-aligned, centred: gold dot + "ALDAR · PORTFOLIO DISCOVERY" kicker, title `disc.heroTitle`, sub "A guided showreel first, then curated ways into the whole collection.", then the 620px stat bar (`rgba(10,16,20,.6)`, border `rgba(232,185,106,.34)`, radius 12, 7px blur) with three centred cells: EXPERIENCES "{N} across the group" · DEFINING "{N} signature rituals" · LIVE "{N} in the world today".

### 01 Showreel (`#sec-reel`, 640px, radius 20, black)
- Photo `disc.d2.reelBg` (Ken Burns `dkb 8s`) under a vertical scrim `.5 → 0 (22%) → 0 (40%) → .6 (62%) → .92`.
- Top row (40px in, 32px down): "01 · SHOWREEL" eyebrow · tick bar (one `flex:1` 3px tick per item: gold current, 50% gold passed, 25% white ahead) · 30px play/pause · "NN / NN".
- Bottom-left block, width `min(620px, calc(100% − 520px))`: Defining pill (gold) + line pill (black 66%, line dot) · pillar eyebrow · Fraunces 48/1.06 title · essence 15/1.5 at 85% · gold **Open the experience →**, outline **Save** / **Compare** (both wired to the real collection picker and compare tray).
- Bottom-right: "UP NEXT" + three 120×160 portrait thumbnails (next three items, click = jump) + ‹ › 44px round buttons. **Below 1100px wide the thumbnails and label hide; the arrows move to top 72px.**

### 02 Curated stories (`#sec-stories`)
- Header: eyebrow "02 · CURATED STORIES" + title "Three ways into the portfolio"; right, a pill switcher (`rgba(255,255,255,.06)`, radius 999, 4px padding) with three tabs: **Defining moments · Recently launched · Theme of the week**, each showing its count at 55%. Active tab is gold with navy text.
- Row under: the tab's blurb (14/300, 70% white, max 60ch) left; "See all N →" outline gold pill right → opens the collection overlay.
- Grid `repeat(auto-fill, minmax(210px,1fr))`, gap 14, **five cards**. Card = 2a: 3:4, radius 10, black scrim, Defining pill top-left (when defining), line pill top-right (black 60%, line dot), Fraunces 21/25 title in a fixed 50px box (2-line clamp), essence 12/17 in a 34px box, hairline, then Compare/Save outline pills + "Open →". Click opens the experience peek (`_dOpen`).

### 03 Benchmark repository (`#sec-bench`, hidden in the `cat` edition)
- Header: eyebrow, title "Best-in-class, from outside Aldar", sub from `BM_INDEX` ("208 benchmarks · 91 brands · 21 industries · latest additions August 2026"); right, "Open the repository →" → `disc.openBench`.
- Grid `minmax(230px,1fr)`, gap 16, **six** cards from `BM_INDEX.highlights`, photo from `BM_IMG_STORY[id]`: industry pill top-left, gold brand eyebrow, Fraunces 24/29 title (58px box), short line (36px box), footer with line dot + line and "Open →". Click opens that benchmark (`window.__BM_OPEN = id; go('benchmark-hub')`).

### 04 Aldar CX Time (`#sec-times`, hidden in the `cat` edition)
- Header: eyebrow, title "Edition {n} · {date}", sub "{N} curated stories on customer experience, each with a Signature Experience opportunity"; right, "Read the edition →" → `disc.openTimes`.
- Two columns `repeat(auto-fit, minmax(min(100%,340px),1fr))`: left, the **lead** as a 380px-min photo card (Signal of the week gold pill + tag pill, Fraunces 32 title, dek, gold source · meta line); right, **three rows** (96px square thumb, "ARTICLE · Source" eyebrow, 15px title 2-line clamp, muted tag · meta). All click through to CX Time.

### 05 The journey (`#sec-journey`)
- Header: eyebrow "05 · THE JOURNEY" (reads "03" when Benchmark/CX Time are hidden), title "The portfolio, moving through maturity", sub.
- **Stage columns** (flex, gap 6): count 38/300 · label 13/600 · sub 10.5 · 3px underline. Active stage in its colour (In review `#7E9BCE` · In implementation `#E18454` · Deployed & live `#7B916C` · Audited `#2D2459`); others at 35–50% white with a 10% underline.
- **Row** (padding 16 0, bottom hairline): line chips left (All lines gold + one per line present, 6px dot, active = gold border + 15% gold fill) · Cards / List toggle right (active gold).
- **Grid** (`max-height:452px; overflow:auto`): cards = the existing `_dTile` 118px photo tiles with ✦ mark, line dot and name; list = `_dRow` rows (46px thumb, name, pillar, line, ›). Same data as before.

## Data & wiring
- One new method, **`_disc2(disc, locals)`**, called at the end of the existing Portfolio Discovery block in `renderVals()`; it returns `disc.d2`. It reuses the locals the v1 model already computes (`dall`, `dreel`, `didx`, `dcur`, `DCOLL`, `DSTAGES`, `ddrillAll`, `ddLine`, `ddView`, `BX`, `openBench`, `dOpenColl`) — nothing is re-fetched.
- New state key: `dTab` (`'defining' | 'live' | 'welcome'`).
- Compare/Save on cards replicate `_actFor` (compare tray max 4; Save opens the collection picker, Unsave opens it in manage mode).
- `DCOLL.welcome.title` is now "Theme of the week" (also the overlay title). The "welcome" items are still selected by the regex `/welcom|arriv|first|onboard|greet|check-in|check in/`; **when the theme rotates, change both the regex and the blurb in `TABS`.**
- v1 fields still computed but unused: `disc.rails`, `disc.mosaic*`, `disc.journey`, `disc.journeySurface`, `disc.timesPreview`, `disc.bench.*` (the old 3-card form), `disc.placeholderTiles`, `disc.cap*`, `disc.reel.strip`. Safe to delete later.
- Section anchors (`_secAnchors`) now list sec-stories · sec-bench · sec-times · sec-journey.
- Export bases rebuilt for this change: `standalone-base.html`, `standalone-base-lines.html` (28.8 MB) and `standalone-base-catalogue.html` (18.1 MB).

## Open items
1. Theme-of-the-week rotation is manual (regex + blurb). A small `data/discovery-theme.js` with `{label, blurb, match}` would let the CX team rotate it without touching the app.
2. In the `cat` edition the journey is numbered 03 (chapters 03/04 hidden). Confirm that is acceptable or hide the numeral.
3. Below ~900px the five-card shelf row wraps to 2–3 columns; the client has not reviewed mobile.
