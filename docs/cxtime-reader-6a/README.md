# Handoff: Aldar CX Time — article reader, "Welcome Home" template (6a)

## Overview
This is the new **article deep-dive** for Aldar CX Time in the Signature Experience Hub, restyled on the client's **"Welcome Home, Every Year"** Signature board template: forest green, pale gold, Poppins only, and a full-bleed photograph that fades up into green.

It **replaces the 5a reader** (`[data-atl-reader]` in `Aldar Times Live.dc.html`, documented in `exports/cxtime-4a5a-handoff/`). The library home is unchanged: the 4a/4b shelves and the Cards/List toggle stay as they are.

## About the design files
- `CX Time Reader - Welcome Home - Preview.html`: a self-contained preview that opens offline. It is built on real Edition 2 data. Use the Tweaks panel or the `story` prop to switch between the five top stories (`e2-s1`, `e2-s2`, `e2-s4`, `e2-w1`, `e2-l1`).
- `source/CX Time Reader - Welcome Home.dc.html`: the design source. It is a Design Component with inline styles and a small logic class.

These are **design references**, not production code. Recreate the reader in the Hub's own environment. For the live Hub, that means replacing the reader block inside `Aldar Times Live.dc.html` and keeping its existing state and handlers: `back`, `cur.dSave`, rail clicks → open story, and "All N stories →" → `back`.

## Fidelity
**High-fidelity, approved by the client.** The colours, type, spacing and copy below are final.

## Client decisions (do not undo)
- **Poppins throughout.** No serif.
- **No navigation bar.** The template's top pill nav (which held Library · Edition 2 · Edition 1) was removed. Only the round **back** button stays, top-left.
- **Section labels:** the left column is **"The experience"** and the right column is **"Signature Experience Opportunity"** (it was "Why it matters for Aldar").
- **"The experience" is one paragraph only**: the first paragraph of the AI summary, never the dek (the dek can echo the title).
- **Removed sections:** 01 In brief / key insights, the pull quote, and the Signature Experiences tiles are all gone. Below the hero there is **only "More in this edition"**.
- **Five cards in one row** across the page, **black** overlay, legible pills.

## Layout

**Palette:**
- Grounds: forest green `#122216` (rgb 18,34,22) · page `#0B0907`
- Gold: `#D9B35C` (dot, rules) · pale gold `#F3DFA4` (labels, opportunity text)
- Button: gradient `90deg #F7E7BE → #D9B35C` · ink `#0C1C27`
- Text: white; body at 92%

**Type:** Poppins 200 / 300 / 400 / 500. Labels are uppercase and widely tracked (letter-spacing `.2em`–`.28em`).

### 1 · Hero
- The hero is `min-height: min(820px, 92vh)`, a flex column with `justify-content: flex-end`, so the content sits at the foot and the hero grows with its text (it never clips).
- **Photo:** `position:absolute; inset:0`, `background-size:cover`, `background-position:55% 35%`. Without a photo, it falls back to `linear-gradient(135deg,#1F3A4D,#12222E)`.
- **Fades:**
  - Bottom, `0deg`: `rgba(18,34,22,.96)` at 0% · `.84` at 34% · `.34` at 58% · `0` at 78%.
  - Top, `180deg`: `rgba(18,14,10,.55)` at 0% → `0` at 22%. This keeps the back button legible.
- **Back button**, top-left (24, 18):
  - 52px circle, `rgba(18,14,10,.68)` with a 10px backdrop blur and a 1px `rgba(243,223,164,.5)` border.
  - The ← glyph is in `#F3DFA4`; hover changes the ground to `rgba(217,179,92,.25)`.
- **Next pill**, right 28px, top 36%. It shows only when the story has a related story:
  - 52px round photo of `related[0]`, then "NEXT · NN ›" (10px, `.28em`, pale gold) above the title (14px white, ellipsis at 300px).
  - Frosted ground `rgba(18,14,10,.5)`, border `rgba(243,223,164,.35)`.
- **Content block:** padding `96px clamp(24px,6vw,120px) clamp(36px,6vh,72px)`, gap 20px.
  - **Pill row:**
    - Pill: a 7px `#D9B35C` dot with `box-shadow:0 0 10px #D9B35C`, then the label. Label: `Signal of the week` for the lead, otherwise `{Article|Video|Podcast} · {tag}`. 10px, `.24em`, pale gold, border `rgba(243,223,164,.6)`, ground `rgba(18,14,10,.45)`.
    - Beside the pill: `source · published · meta`, 10px, `.24em`, pale gold at 75%.
  - **Title:** `clamp(34px,5vw,88px)`, weight 200, line-height .98, letter-spacing −.03em, `max-width:18ch`, `text-wrap:pretty`.
  - **Split:** a grid of `repeat(auto-fit,minmax(min(100%,340px),1fr))`, gap `36px clamp(24px,4vw,50px)`, `border-top:1px solid rgba(243,223,164,.3)`, padding-top 22px. It stacks on narrow screens.
    - **Left · THE EXPERIENCE:**
      - Label: 12px, `.28em`, pale gold.
      - Paragraph: `summary[0]` at `clamp(15px,1.2vw,19px)`, weight 300, line-height 1.55.
      - Buttons:
        - **Gold pill CTA**: `Read the article ↗` / `Watch the video ↗` / `Listen to the episode ↗`, linking to `sourceUrl` in a new tab. 11px, weight 500, `.18em`, padding 11×20.
        - **Save** outline pill, border `rgba(243,223,164,.45)`.
    - **Right · SIGNATURE EXPERIENCE OPPORTUNITY:**
      - `border-left:1px solid rgba(243,223,164,.35)`, padding-left `clamp(0px,3vw,40px)`.
      - Text: `why` at `clamp(17px,1.4vw,22px)`, weight 300, pale gold.
      - Under it, one small outline pill per business line, each with a coloured 6px dot (line colours below).

