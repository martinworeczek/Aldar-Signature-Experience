# Signature experience card — "2a Full-bleed Portrait"

Visual-only change. No data, routing, filtering, sorting or behaviour changes. Every existing field, click handler and button keeps working exactly as today.

Reference build: `Hospitality Page - Card 2a Preview.html` (open in a browser; Tweaks are fixed to the agreed defaults below).

## Where it applies
Every catalogue card grid view — the three card lists in the app:
1. All-experiences catalogue grid (`catCards`, grid mode only — **list mode is unchanged**)
2. Hospitality line page (`hpCards`)
3. Hospitality pillar view (`hpCatCards`)

Hospitality renders its own two lists, so all three templates must be changed; the shared one alone is not enough.

## Card shell
- `position:relative; aspect-ratio:3/4; border-radius:10px; overflow:hidden; background:#000; cursor:pointer`
- Shadow `0 16px 36px rgba(21,38,50,.16)`; hover `translateY(-4px)` + `0 28px 56px rgba(21,38,50,.26)`, transition `.2s`
- Grid: `repeat(auto-fill,minmax(270px,1fr))`, gap `18px`

## Layers (bottom → top)
1. **Photograph** — absolute, `inset:0`, `background-size:cover`, `background-position:center 35%`. Pass the image as a style **object** (`backgroundImage: 'url("…")'`), never as a CSS string: the base64 data URLs contain `;` and break a string style.
2. **No-image state** (when there is no photograph) — background `linear-gradient(160deg,#2B3136 0%,#171E23 60%,#0E1418 100%)` plus a soft gold glow `radial-gradient(60% 40% at 50% 38%,rgba(232,185,106,.14),transparent 70%)`, centred ◎ in `rgba(232,185,106,.5)` 30px and "IMAGERY COMING SOON" 10px / `.16em` / `rgba(246,243,236,.5)`.
3. **Scrim (pure black, not navy)** —
   `linear-gradient(180deg, rgba(0,0,0,.32) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 36%, rgba(0,0,0,.58) 54%, rgba(0,0,0,.84) 72%, rgba(0,0,0,.92) 100%)`
4. **Top row** — absolute `top:16px; left:16px; right:16px`, flex, space-between.
   - Left, only if defining: gold pill — `#E8B96A` fill, text `#0A1014`, 10px / 600 / `.14em` uppercase, radius 999, padding `4px 10px`, "✦ Defining". If not defining, an empty spacer so the right pill stays right.
   - Right: group / line pill — `rgba(0,0,0,.66)` fill, `1px solid rgba(255,255,255,.18)`, `backdrop-filter:blur(6px)`, white 10px / 500 / `.1em` uppercase, radius 999, padding `4px 10px`, nowrap + ellipsis, `max-width:60%`.
5. **Text block** — absolute `left:0; right:0; bottom:0; padding:0 20px 18px`, colour `#FFF`, `text-shadow: 0 1px 2px rgba(0,0,0,.6), 0 0 18px rgba(0,0,0,.5)`.
   - **Eyebrow row** — flex space-between; 11px / 600 / `.1em` uppercase, `#FFF`, with its own stronger shadow `0 1px 3px rgba(0,0,0,.85), 0 0 10px rgba(0,0,0,.6)`. Pillar left (ellipsis); stage right — label is **white**, the status colour lives only in a 7px dot (`box-shadow:0 0 0 2px rgba(0,0,0,.35)`).
   - **Title** — wrapper `height:57px; margin-top:10px; display:flex; align-items:flex-end`; inner Fraunces 26px / 400 / line-height 1.08, `#FFF`, clamp **2 lines**.
   - **Essence** — 12px / 400 / line-height 1.5, `#FFF`, **fixed `height:36px`**, clamp 2 lines, `margin-top:8px`.
   - **Footer** — `margin-top:16px; padding-top:14px; border-top:1px solid rgba(246,243,236,.18)`; left: existing Compare + Save buttons restyled as outline pills (transparent, `1px solid rgba(246,243,236,.3)`, white 11px / 500, radius 999, padding `6px 13px`, hover fill `rgba(246,243,236,.12)`); right: "Open →" 11px / 500 `#E8B96A`. Keep the selected states the app already applies to Compare/Save.

The fixed title and essence heights are what keep every card's text aligned across a row. Do not remove them.

## Stage dot colours (the label itself is always white)
| Stage | Colour |
|---|---|
| Live / Implemented | `#B5EBBE` |
| In implementation / In progress | `#F5CD85` |
| In review | `#EFE2C6` |
| Parked / Deprioritised | `rgba(255,255,255,.85)` |
Map each line's own status vocabulary onto these four.

## Fonts
Fraunces 400 must be loaded (`opsz,wght@9..144,300;9..144,400;9..144,500`).

## Done when
- All three grids show the new card; list mode untouched.
- Compare / Save / Open behave exactly as before, including on Hospitality.
- Every photographed experience shows its photo; the rest show the no-image plate.
- Text rows align across every grid row at 1440px and 1280px widths.
- No console errors.
