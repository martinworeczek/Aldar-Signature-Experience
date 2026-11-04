# Handoff: Aldar CX Times — "Top Five" edition EDM (5a)

## Overview
This is a send-ready email that brings the **five most relevant stories** of a CX Times edition into the inbox and invites readers into the full edition in the Signature Experience Hub. It is adapted from the client's **"Welcome Home, Every Year"** Signature board template.

Each story is one board:
- a full-bleed photograph fading into forest green;
- a gold-dot pill;
- a thin white title;
- a gold-ruled two-column split, with **The story** beside **Why it matters for Aldar**.

The reference build uses **Edition 2 (3 September 2026)** with real Hub data. The template must render every future edition the same way.

## About the design file
`edm-e2-5a-top-five.html` is **production email HTML**. It uses nested `role="presentation"` tables and inline styles, with no JavaScript, plus Outlook conditionals and VML. Treat it as the exact target output.

The job is **to turn it into a data-driven template.** Use a Node build (template literal or Handlebars), React Email or MJML, or your email platform's own templating. Whichever you pick, the compiled HTML must keep the rules below. **Do not** rebuild it as web HTML: flex, grid, CSS-class layout and external stylesheets all break in Gmail and Outlook.

## Fidelity
**High-fidelity, approved by the client.** The colours, sizes, line-heights, padding and copy rules below are final.

## Client decisions (do not undo)
- **The name is "CX Times"** (with the s) in the masthead and the `<title>`. The live Hub still says "CX Times". Leave the Hub as it is unless the client asks.
- **Poppins throughout.** No serif.
- **No headline or intro under the masthead.** The masthead and date line lead straight into story 01.
- **The template's moment cards ("moment bubbles") are deliberately left out.** So are its top navigation bar, home button and "Next ›" pill.
- The template's "What makes it memorable" column is replaced by **"Why it matters for Aldar"**.
- **No unsubscribe link, preferences link or postal address.** This is an internal send. If your platform injects a compliance footer, check with the client first.
- **Photographs must never look framed or inset.** They run edge to edge, with no borders, padding or flat filler bands (see "Image pipeline").

## Email engineering rules
- The layout is one centred **600px** card (`class="w"`, `#122216`) inside a 100% outer table (`#0B0907`). The outer cell padding is `32px 0 48px`. Outlook gets a `<!--[if mso]>` 600px wrapper.
- Every style is inline. The `<style>` block holds only resets and the mobile media query.
- **Fonts:**
  - Poppins weights 200, 300, 400, 500 and 600 load via a `<link>` and an `@import`, both inside `<!--[if !mso]><!-->`.
  - Outlook on Windows is forced to Arial.
  - The stack everywhere is `'Poppins','Helvetica Neue',Helvetica,Arial,sans-serif`.
  - Gmail and Outlook Windows show the fallback. That is expected.
- `mso-line-height-rule:exactly` goes on all text. Every table and cell has explicit widths.
- Spacers are `<div style="height:N;line-height:N;font-size:0">&nbsp;</div>`. Never use margins.
- Use `color-scheme: dark` only.
- The hidden preheader comes first in `<body>`, followed by 70 repetitions of `&#847;&zwnj;&nbsp;`.
- Keep the email under Gmail's ~102 KB clip. It is currently 31 KB.
- The `xmlns:v`, `xmlns:o` and `xmlns:w` namespaces are on `<html>`, for the VML photo panels and the VML button.

### Mobile (`@media screen and (max-width:620px)`)
| class | effect |
|---|---|
| `.w` | card 100% |
| `.st` | stack the cell (`display:block;width:100%;box-sizing:border-box`) |
| `.px` | side padding becomes 24px |
| `.hs` | hide (the column gutter, and the desktop-only `<br>` in the CTA line) |
| `.bl0` | the "Why it matters" column drops its left rule and left padding and gains a 20px top padding when stacked |
| `.ph5` | photo panel height goes from 500px to auto |
| `.bsp` | photo-panel spacer goes from 0 to 150px (pushes the pill and title down over the photo) |
| `.h2` | story title drops from 40/44 to 30/35 |
| `.mast` | "CX Times" drops from 54/56 to 44/46 |

