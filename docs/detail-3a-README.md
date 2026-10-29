# Experience detail — "3a Continuous Portrait"

The detail view that opens when a catalogue card is clicked, redesigned to continue the 2a card: black throughout, the photograph fills the top of the dialog, and every section becomes a numbered chapter on charcoal.

**Visual change, plus one removal.** No data, routing or permission changes. The **Implementation progress / Progress log block (`modal.showLog`) is removed from the detail view** — do not render it (the note, the entries and the composer all go). Leave the underlying data and handlers in place; only the block is no longer shown. Every other section, field, conditional, button, input and handler stays exactly as it is, in the same order.

**Poppins only.** No Fraunces anywhere in the detail view — titles, numerals and narrative are all Poppins.

Reference build: `Experience Detail 3a Preview.html` (open in a browser). It uses the real Golden Coin record. It shows the hero, narrative, lifecycle, Scope, Deployment, Audit (locked state) and Assets. The other sections are specified below but not drawn in the preview.

Companion: the card spec in `card-2a-handoff/README.md`. This uses the same colours, scrim and pills.

## Where it applies
The single experience detail dialog (`showModal` / `modal.*` in the app), for every business line. Any line-specific blocks (Estates vertical cell, Education progress summary, RAG strip and so on) are restyled in place, not moved.

## Palette (dark ground)
| Token | Value | Use |
|---|---|---|
| Ground | `#0A0A0A` | dialog body |
| Ink | `#FFFFFF` | titles, values |
| Ink 2 | `rgba(255,255,255,.88)` | body copy, narrative, log text |
| Ink 3 | `rgba(255,255,255,.7)` | chapter labels, secondary text |
| Faint | `rgba(255,255,255,.55)` | field labels, out-of-scope line |
| Rule | `rgba(255,255,255,.14)` | chapter dividers |
| Rule soft | `rgba(255,255,255,.10)` | row dividers inside a chapter |
| Gold | `#E8B96A` | chapter numerals, primary button, note rule, links |
| Live | `#B5EBBE` | live / implemented / audited |
| In progress | `#F5CD85` | in implementation, in scope, pending |
| Review | `#EFE2C6` | in review |
| Parked | `rgba(255,255,255,.85)` | deprioritised / parked |

Map each line's own status vocabulary onto the four status colours, using the same rule as the card's `_fb()` dot.

**Do not rely on the light-theme colours that the view-model already computes.** `modal.life[].dot/txt/line`, `modal.deployGroups[].assets[].stateColor/nameColor`, `modal.ragBarStyle/ragBadgeStyle/…` and `col.btnStyle/cmpStyle` all hard-code light-ground values (`var(--ink)`, `#1E9E5A` and so on). Add dark variants in the view-model, not CSS overrides.

## Dialog shell
- Backdrop unchanged (`rgba(21,38,50,.42)` + blur 5px, scrolls).
- Panel: `width:min(940px,100%)`, `background:#0A0A0A`, `border-radius:14px`, `overflow:hidden`, `box-shadow:0 40px 90px rgba(0,0,0,.45)`, no border. Keep the existing `mzoom` entrance.

## 1 · Hero (`modal.hasImage`)
- Height `min(520px,62vh)`, `min-height:420px`. Photo is a style **object** (`backgroundImage:'url("…")'`, cover, `center 40%`). Never pass it as a CSS string, because the base64 URLs contain `;`.
- Scrim: `linear-gradient(180deg, rgba(0,0,0,.35) 0%, rgba(0,0,0,0) 22%, rgba(0,0,0,0) 40%, rgba(0,0,0,.6) 62%, rgba(0,0,0,.9) 82%, #0A0A0A 100%)`. It must end on the ground colour so the hero melts into the body.
- Remove the old 4px coloured left track bar.
- **Top row** (`top:22px; left/right:28px`, flex, space-between):
  - **Left group** (flex, gap 8, `flex-wrap:nowrap; flex-shrink:0` — with wrap on, the group collapsed and stacked the pills): the Defining pill, if defining (`#E8B96A` fill, `#0A1014` text, 10px / 600 / `.14em` uppercase, radius 999, padding `5px 11px`, "✦ Defining moment"), **then the line pill right beside it** (`rgba(0,0,0,.66)`, `1px solid rgba(255,255,255,.18)`, blur 6px, white 10px / 500 / `.1em` uppercase, radius 999, `5px 11px`, nowrap). If the record isn't defining, the line pill sits alone at the left.
  - **Right** (`margin-left:auto`): the close button only (34px circle, `1px solid rgba(255,255,255,.3)`, `rgba(0,0,0,.4)` + blur, white ✕, hover border gold).
