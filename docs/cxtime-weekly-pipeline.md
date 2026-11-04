# Aldar CX Time: weekly edition pipeline

This replaces the old three-skill master prompt with a Python pipeline. It runs on its own
every **Monday at 07:07 Abu Dhabi time** (GitHub Actions) and stops at a **review gate**: a pull
request that shows the proposed edition. Nothing reaches the archive or either site until you
reply `/approve` on that pull request.

```
Monday 07:07 ─► Harvest ─► Screen ─► Deep read ─► Enrich ─► Fact-check ─► Curate ─► Pull request (review gate)
                                                                                       │
                       you reply: /drop  /add  /lead  /rerun  ◄────────────────────────┤
                                                                                       ▼
                                              /approve ─► Append edition ─► Hub + standalone + xlsx ─► Merge ─► Deploy both sites
                                                         └─► Benchmarks ─► Benchmark Repository (✦ From Aldar Times)
```

## What it selects: experiential CX, globally

Stories qualify only when they are about **how people actually experience a moment, place,
service or journey**, and how an organisation designed, staged, changed or measured it. The
people can be guests, shoppers, residents, students and parents, visitors, tenants or employees.
Each story needs a concrete, real example and an idea Aldar can transfer.

Coverage is **global**: there is no regional lane and no Gulf weighting.

AI and technology qualify only when they change what a person feels in the moment.

Out of scope:
- earnings, deals and M&A
- openings with no experiential detail
- executive moves
- vendor announcements
- contact-centre cost stories
- metrics with no lived experience
- advertising
- politics

## Feeding the Benchmark Repository

Some stories are more than news. They show **one named organisation doing one concrete thing
at one moment of its customer's journey**, which is exactly what a benchmark is. For each story,
Claude decides whether it qualifies and, if it does, drafts a benchmark in the repository's own
format:
- brand and industry;
- the Aldar line it informs (Hospitality, Retail, Education, Corporate, Estates or Development);
- the journey moment, mapped to that line's own stage, e.g. *Handover* for Estates;
- the Aldar CX pillar;
- themes from the repository's vocabulary;
- a short title in the repository's voice, a one-line summary and a two-sentence lead;
- three "why it works" points;
- how it would travel to other Aldar lines.

The benchmark draft goes through the same fact-check as the story. If any part of it fails,
the benchmark is withheld, but the story can still run.

Trend round-ups, surveys, opinion, vendor products and multi-brand pieces never become
benchmarks; the review page says why each story wasn't benchmarked.

The drafts appear in a **"Benchmark drafts"** section of the review. **Nothing is added to the
repository unless you ask:** reply `/bench <id>` for each draft you want. On `/approve` only those
are appended to the hub's repository:
- with the **✦ From Aldar Times** badge, showing the edition, date and source, and a link back;
- in the Newly added carousel;
- counted in the repository totals and searchable from the hub.

The story's photo is reused. `/nobench e3-s2` withdraws a `/bench` you gave earlier.

Benchmarks are append-only too. `data/benchmarks-from-times.json` records each one added, and
`check` confirms every one is still in the hub. This is also how the Development and Estates
lines, which have no benchmarks yet, start filling up from the news.

## The rules (all in `pipeline/config.toml`)

| Rule | Setting |
|---|---|
| Harvest window | last 7 days per source; a quiet source offers its newest 3 items, never older than 30 days |
| Shortlist for the full read | 18 articles, 6 videos, 6 podcasts (headroom above the caps), at most 4 per source |
| Caps | at most 6 articles, 3 videos, 3 podcasts; ceilings, not quotas |
| Quality bar | experiential ≥ 4 **and** relevance ≥ 3 (both 1-5), and a clean fact-check (up to two corrective rewrites) |
| Lead (Signal of the Week) | the strongest relevance-5 story; you can override it with `/lead` |
| Minimum edition | 5 stories. Below that the edition is marked **HOLD**: it is never padded, and you decide |
| Variety | at most 2 stories per masthead and 2 "AI & Tech" stories; lines spread so no line dominates |
| Never repeated | every URL ever screened is remembered in `data/cxtime-seen.json`; titles are matched against every past edition |
| Related stories | 3 per story, from the same edition only, with a nudge towards a different format |

