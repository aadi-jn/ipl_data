# IPL Analytics Showcase — Project Plan

**Owner:** Aadi Jain | **Started:** March 2026 | **Goal:** Land a Head of Data / Analytics Manager role at a Series A-B consumer startup in Bangalore within 1-2 months.

---

## The Thesis

IPL season is live. India's data community is engaged. Build a public, AI-augmented analytics tool on IPL data — and document the entire journey of building it.

**The product:** A website that delivers real-time, AI-powered insights on IPL — not just stats, but contextual analysis that feels like having an analytics leader watching every match with you.

**The content play:** Build in public on LinkedIn. Share the behind-the-scenes of the craft — finding and evaluating data sources, building pipelines, optimizing tables for analytical queries, making data AI-ready, prompt engineering for sports insights. The data community eats this up because it's *their* work, applied to something they care about.

1. **Gets eyeballs** — 2-3 LinkedIn posts/week showing the build process: pipeline decisions, data modeling choices, AI integration challenges, and the resulting insights
2. **Signals leadership** — the *how* and *why* behind each technical decision demonstrates analytics leadership thinking, not just execution
3. **Showcases AI chops** — the tool itself is the proof: real-time AI-augmented insights on live data, built end-to-end
4. **Creates inbound** — hiring managers at consumer startups see someone who can build an AI-ready data stack from scratch

**One-line pitch:** "I built an AI-powered IPL insights engine from raw data to real-time analysis — and documented every decision along the way."

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

### Phase 1: Data Foundation (Week 1)
**Goal:** Get ball-by-ball data into Athena so rich analysis is possible.

- [ ] Process and upload ball-by-ball/deliveries data to S3 (Parquet)
- [ ] Add Glue table definitions for `deliveries` and `match_players`
- [ ] Validate data quality — row counts, nulls, edge cases
- [ ] Build a few key derived views/tables:
  - Player career stats (runs, wickets, strike rate, economy)
  - Team season summaries
  - Venue performance
  - Powerplay / middle overs / death overs splits

### Phase 2: Auto-Insights Engine (Week 1-2)
**Goal:** Build the AI-powered "wow factor" — an engine that surfaces interesting patterns automatically.

This is the core differentiator. Not a chatbot. Not NL-to-SQL. An **automated insight generator** that:

1. Runs a battery of analytical queries against the IPL data
2. Feeds results to an LLM (Claude via Bedrock) with a prompt like: *"You are an analytics leader at an IPL franchise. Here's the data. What's surprising? What's actionable? What would you present to the team owner?"*
3. Surfaces ranked insights with supporting data and visualizations
4. Frames everything as **business decisions**, not just stats

**Why this matters for the job search:** Every target role in job-filter.md mentions "AI tooling" and "self-serve analytics." This feature IS that — an AI system that generates insights without anyone asking.

**Example auto-insights:**
- "RCB's powerplay run rate has dropped 15% since 2022 — but their middle-overs acceleration is league-best. They're shifting strategy."
- "Teams batting first at Chinnaswamy win 62% when scoring 180+, but only 31% at 160-179. There's a sharp cliff — not a gradient."
- "Player X has the highest death-over economy in the league but only gets 2 overs/match. Underutilized or mistrusted?"

### Phase 3: Visualization Layer (Week 2-3)
**Goal:** Transform the site from SQL editor to an analytics showcase with interactive charts.

- [ ] Choose a charting library (Recharts or Chart.js — keep it simple)
- [ ] Build 6-8 interactive visualizations, each designed to be a LinkedIn post:
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

### Phase 4: Content Engine (Week 2-4, ongoing)
**Goal:** 2-3 LinkedIn posts/week during IPL season. Mix of content types — not every post needs to point in the same direction.

**Pillar A: Build in Public** — behind-the-scenes of building the tool
- "I found 1,169 IPL matches in YAML files. Here's how I turned them into a queryable data lake."
- "Optimizing Parquet tables for AI — what 'AI-ready data' actually means in practice"
- "Why I chose Athena over BigQuery for this project (and when I'd choose differently)"
- "Prompt engineering for sports analytics — what works, what hallucinates, what surprises"
- Pipeline diagrams, code snippets, architecture decisions

**Pillar B: IPL Insights & Analysis** — genuinely interesting findings from the data
- Surprising stats, contrarian takes, myth-busting (e.g., toss impact)
- Deep-dives on teams, players, venues, eras
- AI-generated insights with the "so what" framed as strategy/business decisions
- Screenshots/recordings of the tool in action on live matches

**Content format per post:**
1. Hook (1 line — surprising stat, behind-the-scenes moment, or contrarian take)
2. The substance (2-4 lines — insight, decision, or discovery)
3. Visual (chart screenshot, tool demo, pipeline diagram, or code snippet)
4. CTA (link to the live tool)

