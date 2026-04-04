# Backlog

Prioritized list of pending improvements, tech debt, and feature ideas. Items move off this list when they're done or explicitly dropped.

---

## High Priority

*(empty)*

## Medium Priority

*(empty)*

## Low Priority

- **Review `fetch_matches.py` usage**: The full IPL 2026 schedule is already committed in `data_sources/ipl_2026_matches.csv`. `fetch_matches.py` (CricAPI) is not in the daily pipeline but is still available as a manual script. Confirm it's not being called unnecessarily anywhere, and decide whether to retire it or keep it for future seasons only.

- **Review local Python scripts in `data_sources/`**: Three scripts (`update_match_info.py`, `extract_ball_by_ball.py`, `generate_batter_scorecard.py`) are superseded by the Lambda ingestion pipeline. Decide whether to keep as local fallback utilities or remove. `generate_home_grounds.py` output (`home_grounds.json`) doesn't appear to be used downstream — confirm and potentially remove.

## Done / Dropped

*(empty)*
