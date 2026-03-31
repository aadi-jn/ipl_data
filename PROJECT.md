# IPL Analytics Showcase — Project Plan

**Owner:** Aadi Jain | **Started:** March 2026 | **Timeline:** 9 weeks (Mar 31 – Jun 1, 2026, aligned with IPL season)
**Goal:** Land a Head of Data / Analytics Manager role at a Series A-B consumer startup in Bangalore — and build a genuinely useful product in the process.

---

## The Thesis

IPL season is live. India's data community is engaged. Build a public, AI-augmented analytics tool on IPL data — and document the entire journey of building it.

**The product:** A fully functional, AI-augmented IPL analytics platform — not a portfolio piece, but a real product with 7-8 distinct analysis tabs, real-time match features, MCP servers for programmatic access, and a path to monetization. Not just stats, but contextual analysis that feels like having an analytics leader watching every match with you.

**The content play:** Build in public on LinkedIn. Share the behind-the-scenes of the craft — finding and evaluating data sources, building pipelines, optimizing tables for analytical queries, making data AI-ready, prompt engineering for sports insights. The data community eats this up because it's *their* work, applied to something they care about.

1. **Gets eyeballs** — 2-3 LinkedIn posts/week showing the build process: pipeline decisions, data modeling choices, AI integration challenges, and the resulting insights
2. **Signals leadership** — the *how* and *why* behind each technical decision demonstrates analytics leadership thinking, not just execution
3. **Showcases AI chops** — the tool itself is the proof: real-time AI-augmented insights on live data, built end-to-end
4. **Creates inbound** — hiring managers at consumer startups see someone who can build an AI-ready data stack from scratch

**One-line pitch:** "I built an AI-powered IPL insights engine from raw data to real-time analysis — and documented every decision along the way."

**Target users:** Tech-savvy cricket fans, data professionals, journalists — people who appreciate depth and want programmatic access to IPL data. Good overlap with Aadi's target hiring audience.

---

## Target Audience

**Primary:** India's data community on LinkedIn — fellow analysts, data scientists, analytics managers. They engage, share, and amplify.

**Secondary (reached through primary):** Hiring managers and founders at Series A-B consumer startups in Bangalore who see the content via their data team's shares.