- **Text block** (`left/right:40px; bottom:30px`, `text-shadow:0 1px 2px rgba(0,0,0,.6),0 0 18px rgba(0,0,0,.5)`):
  - Eyebrow row: existing `modal.eyebrow` + stage (7px dot in the status colour + white label), 11px / 600 / `.12em` uppercase.
  - Title `modal.name`: Poppins 300, `clamp(36px,4.6vw,48px)`, line-height 1.05, `letter-spacing:-.015em`, `max-width:16ch`, `text-wrap:pretty`.
  - Essence: 14px / 1.55, white, `max-width:60ch`. Use the record's essence here. The full narrative goes below the hero.
  - Actions (`margin-top:20px`, flex wrap, gap 8, `text-shadow:none`): the existing `col.onPrimary` (Save / Saved), `col.onCmp` (Compare) and `ix.onGo` (Adapt for another line) buttons. Primary is a gold fill (`#E8B96A`, `#0A1014` text); the others are outline (`1px solid rgba(255,255,255,.35)`, white, hover `rgba(255,255,255,.12)`). All 11px / 500, radius 999, padding `8px 16px`, **`white-space:nowrap`**. Keep the labels and selected states `col` already provides, recoloured for dark (selected Compare = `#7B916C` fill; Saved = gold fill).
- **No-image state** (`modal.noImage`): same hero box and layout, but the background is `linear-gradient(160deg,#2B3136 0%,#171E23 60%,#0E1418 100%)` plus `radial-gradient(60% 40% at 50% 34%,rgba(232,185,106,.14),transparent 70%)`, with a ◎ (30px, `rgba(232,185,106,.5)`) and "IMAGERY COMING SOON" (10px / `.16em` / `rgba(246,243,236,.5)`) centred at 34% height. Height `min-height:380px`. The title, eyebrow and actions move into the hero exactly as in the photo state, so the separate light no-image header block goes.

## 2 · RAG strip (`modal.showRag`) — not in preview
Directly under the hero, full width inside the body padding: `display:flex; gap:14px; align-items:center; padding:16px 0; border-bottom:1px solid rgba(255,255,255,.14)`, with a 3px RAG-coloured bar on the left (`border-radius:2px; align-self:stretch`). Badge letter is a 22px circle in the RAG colour with `#0A1014` text. Title white 14px / 600; reason `rgba(255,255,255,.72)` 12.5px; priority and action chips are outline pills (`1px solid rgba(255,255,255,.22)`, white 10.5px). "Also needed" chips use the same outline pill.

## 3 · Narrative
`modal.narrative` directly below the hero, before the first chapter: Poppins 300 (not italic), 18px / 1.6, `rgba(255,255,255,.9)`, `max-width:62ch`, `text-wrap:pretty`, `margin-top:14px`. No box.