**Rough calendar (flexible — go with what's interesting):**

| Week | Mix | Example posts |
|------|-----|---------------|
| 1 | Build in public | "I'm building an AI-powered IPL insights engine" / Data pipeline walkthrough |
| 2 | Insights + build | Player/team deep-dive / "Making 200K deliveries AI-ready" |
| 3 | AI reveal + insights | "What AI sees in IPL data that dashboards can't" / Tool demo + a finding |
| 4 | Both | Live tool on current matches / "How I built this" deep-dive |
| 5+ | Whatever works | React to live IPL 2026 / Ongoing mix of both pillars |

**Experiment and iterate.** See which pillar gets more engagement and lean into it.

### Phase 5: Polish & Portfolio (Week 3-4)
**Goal:** Make the site interview-ready.

- [ ] Add an "About" section explaining the project's tech stack and approach
- [ ] Mobile-responsive design (LinkedIn audience is 60%+ mobile)
- [ ] Custom domain (optional but professional)
- [ ] Open-source the analysis notebooks/queries (shows transparency)
- [ ] Performance optimization (fast loads, no spinners)

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
| AI model | Claude via Bedrock | Already in ap-south-1, no API key management, pay-per-use |
| Charts | TBD (Recharts vs Chart.js) | Need to evaluate — Recharts is React-native, Chart.js is more flexible |
| Data processing | Python scripts (local) → Parquet → S3 | Simple, repeatable, no Spark overhead for this data size |
| Content screenshots | TBD | May need a way to export charts as images for LinkedIn posts |
| Live data updates | Out of scope initially | Would need a scraping/API pipeline — defer unless IPL 2026 analysis becomes the hook |

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

### Must resolve before building

1. **Ball-by-ball data format:** What format is the data in? (CSV, YAML, JSON?) Need to plan the processing pipeline.
2. **Bedrock access:** Is Claude model enabled in Bedrock for your AWS account in ap-south-1? Need to check/enable.
3. **Budget:** What's the monthly AWS spend ceiling? Athena + Bedrock can add up with heavy querying.

### Should resolve during building

4. **Chart library:** Recharts (React-native, easier) vs Chart.js (more chart types, bigger community). Need to prototype both.
5. **Custom domain:** Worth buying one? (e.g., iplanalytics.in) Adds professionalism but costs time to set up.
6. **Mobile experience:** How much effort to invest? LinkedIn mobile users will click through — a bad mobile experience kills credibility.
7. **Open-sourcing:** GitHub repo public from day 1, or reveal later for a "how I built this" post?

### Nice to resolve eventually

8. **Live IPL 2026 data:** Is there an API or data source for current-season matches? Real-time analysis would be a massive engagement driver.
9. **Collaboration:** Any data friends who'd co-create content? Shared posts get more reach.
10. **Post-IPL longevity:** What happens to the site after IPL season? Does it become a permanent portfolio piece or sunset?

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI insights are generic/boring | Project loses its differentiator | Invest heavily in prompt engineering; frame insights as franchise-level decisions, not trivia |
| Low LinkedIn engagement | No eyeballs → no job leads | Test hooks with smaller posts first; engage with others' IPL content to build momentum |
| Time crunch (10-20 hrs/week) | Can't ship all phases | Phase 1-2 are non-negotiable; Phase 5 is nice-to-have. Ship imperfect > ship late |
| Cricket domain gaps | Analysis feels shallow to real fans | Lean into the "analytics leader perspective" framing — you're not competing with Cricbuzz on cricket knowledge |
| AWS costs spiral | Bedrock + Athena costs | Set billing alarms; cache AI-generated insights; limit Athena scans with partitioning |

---

## Weekly Plan (4-week sprint)

### Week 1 (Mar 31 - Apr 6)
- Process and upload ball-by-ball data
- Build derived tables/views
- Enable Bedrock, prototype auto-insights Lambda
- First LinkedIn post: "I analyzed every IPL match ever played. Here's what I found."

### Week 2 (Apr 7 - Apr 13)
- Build auto-insights engine (queries → LLM → ranked insights)
- Start visualization layer (2-3 charts)
- LinkedIn posts: player/team deep-dives with chart screenshots

### Week 3 (Apr 14 - Apr 20)
- Complete visualization layer (6-8 charts)
- Build the "AI Insights" page on the site
- LinkedIn posts: AI insights reveal + methodology
- Polish mobile experience

### Week 4 (Apr 21 - Apr 27)
- About page, portfolio polish
- "How I built this" LinkedIn post (tech stack + process)
- Start applying to target-archetype companies with project as portfolio centerpiece
- Retrospective: what worked, what to keep posting

---

*This is a living document. Update it as decisions are made and priorities shift.*
