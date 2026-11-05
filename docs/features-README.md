# Showing and hiding hub sections

`features.json` (repository root) decides which sections of the hub are visible. Set a value to `true` to show
a section and `false` to hide it, then commit and redeploy. Nothing is deleted. Code, data and photos stay in place,
so switching a section back on brings it back exactly as it was.

| Switch | When `false`, this is hidden |
|---|---|
| `report_studio` | The Report Studio tab (Signature Experiences: Catalogue · Activity · ~~Report Studio~~), its view and `#report` links, Ask Echo's "Open in Report Studio" and report-PDF download, and report suggestions in Ask Echo |
| `rag_status` | The RAG strip on experience cards (On track / On watch / Needs a decision, priority and next action). In Ask Echo: the RAG instructions and counts, RAG reasons and dots in lists and timelines, the Health table column, the spotlight RAG pill, and "Which experiences are Red?" suggestions |
| `idea_exchange` | The Idea Exchange menu item and view, "See it in Idea Exchange" on experience cards, and Idea Exchange wording in AI disclaimers. In `/mcp` (Echo): the `get_idea_moves` tool, the `idea_move` filter, the search category and the `idea_moves` fields |
| `benchmark_editor` | The Benchmark Editor tab inside Benchmark. Library, Business Line Transfer Viewer and Boards stay |
| `ask_echo` | The hub's original in-page assistant (Claude). While `false`, the **Ask Echo** page shows Echo, the Copilot Studio agent, instead. `cx_martin_chat_url` is `/app/martin.html`, the hub's own branded chat: dark and gold, Aldar avatar, starter chips, tables styled like the hub. It connects over Direct Line with a short-lived token from `/api/martin-token`, which holds the Web channel security secret in the `CX_MARTIN_DIRECTLINE_SECRET` Netlify environment variable, never in the page. If that can't connect, the chat offers `cx_martin_microsoft_url` (Microsoft's own web chat). The original assistant's code stays in place; set `ask_echo` back to `true` to restore it. (The setting names still say `cx_martin`, the agent's former name.) |
| `project_plus` | Project Plus as a business line everywhere: menu and line page, catalogue chips and counts, catalogue hero, Portfolio Discovery (its headline becomes "six programmes"), Activity feed and search. In `/mcp`: its experiences, programme and counts (asking for it returns "not part of the hub right now"). In Submit & review: its lead and code |
| `board_sharing` | Board sharing. When `true` (now): **Export board** downloads a `.board.json` file, and a colleague uses **Import board** to add it to their own browser, credited to you, where it appears under *Shared with me*. When `false`: Export, Import and *Shared with me* are hidden. Either way, boards save automatically in each person's browser, and there is no whole-hub "Save board" download or "Download updated file" reminder (wording in `tools/board-sharing.json`) |
| `cx_academy` | The "In development · CX Academy" menu item and view, and the "CX Academy highlights" panel on Portfolio Discovery. Corporate experiences that mention CX Academy, such as *Aldar Performance Pins*, stay |

Hidden destinations also drop out of "Search everything" (⌘K). A bookmark or link to a hidden view opens
Portfolio Discovery instead. Ask Echo is told these sections aren't part of the hub, and never receives RAG data.

**How it works:** `tools/apply_features.py`, which runs on every Netlify build, does three things:
- writes `window.__SIG_OFF` into the page `<head>`;
- adds small guards to the hub's template wherever it builds those menus, tabs, buttons and answer cards;
- swaps a few fixed sentences that name a hidden section for neutral wording, and back again.

It is idempotent, and turning a section off, on and off again gives a byte-identical page. `/mcp` reads
`features.json` directly in `netlify/functions/_lib/mcp-core.mjs`.

## Always on: weekly Portfolio Discovery, and one AI read for comparisons

The same tool also installs three things that aren't switches:
- **Theme of the week.** The third rail on Portfolio Discovery rotates through `discovery-themes.json`, one theme per week, starting each Monday.
  - Each theme has a title, a blurb, colours and a `match` pattern, which is tested against each experience's name and essence.
  - A theme is only used when at least 4 photographed experiences match it.
  - Edit, add or reorder themes, then redeploy.
- **Defining moment of the week.** The showreel opens on it once the welcome screen closes, and the Defining moments rail leads with it.
  - Each week moves to the next business line, then to that line's next flagship.
- **One comparison read.** The compare view asks `/api/compare-read` for its AI read, and Echo's `compare_experiences` uses the same code and the same cache. The hub and Echo give the same read for the same set, until one of the experiences changes.

## Always on: Ask Echo, catalogue cards and implementation photos

- **Ask Echo** is one knowledge base across every visible business line, with no line tabs.
  - Every line gets Hospitality's capabilities: the factual-answer rules, supporting documents from the experience's own line, video, a filter taxonomy for each line's journeys, pillars, segments, asset types and properties, property questions, and breakdowns by journey stage, pillar, asset type and property.
  - The AI receives a slimmer copy of each experience: the full essence, a short narrative and the latest note, with empty fields dropped. That's about 60k tokens per question; follow-ups in the same conversation reuse the cached instructions.
  - Answer cards keep the full record.
- **Catalogue cards** no longer show the pillar, only the scope and stage. The pillar stays in the card detail.
- **Implementation photos** replace the SharePoint asset-library section in the card detail. Photos are grouped by asset (for example *W Hotel · 4 photos*) and open full size. They come from two places:
  - leads: an update in Submit & review has a *Photos from the live experience* section (choose the asset, add photos, optional caption), and photos appear once approved;
  - batches: `data/implementation-photos.json`, keyed by experience id, `{ asset, src, caption, when }`; files go in `img/impl/`.

  When an experience has none yet, the section says so and points to Submit & review. Echo returns them as `implementation_photos` on `get_experience`.