**Preview gotcha:** a 600px iframe triggers the mobile layout. Preview the desktop layout at 680px or wider.

## Layout, top to bottom

**Palette** (from the template):
- Grounds: outer `#0B0907` · card / forest green `#122216` (rgb 18,34,22)
- Gold: `#D9B35C` (dot, rules, "CX", links) · pale gold `#F3DFA4` (labels, the "why" text)
- Text: title `#FFFFFF` · body `#ECEDEA` (white at 92% over green) · muted `#99936B`
- Split rules: top `#565B41` (pale gold at 30% over green) · column `#616448` (pale gold at 35%)
- Pill: ground `rgba(18,14,10,.45)` (fallback `#1F2A1F`) · border `rgba(243,223,164,.6)` (fallback `#A39A72`)
- Button: gradient `90deg #F7E7BE → #D9B35C` (fallback `#E8CD8D`) · ink `#0C1C27`
- CTA panel: gradient `#1A2E1E → #0D1910` (fallback `#0F1D12`)

### 1 · Masthead (centred, padding `48px 40px 0`)
- "ALDAR": 13/17, white, letter-spacing 11px, uppercase, `padding-left:11px`. The padding balances the trailing tracking so the word centres optically.
- 10px gap.
- "**CX** Times": 54/56, weight 200, letter-spacing 1px, white. "CX" is `#D9B35C` at weight 400. Class `mast`.
- 14px gap.
- Ornament row: a 56×1 `#D9B35C` rule, then `pat-sadu-mini-clear.png` at 92×25 (10px padding each side), then another 56×1 rule.
- 26px gap.
- Date line: 10/14, `#ECEDEA`, letter-spacing 2.6px, uppercase. It reads **`Edition 2`** (in `#F3DFA4`) `  ·  3 September 2026`.
- 36px gap.

### 2 · Five story boards
Each board is two rows.