**Not the audience:** Recruiters (they won't understand the technical depth), general cricket fans (they have Cricbuzz).

---

## What Exists Today

| Component | Status | Notes |
|-----------|--------|-------|
| AWS infra (S3, Glue, Athena, Lambda, API Gateway, CloudFront) | Deployed | CDK stack, ap-south-1 |
| SQL query interface | Live | [d35f2okpod3reh.cloudfront.net](https://d35f2okpod3reh.cloudfront.net) |
| Match-level data | 1,169 rows | 2008-2025, Parquet in S3 |
| Ball-by-ball data | Available locally | Not yet uploaded/processed |
| React + Vite frontend | Deployed | Single-page SQL editor, minimal UI |

---

## What We're Building

The project has three broad phases. Weeks 1-3 are about getting all the data into one place and building stable infrastructure. Around week 4, it shifts to AI-enabled features because the data is ready and tested. Beyond that, it shifts to NL queries, animated summaries, MCP connectors, and more engaging features.

Priorities will change almost every week as we see what's easy, what's hard, what's needed, and what doesn't matter. See `project-docs/weekly_plan.md` for the concrete week-by-week breakdown.

### Phase 1: Data Foundation & First Impressions (Weeks 1-3)
**Goal:** All data ingested, stable infrastructure, a frontend people want to use, and pre-match analysis live.

- [ ] Process and upload ball-by-ball/deliveries data to S3 (Parquet)
- [ ] Add Glue table definitions for `deliveries` and `match_players`
- [ ] Validate data quality — row counts, nulls, edge cases
- [ ] Build derived tables/views:
  - Player career stats (runs, wickets, strike rate, economy)
  - Team season summaries
  - Venue performance
  - Powerplay / middle overs / death overs splits
- [ ] Redesign frontend from SQL editor to a real analytics interface
- [ ] Pre-match analysis cards from historical data (H2H, venue, form, toss)
- [ ] Mobile-responsive layout
- [ ] Deep ball-by-ball analytics (phase-wise performance, player matchups) — week 3
- [ ] 6-8 interactive visualizations, each designed to also be a LinkedIn post:
  1. **Team dominance timeline** — which teams dominated which eras (heatmap or bump chart)
  2. **Toss impact analysis** — does winning toss actually matter? (spoiler: it's nuanced)
  3. **Death overs specialists** — who owns the last 4 overs? (scatter: economy vs wickets)
  4. **Powerplay evolution** — how has first-6-overs strategy changed over 17 seasons?
  5. **Venue personality** — each ground has a "character" (high-scoring, spin-friendly, etc.)
  6. **Clutch performers** — who performs best in high-pressure situations?
  7. **The "AI Insights" page** — auto-generated insights with supporting charts
  8. **Season-over-season trends** — IPL's evolution as a league
- [ ] Each visualization should have:
  - A compelling headline (LinkedIn-ready)
  - The insight in 1-2 sentences (the "so what")
  - Interactive chart (hover, filter, drill-down)
  - A "methodology" expandable section (shows analytical rigor)

### Phase 2: Auto-Insights Engine (Weeks 2-4)
**Goal:** Build the AI-powered "wow factor" — an engine that surfaces interesting patterns automatically.

This is the core differentiator. Not a chatbot. Not NL-to-SQL. An **automated insight generator** that:

1. Runs a battery of analytical queries against the IPL data
2. Feeds results to an LLM with a prompt like: *"You are an analytics leader at an IPL franchise. Here's the data. What's surprising? What's actionable? What would you present to the team owner?"*
3. Surfaces ranked insights with supporting data and visualizations
4. Frames everything as **business decisions**, not just stats

Auto-insights are generated once per match day (or twice if there are two games). This keeps costs minimal while delivering high value. Testing will use local/free open-source models before any paid API.

**Why this matters for the job search:** Every target role in job-filter.md mentions "AI tooling" and "self-serve analytics." This feature IS that — an AI system that generates insights without anyone asking.

**Example auto-insights:**
- "RCB's powerplay run rate has dropped 15% since 2022 — but their middle-overs acceleration is league-best. They're shifting strategy."
- "Teams batting first at Chinnaswamy win 62% when scoring 180+, but only 31% at 160-179. There's a sharp cliff — not a gradient."
- "Player X has the highest death-over economy in the league but only gets 2 overs/match. Underutilized or mistrusted?"

### Phase 3: Real-Time & AI Features (Weeks 4-5)
**Goal:** Integrate live IPL 2026 data and shift to AI-enabled use cases.

- [ ] Real-time data pipeline from live data source
- [ ] Live match context: par scores, win probability, phase comparisons
- [ ] Post-match analysis cards (turning points, player ratings, AI-generated summaries)
- [ ] Points table with playoff math and NRR scenarios
- [ ] Auto-insights running daily on live matches
- [ ] Additional tabs: team analysis, player leaderboards, season narratives

### Phase 4: NL Queries & Programmatic Access (Weeks 6-8)
**Goal:** Open up the data for users to query directly, and provide programmatic access.

**Natural language queries** are not as simple as they look. They require:
- Guardrails around outputs
- Metric definitions and context for the LLM
- Testing with real users before going public
- A backend that can handle complex/deep follow-up questions

NL queries will be tested locally with open-source models throughout the project, but only go public once tested and validated — likely week 7 at the earliest.

- [ ] NL query engine — internal testing (week 6), public launch (week 7 if ready)
- [ ] MCP servers for programmatic access (Claude, Slack)
- [ ] Text-based data sources: commentary, pre-match analysis
- [ ] Animated match summaries or richer post-match content
- [ ] Shareable stat cards, social content features

### Phase 5: Season Wrap & Future (Week 9)
**Goal:** End-of-season content, polish, and decide what continues post-IPL.

- [ ] Player and team season summaries
- [ ] NRR, points table race, playoff projections
- [ ] Player performances over time across the IPL
- [ ] About page / project story for new visitors
- [ ] Speed, mobile, visual consistency polish
- [ ] Retrospective: what worked, what to keep running

### Content Engine (Ongoing, Weeks 1-9)
**Goal:** ~4 LinkedIn posts/week during IPL season. Two pillars running in parallel.

**Pillar A: Project Outcomes** (~2 posts/week) — insights, charts, features from the tool
- Surprising stats, contrarian takes, myth-busting (e.g., toss impact)
- Deep-dives on teams, players, venues, eras
- AI-generated insights with the "so what" framed as strategy/business decisions
- Screenshots/recordings of the tool in action on live matches

**Pillar B: AI Analytics Narrative** (~2 posts/week) — behind-the-scenes, collaboration, broader AI analytics thinking
- "I found 1,169 IPL matches in YAML files. Here's how I turned them into a queryable data lake."
- "Optimizing Parquet tables for AI — what 'AI-ready data' actually means in practice"
- "Why I chose Athena over BigQuery for this project (and when I'd choose differently)"
- "Prompt engineering for sports analytics — what works, what hallucinates, what surprises"
- Pipeline diagrams, code snippets, architecture decisions
- Invitations to collaborate, feedback requests

**Content format per post:**
1. Hook (1 line — surprising stat, behind-the-scenes moment, or contrarian take)
2. The substance (2-4 lines — insight, decision, or discovery)
3. Visual (chart screenshot, tool demo, pipeline diagram, or code snippet)
4. CTA (link to the live tool)

**Experiment and iterate.** See which pillar gets more engagement and lean into it.

---

## Architecture (Target State)

```
┌─────────────────────────────────────────────────┐
│                   CloudFront                      │
│         React SPA + Interactive Charts            │
└──────────────┬──────────────────┬────────────────┘
               │                  │
    ┌──────────▼──────┐  ┌───────▼────────┐
    │   API Gateway    │  │  Static Assets  │
    │   /query (SQL)   │  │  (S3 bucket)    │
    │   /insights (AI) │  │                 │
    └──────────┬───────┘  └─────────────────┘
               │
    ┌──────────▼──────────┐
    │      Lambda          │
    │  query_runner (SQL)  │
    │  insight_gen (AI)    │
    └───┬─────────────┬────┘
        │             │
   ┌────▼────┐  ┌─────▼─────┐
   │ Athena   │  │  Bedrock   │
   │ (SQL)    │  │  (Claude)  │
   └────┬─────┘  └───────────┘
        │
   ┌────▼──────────────┐
   │  S3 Data Lake      │
   │  matches/          │
   │  deliveries/       │
   │  match_players/    │
   │  derived/          │
   └────────────────────┘
```

---

## Tech Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| AI model (testing) | Local open-source models | Free, no API costs, good enough for prototyping and internal testing |
| AI model (production) | TBD — Bedrock or other | Defer until NL queries go public; auto-insights can use local models initially |
| Charts | TBD (Recharts vs Chart.js) | Need to evaluate — Recharts is React-native, Chart.js is more flexible |
| Data processing | Python scripts (local) → Parquet → S3 | Simple, repeatable, no Spark overhead for this data size |
| Content screenshots | TBD | May need a way to export charts as images for LinkedIn posts |
| Live data updates | In scope (weeks 4-5) | Data sources exist; pipeline to be built when foundation is stable |
| MCP servers | In scope (weeks 6-8) | Programmatic access via Claude/Slack for users |

---

## Success Metrics

Not vanity metrics. Outcomes that lead to the job:

| Metric | Target | Why it matters |
|--------|--------|----------------|
| LinkedIn post impressions | 10K+ on at least 2 posts | Proves reach into the data community |
| Profile views spike | 3-5x baseline during content series | People are checking you out |
| Inbound messages | 3+ "let's chat" DMs from data/analytics leaders | Direct pipeline |
| Interview conversations | 2+ interviews at target-archetype companies | The actual goal |
| Site visits | 500+ unique visitors | Shows the content drove traffic |

---

## Open Questions

### Resolved

1. **Ball-by-ball data format:** JSON from Cricsheet. See `project-docs/data_format.md` for full reference.
2. **Budget:** $120 AWS free credits for 6 months. Stay within this. No Bedrock spend yet — local models for testing.
3. **Live IPL 2026 data:** Data sources exist. Will integrate in weeks 4-5.
4. **Timeline:** 9 weeks (Mar 31 – Jun 1), not 4. Realistic pace alongside job search and other commitments.

### Should resolve during building

5. **Chart library:** Recharts (React-native, easier) vs Chart.js (more chart types, bigger community). Need to prototype both.
6. **Custom domain:** Worth buying one? (e.g., iplanalytics.in) Adds professionalism but costs time to set up.
7. **Open-sourcing:** GitHub repo public from day 1, or reveal later for a "how I built this" post?
8. **Bedrock vs alternatives:** When auto-insights or NL queries go to production, which AI backend? Defer until week 4+.

### Nice to resolve eventually

9. **Collaboration:** Any data friends who'd co-create content? Shared posts get more reach.
10. **Post-IPL longevity:** What happens to the site after IPL season? This is a product, not just a season project — what's the longer-term vision?
11. **Monetization:** Pay tier for MCP/API access or premium features. When and how?

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI insights are generic/boring | Project loses its differentiator | Invest heavily in prompt engineering; frame insights as franchise-level decisions, not trivia |
| Low LinkedIn engagement | No eyeballs → no job leads | Test hooks with smaller posts first; engage with others' IPL content to build momentum |
| Time crunch (limited hrs/week) | Can't ship all phases | Phase 1-2 are non-negotiable; later phases flex. Ship imperfect > ship late |
| Cricket domain gaps | Analysis feels shallow to real fans | Lean into the "analytics leader perspective" framing — you're not competing with Cricbuzz on cricket knowledge |
| AWS costs spiral | Bedrock + Athena costs | Set billing alarms; cache AI-generated insights; limit Athena scans with partitioning |

---

## Weekly Plan (9 weeks)

See `project-docs/weekly_plan.md` for the detailed week-by-week breakdown.

**Summary of the arc:**
- **Weeks 1-3:** Data foundation, stable infrastructure, pre-match analysis, frontend redesign, first visualizations
- **Week 4:** Shift to AI-enabled features — auto-insights on live matches, post-match analysis
- **Week 5:** Real-time data pipeline, live match features
- **Weeks 6-7:** NL queries (test then launch), MCP servers, text-based data sources
- **Week 8:** Connectors (Slack, Claude), social features, end-of-season analytics
- **Week 9:** Season wrap, polish, retrospective

Priorities will shift weekly. The weekly plan has 4-6 concrete items per week — enough to stay focused, flexible enough to adapt.

---

*This is a living document. Update it as decisions are made and priorities shift.*

---

## Frontend Theme — CricInfo-Inspired (Applied Mar 31, 2026)

- **Nav bar:** Cerulean blue gradient header (`#0398DC`) with white text, cricket ball icon, match count badges
- **Backgrounds:** Light gray (`#F2F3F5`) page, white cards — clean editorial look
- **Typography:** DM Sans for body, JetBrains Mono for code/SQL
- **Tables:** White with blue header accent stripe, alternating row tint, blue sort indicators
- **Query builder:** Card-based layout with header bar, example pills along the bottom, blue gradient "Run Query" button
- **Breadcrumb strip:** `Stats / IPL / Query Builder` under nav
- **Error states:** Soft red card with proper icon
- **Animations:** Subtle fade-in on load, slide-down on schema expand
- **CSS variables** for full theme consistency
