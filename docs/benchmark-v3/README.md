# Handoff: Benchmark v3 uplift (Signature Experience Hub)

## Overview
This handoff brings the Benchmark tab (`Benchmark Gallery.dc.html`, a child component of the Hub entrypoint) up to the same standard as the Signature catalogue. The client approved four decisions:

- **1a cards:** full-bleed portrait cards, the same family as catalogue card 2a.
- **1c detail:** a dark quick-detail overlay with numbered chapters.
- **2a showreel:** a full-bleed cinematic reel with Up next thumbnails.
- **3c library:** an index on the left with three portrait cards beside it, merged with the old full collection into one **Library**. The Library has two modes, **Browse by** and **All benchmarks**.

**This is already implemented in the live Hub** (4 Nov 2026). Treat the live file as the reference. The pre-change file is kept at `build/Benchmark Gallery pre-v3.dc.html` for diffing and revert.

## Files
- `Benchmark v3 - Preview.html`: an offline preview built on a 24-benchmark sample.
- `source/Benchmark v3 Preview.dc.html`: the approved design source.
- `source/benchmark-v3.extract.html`: the exact template block and `_u3()` logic method taken from the live component.

All of these are design references in the Hub's DC dialect (`sc-for`, `sc-if`, `{{ }}` holes, inline styles). Recreate them in your production stack and keep the rules below.

## Fidelity
High fidelity, approved by the client. Fonts are Poppins and Fraunces (Fraunces for card and reel titles only).

**Palette:**
- Grounds: `#0A0A0A` (library and detail), `#161616` (chapter panels), `#1E1E1E` (tiles)
- Gold: `#E8B96A`
- Page: `#F4F1E9`
- Compare-on: sage `#9BB48C`

## Client decisions (do not undo)
- The **hero is unchanged**: the existing 400px frame with photo orbits and four stats.
- **No "Informs 1 SE" tag** on cards.
- **No Moment filter.** The client said it was never a filter before.
- **No discovery questions.** "Ask the library" and "Start from a question" were both tried and removed. The old Discovery lens is retired from the gallery.
- **The Full collection is no longer a separate chapter.** It is the **All benchmarks** mode of the Library.
- **Keep the old collection's filters and sorts:** Industry · Geography · Signature pillar · Theme · Business line (multi-select), **Not yet drawn on**, and **Brand A–Z / Newest first**.
- The detail's **Already informs** chapter shows each linked Signature Experience **with its photo as a thumbnail**.

## Page structure (gallery view)
Hero (unchanged) → `#bm-newly` **01 Showreel** → `#bm-explore` **02 The library**. The quick-detail overlay sits on top of both.

The ids are load-bearing: the hero's "N benchmarks added since your last visit" button scrolls to `#bm-newly`.

### 01 · Showreel (`[data-bm-reel]`)
- **Frame:** 640px tall, radius 20, black, `container-type:inline-size`.
- **Photo:** cover at `center 35%`, crossfading (`bgFade .6s`, keyed on id). Overlay: `180deg rgba(0,0,0,.5) 0 → 0 22% → 0 40% → .6 62% → .92 100%`.
- **Content:** the eight newest benchmarks by `added` (descending), topped up with `feat` records.
- **Top bar:** the label "01 · Newly added" (gold, 10.5px, `.22em`), a row of tick segments (3px; the current one gold, played ones at 50% gold), and an "NN / NN" counter.
- **Bottom-left block** (`width:min(620px, 100% − 520px)`, min 440px):
  - pills: "New" in gold and the industry on frosted black;
  - brand, 12px/600, uppercase;
  - title, Fraunces 48/52;
  - short, 15px at 85% opacity;
  - buttons: **Read the benchmark →** (gold), then **Compare** and **Save** (outline; Compare-on is sage, Saved is gold).
- **Bottom-right, Up next:** three 120×160 thumbnails, then ‹ › round buttons (44px).
  - **Below 1100px viewport** the thumbnails are hidden and the arrows move to `top:72px`, so the text never runs under them.
  - The resize listener only re-renders when that 1100px threshold is crossed.

### 02 · The library (`[data-bm-library]`)
- **Panel:** `#0A0A0A`, radius 20, padding 40.
- **Header:** kicker "02 · The library" and the title "The library" (34px/300). On the right, a mode switch: **Browse by** | **All benchmarks · N**. Segments: on = gold ground with `#0A1014` text; off = 75% white.

**Browse by (3c)**
- **Lens switch:** Brand A–Z · Theme (default) · Industry · Geography · Signature pillar · Business line.
- **Grid:** `minmax(200px,280px) | 1fr`.
- **Left: the index.**
  - Rows show value and count. The selected row is 17px/400 white with a 22px gold lead rule that animates its width. Other rows are 15px/300 at 60% white.
  - Max height 600, thin dark scrollbar, `padding-right:16px`.
  - **Hovering a row switches the cards after a 90ms debounce**, because the component is large. Clicking switches straight away.
- **Right:**
  - the selected value as a heading (22px/300), with an outline gold pill **See all N →** beside it;
  - three 1a cards, in a grid of `auto-fill, minmax(230px,1fr)`.
- **See all N →** switches to All benchmarks with that value pre-selected as a filter.

**All benchmarks**
- **Toolbar** (a rounded bar at 5% white):
  - ⌕ search over title, brand, industry, short and themes;
  - a count ("N of M");
  - a **Not yet drawn on · N** toggle (`informed.length === 0`);
  - **Brand A–Z / Newest first** (`bmRecency(added)`);
  - **Cards / List**.