**Row A · photo panel**
- The outer `<td>` has zero padding. Inside it is a table with `bgcolor="#122216"`, `background="img/top5-0N.jpg"` and `style="background:#122216 url(…) center bottom / cover no-repeat"`.
- Outlook gets a `<v:rect>` 600×500 with `<v:fill type="frame">` and a `v:textbox` styled `mso-fit-shape-to-text:true`.
- The inner cell is `class="px ph5"`, `height="500"`, `valign="bottom"`, `style="height:500px;padding:0 40px;vertical-align:bottom"`.
- **The panel height must equal the photo's display height (500px).** If the panel is shorter, `cover` crops the top of the photo and removes the baked top fade, which leaves a hard seam between boards. This regression has already been fixed once.
- Contents, from the bottom up:
  - **Pill** (`border-radius:999px`, `padding:6px 14px 6px 12px`, 10/14, `#F3DFA4`, letter-spacing 2.4px, uppercase, nowrap):
    - It starts with a dot: `●` (`&#9679;`) at 9px in `#D9B35C` with `text-shadow:0 0 10px #D9B35C` (the template's glowing dot).
    - Label: `01 · Signal of the week` for the lead; `NN · {Article|Video|Podcast} · {sourceShort}` for the others.
  - 18px gap.
  - **Title**: 40/44, weight 200, letter-spacing −1px, white, linked to the edition (no underline). Class `h2`.
  - 26px gap.

**Row B · split** (`class="px"`, `bgcolor="#122216"`, padding `0 40px`)
- An inner table with `border-top:1px solid #565B41` and three cells:
  - **Left cell** (`st`), 196px wide, padding-top 22px:
    - label "THE STORY": 10/14, `#F3DFA4`, letter-spacing 2.8px;
    - 12px gap;
    - `dek` text: 14/22, weight 300, `#ECEDEA`.
  - **Gutter** (`hs`): 24px.
  - **Right cell** (`st bl0`): padding `22px 0 0 24px`, `border-left:1px solid #616448`:
    - label "WHY IT MATTERS FOR ALDAR";
    - 12px gap;
    - `why` text: 16/25, weight 300, `#F3DFA4`.
- 24px gap.
- Link: `{Read|Watch|Listen to} the story  →`, 11/15, weight 500, `#D9B35C`, letter-spacing 2.6px, uppercase, linked to the edition.
- Gap below the board: 44px between boards, 8px after the last one.

### 3 · Call-to-action panel
- **Wrapper cell:** padding `56px 24px 0`.
- **Panel table:** `bgcolor="#0F1D12"`, `linear-gradient(180deg,#1A2E1E,#0D1910)`, `border:1px solid #565B41`, `border-radius:4px`.
- **Inner cell:** padding `54px 44px 52px`, centred.

Content, in order:
- Kicker: "Edition 2 is live in the Hub", 10/14, `#F3DFA4`, letter-spacing 3px, uppercase.
- 18px gap.
- "Step inside<br>the edition.": 38/44, weight 200, letter-spacing −.5px, white.
- 18px gap.
- "{N} more stories, and a Signature Experience `<br class="hs">` to explore for each.": 15/24, weight 300, `#ECEDEA`. Here **N = the edition's story count − 5**.
- 34px gap.
- **Button,** label **READ THE EDITION →**:
  - **Outlook:** `<v:roundrect>` 340×60, `arcsize="50%"`, `fillcolor="#D9B35C"`, text Arial 14 bold, letter-spacing 3px, `#0C1C27`.
  - **Everything else:** a `<td>` with the gold gradient, `border-radius:999px` and `box-shadow:0 10px 30px rgba(217,179,92,.28)`. It wraps `<a style="display:block;padding:21px 46px">`, set 14/18, weight 600, letter-spacing 3px, uppercase, `#0C1C27`.

### 4 · Sign-off (centred, padding `48px 40px 40px`)
- `pat-sadu-mini-clear.png` at 104×28.
- 22px gap.
- "Curated by Aldar Group Customer Experience": 9/13, `#99936B`, letter-spacing 2.4px, uppercase.
- 16px gap.
- **Image credits** line: 9/14, `#99936B`. **Required.** Three of the photographs are CC BY-SA. Build it from the unique `imageCredit` values joined with " · ".

## Data mapping
Source: `window.AT_DATA.editions[0]`. Skill C writes it to `data/aldar-times.json`; the live app reads `data/aldar-times-rec.js`.

| email field | rule |
|---|---|
| The five stories | Items with the **highest `relevance`**, kept in edition order, with the lead (`lead:true`) always first. In Edition 2 these are the five records rated relevance 5: `e2-s1`, `e2-s2`, `e2-s4`, `e2-w1`, `e2-l1`. Allow an editor override. |
| Pill | lead → `01 · Signal of the week`; others → `NN · {FMT[format]} · {sourceShort}`, where FMT maps read→Article, watch→Video, listen→Podcast |
| Title | `title` |
| The story | `dek` |
| Why it matters for Aldar | `why`, **verbatim**. The Hub's text is curated, so never rewrite it in the template. |
| Link verb | read→Read · watch→Watch · listen→Listen to |
| Date line | `Edition {n} · {date}` |
| CTA count | `items.length − 5` |
| Credits | unique `imageCredit` values |
| Preheader | Editorial. Edition 2 uses *Oura's survey-free CX score, wellness inside everyday purchases, and three more stories for Aldar.* |
| Subject | Editorial. Suggested: *Aldar CX Times · Edition 2 — the top five* |
| All links | the edition's Hub URL. The current value is a placeholder: `https://hub.aldar.com/cx-time/edition-02` |

Data note: the Edition 2 lead's `why` still says "PM & Leasing", which is the old name for Estates. If the client wants it changed, fix it at the source in the Hub data, not in the email.

## Image pipeline
The source is `window.AT_IMG[imageKey || id]` (WebP base64, 700–900px wide). Each story produces `top5-0N.jpg` at **1200×1000** (shown at 600×500), JPEG q≈.76.

1. **Trim filler bands first.** Some source images are pillarboxed with flat colour bands. `e2-s2` (Paradisus Bali) had flat bands at x 0–170 and x 735–899. Detect columns whose luminance variance is ≈0 down the full height and crop them away before fitting; otherwise the board looks framed. For `e2-s2` the crop is sx = 176, sw = 552.
2. **Cover crop** to 1200×1000, with the horizontal anchor at 55% (50% for trimmed images) and the vertical anchor at 35%, as in the template's `object-position`.
3. **Bake two fades** in `rgba(18,34,22,α)`:
   - **Top:** α 1 at 0% → 0 at 16%. This blends each board into the one above it.
   - **Bottom:** α 0 until 32%, then .36 at 48%, .82 at 66%, .95 at 84%, and 1 at 100%. The pill and title sit on this part of the photo, and its foot matches the green split row exactly.

The originals are small, so the 2× output is upscaled and looks slightly soft on retina screens. Ask the pipeline for originals 1200px wide or larger.

## Before every send
1. Host `img/` publicly and rewrite every `img/` path (the `background` attributes, the CSS `url()` values and the VML `src`) to https.
2. Set the real edition URL.
3. Set the subject line and preheader.
4. Test in Gmail (web and app), Outlook 365 and Windows desktop, Apple Mail (iOS and macOS) and Samsung Mail.

## Files
- `edm-e2-5a-top-five.html`: the approved email.
- `img/`:
  - `top5-01.jpg` to `top5-05.jpg`: the five story boards, with fades baked in.
  - `pat-sadu-mini-clear.png`: the gold Sadu lozenge motif on a transparent ground, used in the masthead and the sign-off.
- In the project root (not in this folder): `CX Times EDM Options.dc.html` is the review canvas. 5a is under Turn 5, and the Tweaks panel has a 375px mobile toggle.

## How the pipeline builds it (`pipeline/cxtime/edm.py`, `newsletter.py`)
- **Links.** Each board's **Read / Watch / Listen to the story** link goes to the **source material** (the record's `sourceUrl`), as Group CX asked. Titles and the Read the edition button go to the CX Times edition, `https://aldar-cx-time.netlify.app`.
- **Fits the reading window.** The card fills the reading pane up to **800px** and shrinks to any narrower pane or phone. Board photos are cut at **1600×1000**, the shape of the widest panel (800×500). That way CSS `cover` only ever trims their sides and never the baked top fade, and boards join without a seam at every width. The split's left column is 36% wide. Outlook for Windows gets 800px ghost tables and 800×500 VML panels.
- **The five stories:** `newsletter.top_five()` takes the lead first, then the highest relevance in edition order. A `/pick` on the review PR takes precedence.
- **A story without a photograph** gets a green board sized to its pill and title.
- **Image pipeline:** as above. Flat pillarbox bands are trimmed, then the image is cover-cropped (anchor 55%/35%, or 50% if trimmed), and both green fades are baked in at JPEG q76.
- **Credits:** the unique `imageCredit` values of the boards that carry a photo.
- **Copy:** the preheader is the only written line; the review page shows it, and `/preheader` and `/subject` override it. The subject is `Aldar CX Times · Edition N — the top five`. "Why it matters for Aldar" is the record's `why`, verbatim.
- **Label change (Group CX, 3 Nov 2026):** the right-hand column's label reads **"Signature Experience opportunity"** instead of "Why it matters for Aldar". Its text is still the record's `why`, verbatim.