### 2 · More in this edition
- **Section:** padding `clamp(40px,6vh,72px) clamp(24px,6vw,120px)`.
- **Header row:** "MORE IN THIS EDITION" (12px, `.28em`, pale gold) on the left; an outline pill "All N stories →" on the right.
- **Grid:** `repeat(5, minmax(0,1fr))`, gap 18px. Exactly **5 cards**: the story's `related[]` first, then the rest of the edition in order, excluding the current story.
- **Card:**
  - 3:4, radius 14, `overflow:hidden`.
  - Photo cover at `50% 40%`.
  - Hover: `translateY(-6px)`, shadow `0 24px 50px rgba(0,0,0,.35)` plus an inset 1px `rgba(243,223,164,.35)` edge, easing `cubic-bezier(.2,.7,.2,1)` over .3s.
- **Overlay (black):** `180deg`, `rgba(0,0,0,.45)` at 0% · `0` at 24% · `0` at 38% · `.62` at 58% · `.9` at 100%.
- **Top pills** (inset 14px):
  - Format on the left (Article / Video / Podcast), story number on the right (`01`–`NN`).
  - Both: white 10–11px, weight 500, ground `rgba(0,0,0,.62)`, border `rgba(255,255,255,.22)`, 6px backdrop blur, radius 999.
- **Foot** (padding `0 18px 20px`, gap 10px):
  - A 22×1 `#D9B35C` rule.
  - Title: 18px / **23px line-height**, weight 400, white, in a **fixed 69px box** clamped to 3 lines. This keeps every card aligned; use pixel line-heights.
  - Source: 10px, weight 500, `.22em`, pale gold, nowrap with ellipsis.
- **Mobile:** the five-across row gets cramped below ~900px. Suggest `repeat(auto-fill,minmax(200px,1fr))` or a horizontal scroll row, and confirm with the client.

### Line colours (dots)
- Corporate `#4FB58C`
- Development `#C9A35A`
- Education `#8FB7C4`
- Estates `#D9786A`
- Hospitality `#E0AE82`
- Retail `#E0927C`
- All lines `#E8B96A`

Normalise legacy line names `PM…` / `Community…` to **Estates**.

## Data mapping (`window.AT_DATA.editions[0].items[]`)
| UI | field |
|---|---|
| Hero photo, card photos | `window.AT_IMG[imageKey || id]` |
| Pill | `lead ? 'Signal of the week' : FMT[format] + ' · ' + tag` |
| Meta line | `source` · `published` · `meta` |
| Title | `title` |
| The experience | `summary[0]` (fallback `dek`) |
| CTA label and link | `format` → verb; `sourceUrl` |
| Signature Experience Opportunity | `why`, verbatim |
| Line pills | `lines[]` (normalised, de-duplicated) |
| Next pill | first `related[]` id that exists in the edition |
| Card number | position in `items` (1-based, two digits) |
| All N stories | `items.length` |

Data note: the Edition 2 lead's `why` still says "PM & Leasing", which is the old name for Estates. Fix it in the Hub data if the client asks.

## Hub integration notes
- In the Hub, photos are attached by `SIG_IMAGES`/`AT_IMG`. The standalone DC shows gradient fallbacks until they load, so verify inside the app.
- Keep `data-atl-reader` on the reader root, and add `data-atl-card` to the five cards so existing probes still work.
- The old reader fields (`opps`, `railCards`, `excerptClean`, `keyInsights`) can stay computed. They are simply no longer rendered.
- After integrating, **rebuild all three export bases** (`standalone-base.html`, `standalone-base-lines.html`, `standalone-base-catalogue.html`) per `CLAUDE.md`.

## How it is applied in this repo
- `tools/apply_reader_6a.py` swaps the 5a reader block in the hub's CX Time module (manifest asset `59c00ad5` in `index.html`) for this design. It adds the values the design reads (`cur.rd*`) beside the existing ones. The existing handlers are kept: `back`, `cur.onSave` (the platform's own save flow), rail cards → open that story, and "All N stories →" → `back`. `data-atl-reader` stays on the root, and the five cards carry `data-atl-card`.
- `tools/build_cx_time.py` then rebuilds the standalone site (`sites/cx-time/`) from the hub, so both render the same reader. The "export bases" named above belong to the design project, not to this repo.
- **Phones and narrow panes** (the open question in "Mobile" above): the reader's layout follows **its own width, through a container query**, because in the hub the sidebar narrows it.
  - Up to 980px: the five cards become a swipeable row with scroll-snap.
  - Up to 880px: once the columns stack, the opportunity column takes a top rule, and the hero's green fade climbs higher, so the title stays legible over bright photos.
- **Group CX follow-up (4 Nov 2026):**
  - **The Next pill is removed.** The back button is the reader's only navigation.
  - **The space between the story and "More in this edition" is tightened.** The hero's foot padding (up to 72px) and the section's top padding (up to 72px) stacked to about 144px and left the two parts feeling disconnected. They are now 28px and 32px, about 60px together.