- **Active filters** appear as gold pills with ×, plus **Clear all**.
- **Filter rail** (default; prop `allLayout: 'Filter rail' | 'No rail'`):
  - sticky, `minmax(190px,240px)` wide;
  - groups in this order: Industry · Geography (in `BM_REGIONS` order) · Signature pillar (in `BM_PILLARS` order) · Theme (top 10) · Business line;
  - each value shows a count, and all groups are multi-select;
  - with No rail, the same groups render as chip rows above the grid.
- **Cards:** 1a cards in `auto-fill, minmax(230px,1fr)`, with `content-visibility:auto; contain-intrinsic-size:auto 400px`, because 208 photo cards are in the DOM.
- **List:** rows of `36px num | 64px thumb | 1fr text | actions`. The text is brand (gold), industry, the "Added Mon YYYY" date and the title (17px/300, single-line ellipsis), followed by Compare/Save and →.
- **Empty state:** "Nothing matches that yet".

### 1a card (`[data-bm-card]`)
- **Shape:** 3:4, radius 10, black, with `translateY(-4px)` on hover.
- **Scrim:** `180deg .35 0 → 0 18% → 0 36% → .58 54% → .84 72% → .92 100%`.
- **Top-left:** an industry pill (frosted black, nowrap, ellipsis at 80%).
- **Foot** (padding `0 20px 18px`):
  - brand, 11px/600, uppercase;
  - title, Fraunces 24px / **29px** line-height, in a **fixed 58px box** (2-line clamp, bottom-aligned);
  - short, 12/18, in a **fixed 36px box** (2-line clamp);
  - a hairline rule, then **Compare** / **Save** buttons (live state) and "Open →" in gold.
- **Use pixel line-heights and fixed boxes** so every row aligns. This is the same rule as catalogue card 2a.
- Clicking the card opens the quick detail. The Compare/Save buttons stop propagation.

### 1c quick detail (`[data-bm-quick]`)
- **Overlay:** fixed, **z-index 110**, so the existing "Save to a board" popover (z-index 120) opens above it. Ground `rgba(21,38,50,.42)` with a 5px blur.
- **Card:** `min(940px,100%)`, `#0A0A0A`, radius 14.
- **Hero** (min height 520):
  - photo, faded to `#0A0A0A`;
  - top row: "Benchmark" (gold pill), the industry pill, and ✕;
  - "brand · moment" (moment from `bmStage()`, falling back to `bmPlace()`);
  - title, clamp(30–44px)/300;
  - short;
  - buttons: **Adapt in Idea Exchange →** (gold), then **Save** and **Compare**.
- **Chapters** (`#161616`, radius 14, a 170px left column with a gold 34px number):
  - **01 What they do:** `lead`.
  - **02 Why it works:** the `why[]` entries, each numbered with a head and a body.
  - **03 Where it could land at Aldar:** `transfer[]` tiles, each with a line dot.
  - **04 Already informs** (only if there are any): rows with a **64px experience photo** (from `_expMeta(eid).image`), a line dot, the name, the line and **Open ↗**. Open goes to `_openExpFull` and shows that experience in the catalogue.
- **Footer:** "Source · …".
- **Scope:** only the gallery opens the quick detail. Boards, Compare, Collections, the Transfer Viewer and external `__BM_OPEN` still open the existing full feature-story page through `_open(id)`.

## Wiring (live)
- **State keys** (namespaced): `u3Reel`, `u3Lens`, `u3Val`, `u3Mode`, `u3View`, `u3Q`, `u3Sort`, `u3Sel{lens: [values]}`, `u3Unused`, `u3Open`.
- **Data:**
  - Records: `DATA`, scoped by `S.line` when it is not "all".
  - Images: `window.BM_IMAGES[id]`, then `BMX_IMG[id]`, then the `G[art]` gradient. Images are gated on `imgsReady`.
- **Facets:**
  - Geography: `bmGeo(b).regionLabel`
  - Pillar: `bmPillar(b).short`
  - Line: `LINES[key].label`
- **Actions** reuse the existing handlers:
  - `_actCol(id)` supplies `onCmp`/`onSave` and their labels (Compare → "✓ Comparing", Save → "Saved").
  - The compare tray and the Save-to-board popover are unchanged.
- **Adapt in Idea Exchange** closes the overlay and calls `__SIG_GO('transfer')`.
  - **Gap:** Idea Exchange has no hook to receive a benchmark, so it opens on its default view.
  - A follow-up could add something like `window.__IX_BM = id` and have Signature Transfer read it.
- **Retired from the gallery view:** the old Chapter 01 procession and Chapter 02 Explore band, which held the Discovery, Brand, Theme, Industry, Geography and Pillar lenses plus the full collection ledger with its sticky preview.
  - Their view-model code still runs in `renderVals` and can be deleted in a clean-up pass.

## Verification checklist
- The hero is unchanged, and its "added since your last visit" button scrolls to the showreel.
- The reel cycles through 8 benchmarks; ticks, arrows and Up next all work; Up next hides below 1100px.
- In Browse by, hover or click on index rows swaps the three cards, and See all lands in All benchmarks with the filter pill set.
- In All benchmarks, search, rail filters, Not yet drawn on, both sorts and Cards/List all work together. The count matches what is shown.
- Compare and Save change state on cards, in the reel, in the list and in the detail. The board popover appears above the overlay.
- The detail's Already informs rows show photos and open the experience.
- After any change, **rebuild the export bases** per `CLAUDE.md`. Benchmark is not in the `cat` edition, so only `standalone-base.html` and `standalone-base-lines.html` change.
