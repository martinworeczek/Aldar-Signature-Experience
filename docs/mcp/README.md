# Aldar Signature Experience Hub — MCP server

A read-only [Model Context Protocol](https://modelcontextprotocol.io) server over every data set the hub renders, so external agents (Microsoft Copilot Studio, Claude, any MCP client) can query it live.

- **Endpoint:** `https://aldar-signature-experience.netlify.app/mcp`
- **Transport:** Streamable HTTP (stateless; JSON responses; no SSE stream). Protocol versions 2025-06-18, 2025-03-26 and 2024-11-05.
- **Auth:** none. The server is open and public (read-only, CORS enabled), so any MCP client can connect with just the URL.
- **Freshness:** Netlify runs `node tools/build_mcp_data.mjs` on every deploy. It loads the data sets embedded in `index.html` exactly as the browser does and writes the dataset the function serves. So the MCP answers always match the deployed site; there is no second copy to maintain.
- **Rate limit:** 120 requests per minute per client.

## Data categorisation

| # | Category | What it holds | Size today |
|---|---|---|---|
| 1 | **Signature experiences** | Every experience in the 7 business lines, normalised to one schema: id, line, name, flagship flag, lifecycle stage (the hub's own rules), pillar, journey stage, target go-live, essence, narrative, latest note, dated history, segment / type / cadence, touchpoints, benefits, audit scores, photo URL | 267 (Corporate 31, Hospitality 58, Retail 40, Education 22, Development 54, Estates 44, Project Plus 18) |
| 2 | **Programmes** | Per line: programme name, source and last update, vision, pillars, journeys / phases, properties / malls / schools, segments, tiers, tracks, research findings | 7 |
| 3 | **Deployment** | Per experience: assets in scope, which are live, and which are out of scope. Covers hotels and beach clubs, malls, schools, communities and HQ | inside each experience |
| 4 | **Benchmarks** | Global CX reference cases: brand, industry, pillar, themes, lead, why it works, how it transfers to each Aldar line, source, and the Aldar experiences it informed | 208 |
| 5 | **Aldar CX Time** | Editions and stories (articles, videos, podcasts): AI summary, why it matters to Aldar, relevant lines, suggested signature experience, speakers, links | 2 editions, 16 stories |
| 6 | **Idea Exchange** | *Hidden while `idea_exchange` is false in `features.json`.* Transferable experience moves, what each becomes in every line, and the experiences that embody it | 26 moves |
| 7 | **Asset library** | SharePoint folder per experience (folder, link, photo / film / document counts, file names) | 22 folders, attached to experiences |

Not included, because they live only in each visitor's browser: saved boards, audits recorded in the browser, and Ask Echo chats.

## Tools

| Tool | Answers questions like |
|---|---|
| `get_overview` | "What can you tell me about?" Categories, counts, data stamps, which tool answers what. Agents should call this first. |
| `search` | "Anything about pet welcomes?" Ranked matches across experiences, benchmarks and CX Time. |
| `list_experiences` | "Which Hospitality experiences are live?", "What's live at W Hotel?", "What's due Nov–Dec 2026?", "Flagships in Retail". Filters: line, stage, defining, pillar, journey stage, property, live at, target window, text. Sorting and paging included. |
| `get_experience` | "Tell me everything about The Golden Coin." The full record, with linked benchmarks. Accepts an id or a name. |
| `portfolio_breakdown` | "How many experiences per stage in Retail?", "Live experiences by property". Group by line, stage, pillar, journey stage, property, live property, target month or defining, with the same filters as `list_experiences`. |
| `get_programme` | "What are Estates' journeys and verticals?" |
| `list_benchmarks` / `get_benchmark` | "Shopping mall benchmarks on loyalty", "Why does JPMorgan 270 Park work?" |
| `list_cx_time` / `get_cx_time_story` | "Podcasts in the latest edition", "Summarise the Oura TCX story". |
| `list_customer_stories` / `get_customer_story` | "Customer stories from our schools", "Has Behind the Build worked for a real customer?". Stories from `data/customer-stories.js` (hidden ones left out), each with the experience it expresses and whether that link is confirmed or proposed. `get_experience` also returns an experience's `customer_stories`. |
| `compare_experiences` | "Compare The W Paws arrival with The note nobody asked for." The hub's AI read of 2 to 4 experiences: verdict, shared and different points by lens (need, mechanism, moment), takeaway. Same read, same cache as the hub's compare view (`/api/compare-read`, `netlify/functions/_lib/compare-read.mjs`). |
| `get_idea_moves` | *Hidden while `idea_exchange` is false.* "What does 'a named greeting ritual' become in Retail, and who already does it?" |

Every tool is read-only (`readOnlyHint`) and returns both text JSON and `structuredContent`.

## Connecting Microsoft Copilot Studio

1. Open your agent in Copilot Studio → **Tools** → **Add a tool** → **New tool** → **Model Context Protocol**.
2. Fill in the form:
   - **Server name:** Aldar Signature Experience Hub
   - **Server description:** Read-only access to Aldar's signature experiences, programmes, deployment, benchmarks and CX Time.
   - **Server URL:** `https://aldar-signature-experience.netlify.app/mcp`
3. **Authentication:** choose **None**.
4. Click **Create**. Copilot Studio lists the 13 tools; leave them all enabled.
5. In the agent's instructions, add: "For anything about Aldar signature experiences, CX programmes, benchmarks or CX Time, use the Aldar Signature Experience Hub tools. Call get_overview first if unsure. Quote stages, dates and counts exactly as returned."

If your Copilot Studio tenant offers only the custom-connector route, create a custom connector from an OpenAPI definition with host `aldar-signature-experience.netlify.app`, base path `/`, a POST operation `/mcp` marked `x-ms-agentic-protocol: mcp-streamable-1.0`, and no authentication.

## Maintaining it

- **New data in the hub:** nothing to do. The next deploy rebuilds the dataset.
- **A new field or category:** add it in `tools/build_mcp_data.mjs` (dataset) and `netlify/functions/_lib/mcp-core.mjs` (tools).
- **Local test:** run `node tools/build_mcp_data.mjs`, then call the default export of `netlify/functions/mcp.mjs` with a `Request`. Calls are logged as `{"mcp":"call",…}` lines in the Netlify function log.

## Hidden sections

`features.json` switches hub sections off without deleting them (see `docs/features-README.md`). While `idea_exchange` is false, `/mcp` drops `get_idea_moves`, the `idea_move` filter, the `idea_moves` search category, and every `idea_moves` field in results.