## Steps and safeguards

1. **Harvest.** Only sources on the allow-list are fetched, from their own RSS feeds, podcast
   feeds or YouTube channel feeds. `robots.txt` is respected and requests are paced. A broken
   source is reported in the review and never stops the run.
2. **Screen.** Claude scores each story's metadata for experiential fit. Only the best go on
   to a full read, which keeps cost down.
3. **Deep read.** The full article, video description or episode notes are fetched.
   - Articles with fewer than 250 accessible words (paywalls, stubs) are dropped, because they
     can't be summarised faithfully.
   - Source text stays in memory only. It is never written to the repo.
4. **Enrich.** Claude writes the full record:
   - the title, standfirst, a three-sentence summary and "why it matters to Aldar" (naming a
     line and a moment);
   - the pull-quote (paraphrase, or a quote under 25 words with attribution);
   - one **Signature Experience per business line**, which fills the reader's chapter 03 one
     tile per line;
   - the tag, lines, insight type, themes and key insights.
5. **Fact-check.** A separate Claude pass compares every claim with the source. If it finds
   problems, the story is rewritten once and checked again. Anything still unsupported is
   flagged ⚠️ in the review and kept out of the automatic selection.
6. **Photo.** The source's own editorial image (og:image, episode artwork or the official video
   poster) is cropped to 16:9 and saved as WebP under 180 KB in `img/`. It is never hotlinked.
   Images narrower than 600 px fall back to the tag gradient.
7. **Curate.** Plain rules with no AI, so the same records always give the same edition.
8. **Review.** The pull request shows:
   - the lead and every shelf;
   - for each story: title, source, format, lines, scores, summary, "why it matters", the
     ideas, the photo and any flags;
   - line coverage, and which lines got nothing this week;
   - the bench (good stories that weren't selected);
   - everything dropped, with reasons;
   - the health of every source.

   If a Netlify token is set, it also links a live preview of the proposed page.
9. **Publish (after `/approve`).**
   - The edition is **prepended** to `data/aldar-times.json`.
   - Every earlier edition is checked against its fingerprint in `data/aldar-times.lock.json`.
     If any past edition differs by a single byte, publishing stops.
   - The edition is written into the hub page, the standalone site is rebuilt and
     `data/aldar-times.xlsx` is regenerated across the whole archive.
   - Every source link is checked: a dead link (404) blocks publishing, and bot refusals are
     listed for you to check by hand.
   - Benchmark drafts you selected with `/bench` are appended to the hub's Benchmark Repository.
   - The pull request is merged and both sites are deployed.

## Review commands

Reply on the edition's pull request, one command per line:

| Command | Effect |
|---|---|
| `/approve` | Publish, merge, deploy both sites |
| `/approve anyway` | Publish an edition marked HOLD |
| `/drop e3-s4` | Take a story out (it goes to the bench) |
| `/add k:ab12cd34` | Bring a bench story in (keys are in the bench table) |
| `/lead e3-w1` | Make it the Signal of the Week |
| `/rerun e3-l2 lean on the arrival ritual` | Re-read and rewrite one story, with your note |
| `/bench e3-s2` | Add this story's benchmark draft to the repository on publish (nothing is added without it) |
| `/nobench e3-s2` | Withdraw a `/bench` given earlier |

Only the repository owner and collaborators can run commands. A published edition is
permanent: correct it in a later edition, never by editing the archive.

**Retiring editions** is the one exception, and only when Group CX asks for it.
`python3 -I tools/retire_cxtime_editions.py <n> …` moves editions, unchanged, into
`data/aldar-times-retired.json` (with their lock records and photo refs; nothing in `img/` is
deleted). It then rewrites the live archive, the lock, the hub and the xlsx without them. Their
stories still count as published, so the weekly run never offers them again. Afterwards, rebuild the
standalone site and redeploy both sites. Editions 1 and 2 were retired on 4 November 2026;
CX Time now starts at Edition 3, and the next edition is 4.

If an edition is still open the next Monday, that run is skipped and the pull request gets a
reminder. Close the pull request to discard an edition.

## The announcement email

Every edition gets a designed announcement email (design "5a Top Five", spec in `docs/edm/README.md`). It carries the edition's **five most relevant stories**, the lead first. Each is a full-bleed photo board with *The story* and *Signature Experience opportunity* (the edition's own "why it matters" text, verbatim). Each board's **Read / Watch / Listen to the story** link goes to the source. A **Read the edition** panel leads into CX Time. The email is fluid, so it fits any reading pane or phone.