## 4 · Lifecycle stage (`modal.life`)
A ruled strip, not a box: `display:grid; grid-template-columns:repeat(N,minmax(0,1fr)); border-top + border-bottom 1px rgba(255,255,255,.14); padding:18px 0; margin-top:28px`. Each step is an 8px dot + 12px label:
- current: dot `#F5CD85` (or the stage's status colour) with halo `0 0 0 4px rgba(245,205,133,.2)`, label in the same colour, weight 500;
- done: filled `rgba(255,255,255,.75)`, label `.75`;
- upcoming: hollow `1px solid rgba(255,255,255,.45)`, label `.5`.

Drop the old connector lines.

## 5 · Chapters
Every remaining block becomes a chapter with one shared shell:
```
display:grid; grid-template-columns:150px minmax(0,1fr); gap:28px;
padding:30px 0; border-bottom:1px solid rgba(255,255,255,.14)   (last chapter: no border, padding-bottom 0)
left:  numeral  Poppins 300 28px #E8B96A line-height 1, letter-spacing -.02em
       label    11px / 500 / .12em uppercase rgba(255,255,255,.7), margin-top 9px
right: the block's content
```
**Numbers are computed, not hard-coded.** Count only the chapters that actually render for this record, in display order, so the numbers never skip. Compute this in the view-model (for example `modal.chapters` or a `n` per block).

Chapter order is the current order, minus the removed Progress log: Scope & attributes → Deployment → Progress summary → Why it matters → Touchpoints → Audit intelligence → Assets → Implementation photos.

Below 720px panel width, the chapter grid collapses to one column, with the numeral and label in a row above the content.

### Scope & attributes
3-column grid (`repeat(3,minmax(0,1fr))`, gap `20px 24px`). Label 11px `rgba(255,255,255,.55)`; value 14px white, `margin-top:4px`. "—" / TBC values use `rgba(255,255,255,.5)`. Target go-live uses its status colour (gold-amber when committed). The Estates vertical cell, when present, is the first cell.

### Deployment (`modal.showDeploy`)
- Header line: on the left (a nowrap, `flex-shrink:0` group, gap 14), the **experience status as a tinted tag, not a dot** (see the rule below), then "Rollout **`modal.deployRollout`**" (12px `.7`, value white 500). On the right, `modal.deploySummary` in `.7` (12px).
- **One symbol, one meaning.** In the Deployment chapter, **dots mean assets only**. The experience-level status (`modal.deployStatusLabel`) is a square-cornered tag: 11px / 600 / `.06em` uppercase, text in the status colour, background = that colour at 12% alpha, `1px solid` the colour at 40%, `border-radius:4px`, padding `5px 10px`, nowrap. For example, In implementation is `#F5CD85` text on `rgba(245,205,133,.12)` with a `rgba(245,205,133,.4)` border. The tag is never a pill and never a dot, so the experience's status can't be mistaken for an asset row.
- Progress bar: 3px tall, track `rgba(255,255,255,.14)`, live segment `#B5EBBE`, square ends, margin `12px 0 20px`.
- Live-date row (`modal.hasLiveDate`): plain 12px `.7` text, values white; audit-gap chip = dot + label in its status colour.
- Asset groups: group label 10px / 500 / `.12em` uppercase `.5`. Rows: `padding:10px 0; border-bottom:1px solid rgba(255,255,255,.1)`, 8px dot + name (13px white) + state (11px in the state colour, right). Live = `#B5EBBE`, in scope/pending = `#F5CD85`.
- Out of scope (`modal.outScopeText`): 12px `.55`, line-height 1.6.
- No-deploy note: 13px `.7`.

### Progress log (`modal.showLog`) — removed
Not rendered in the detail view. No chapter, no number.

### Progress summary (`modal.hasProgress`) — not in preview
Chapter body is 13px / 1.65 `.88`; "Updated …" sits under the chapter label in 11px `.5`.

### Why it matters (`modal.hasBenefits`) — not in preview
Two columns (`1fr 1fr`, gap 28px), no cell fills. Sub-labels "For the customer" and "For Aldar" are 10px / 500 / `.12em` uppercase `.55`; text 13px / 1.6 `.88`. "Moment of truth · …" goes under the chapter label in 11px `.5`.

### Touchpoints (`modal.hasTP`) — not in preview
Two-column list, gap `10px 28px`, gold "—" marker, 13px `.88`.

### Audit intelligence
- Locked / pending copy: 13px / 1.6 `.7`, bold spans white.
- Scores (`modal.showScore`): eNPS and CSAT numerals in Poppins 300 44px `#E8B96A`, labels 10px uppercase `.55`, separated from the summary by `1px solid rgba(255,255,255,.14)`. Summary 13px `.88`; "View full audit report ↗" in gold.
- Record/Edit audit button: outline pill (white on dark). The edit form's inputs and textarea use a dark field: `background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.16); border-radius:10px; color:#FFF; font 13px; placeholder rgba(255,255,255,.4)`, focus border `#E8B96A`. Save audit is a gold pill (`#E8B96A`, `#0A1014`, 11.5px / 600, padding `10px 18px`).

### Assets (SharePoint library)
- Head line `modal.assetHead` 14px `.88`; "SharePoint" 11px `.5` on the right.
- Library block (`modal.hasAssets`): `background:rgba(255,255,255,.04); border-radius:10px; padding:20px`. Label 10px / 500 / `.14em` uppercase gold; folder name Poppins 300 24px white; preview line 12.5px `.7`. Thumbnails keep their shape, with `border-radius:6px` and `1px solid rgba(255,255,255,.1)`. The "+N more" tile is outline `rgba(255,255,255,.2)`, number in Poppins 300 white, hover border gold.

### Implementation photos (`modal.hasPhotos`)
Same 2-column grid, `border-radius:8px` on each tile, no other chrome.

## Fonts
Poppins only (300, 400, 500, 600). Remove every Fraunces `font-family` from the detail view.

## Done when
- Every record opens in the dark detail view, with and without a photograph.
- Every section that showed before still shows, in the same order, with the same content and working controls: Save/Compare/Adapt, close, audit record/edit/save, asset links. The Implementation progress block no longer appears for any line.
- Chapter numbers run 01, 02, 03… with no gaps for every line (check one Hospitality, one Development, one Estates and one Education record).
- No light-theme colour leaks onto the dark ground. Check the lifecycle, asset state colours and the RAG strip.
- Title and button labels never wrap mid-word at 1280px and at a 720px-wide window.
- No console errors.