- **Words.** The subject is `Aldar CX Times · Edition N — the top five`, and a one-line preheader is written with the proposal. Both are shown on the review page under *Announcement email*; change them with `/subject` or `/preheader` followed by your text. Choose which stories follow the lead with `/pick e3-s4 e3-s5 …` (up to four); the rest fill by relevance. The email is approved together with the edition.
- **Build.** On publish, the board photographs are cut to JPEG with their fades baked in (Outlook desktop does not show WebP), and the
  email is written to `sites/cx-time/email/edition-N/`. It goes live at
  `https://aldar-cx-time.netlify.app/email/edition-N/` with the site deploy.
- **Send.** Save that `index.html` as `<subject>.html` into OneDrive **CX Times/Outbox**. A Power
  Automate flow (*When a file is created* → *Send an email (V2)*, with the file content as the body)
  sends it with the design in the email body. The file must be a new upload: copies don't trigger the
  flow. The pipeline's own mail connector strips images and styling, so it can't send the email itself.

## One-time setup

1. **Secrets** (GitHub → Settings → Secrets and variables → Actions):
   - `ANTHROPIC_API_KEY`: required.
   - `NETLIFY_AUTH_TOKEN`: a Netlify personal access token, for previews and deploys.
     Without it, the edition still publishes to the repo, and you deploy both sites by hand.
2. **Let Actions open pull requests:** GitHub → Settings → Actions → General → Workflow
   permissions → tick *Allow GitHub Actions to create and approve pull requests*.
3. **First run:** Actions → *CX Time · weekly edition* → *Run workflow*. That run shows whether
   every source in the allow-list is reachable; fix or swap any that report a failure.

## Running it by hand

```bash
pip install -r pipeline/requirements.txt
python3 pipeline/run.py check                 # archive locked and in step with the hub
python3 pipeline/run.py propose               # needs ANTHROPIC_API_KEY and open internet
python3 pipeline/run.py revise comment.txt    # same commands as on the pull request
python3 pipeline/run.py preview /tmp/preview  # standalone page with the proposed edition
python3 pipeline/run.py publish               # append + rebuild; then deploy both sites
python3 pipeline/tests/e2e_offline.py         # full offline test with fake feeds and a mock editor
```

## Sources (global allow-list)

| Kind | Sources |
|---|---|
| Experience design | Blooloop, TrendWatching, PSFK, Event Marketer, Hospitality Design, Dezeen (interiors) |
| CX practice | CX Network, CX Dive, CMSWire (customer experience) |
| Hospitality | Skift, Hospitality Net |
| Retail | Retail TouchPoints, Retail Dive |
| Places and communities | Urban Land (ULI), Project for Public Spaces |
| Education and workplace | EdSurge, Work Design Magazine |
| Podcasts | Good Morning Hospitality, Skift Podcast, CX Decoded, Experience This!, Remarkable Retail, Amazing Business Radio, The CX Leader Podcast, EdSurge Podcast |
| Video | Skift, Blooloop, TrendWatching, Shep Hyken, CX Today |

Removed from the old skills:
- **CX4CA and AGBI:** regional sources, and coverage is now global.
- **OpenAI News and MIT Technology Review:** they flood the edition with AI stories that have
  no experiential angle.
- **Times Higher Education:** paywalled.
- **Propmodo:** proptech, with little lived experience.
- **Retail Customer Experience:** replaced by Retail TouchPoints.
- **Gallup Workplace:** engagement data rather than experiences.
