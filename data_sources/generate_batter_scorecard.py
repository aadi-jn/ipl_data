"""
Generate per-match batter scorecards from ball-by-ball data.

For each match and each batter, produces:
- Entry context: team score, wickets fallen, over, bowler when batter came in
- Progressive scores: runs after 5, 10, 20, 30, 40, 50 balls faced
- Final stats: total runs, balls faced, out/not out, dismissal kind
- Innings context: innings number (1 = setting, 2 = chasing)

Output: data_modeling/batter_scorecard.csv and data_modeling/batter_scorecard.parquet
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data_modeling"
MILESTONE_BALLS = [5, 10, 20, 30, 40, 50]


def build_scorecards(df: pd.DataFrame) -> pd.DataFrame:
    """Build batter scorecards from ball-by-ball DataFrame."""
    records = []

    # Group by match and innings
    for (match_id, innings), innings_df in df.groupby(["match_id", "innings"]):
        innings_df = innings_df.sort_values(["over", "ball"]).reset_index(drop=True)

        # Track team score and wickets as the innings progresses
        team_runs_cumulative = innings_df["total_runs"].cumsum()
        wickets_cumulative = innings_df["is_wicket"].cumsum()

        # Match-level context from first row
        first = innings_df.iloc[0]
        match_ctx = {
            "match_id": first["match_id"],
            "date": first["date"],
            "venue": first["venue"],
            "city": first["city"],
            "season": first["season"],
            "batting_team": first["batting_team"],
            "bowling_team": first["bowling_team"],
            "innings": first["innings"],
        }

        # For each batter in this innings
        batter_groups = innings_df.groupby("batter")

        for batter_name, batter_df in batter_groups:
            # Balls faced = deliveries where batter is on strike, excluding wides
            # (wides don't count as balls faced in cricket)
            balls_faced_mask = batter_df["wides"] == 0
            balls_faced_df = batter_df[balls_faced_mask].reset_index(drop=True)

            if len(balls_faced_df) == 0:
                continue

            # --- Entry context ---
            # Find the first ball this batter faced in the innings
            first_ball_idx = batter_df.index[0]  # index in innings_df
            if first_ball_idx == 0:
                entry_score = 0
                entry_wickets = 0
            else:
                entry_score = int(team_runs_cumulative.iloc[first_ball_idx - 1])
                entry_wickets = int(wickets_cumulative.iloc[first_ball_idx - 1])
            entry_over = batter_df.iloc[0]["over"]
            entry_bowler = batter_df.iloc[0]["bowler"]

            # --- Progressive scores at milestone balls ---
            batter_runs_cum = balls_faced_df["batter_runs"].cumsum()
            milestone_scores = {}
            for m in MILESTONE_BALLS:
                if len(batter_runs_cum) >= m:
                    milestone_scores[f"runs_after_{m}_balls"] = int(batter_runs_cum.iloc[m - 1])
                else:
                    milestone_scores[f"runs_after_{m}_balls"] = None

            # --- Final stats ---
            total_runs = int(batter_df["batter_runs"].sum())
            total_balls = int(balls_faced_mask.sum())

            # Dismissal: check if this batter was the player_out on any delivery
            dismissal_rows = innings_df[innings_df["player_out"] == batter_name]
            if len(dismissal_rows) > 0:
                out = True
                dismissal_kind = dismissal_rows.iloc[0]["dismissal_kind"]
                dismissal_bowler = dismissal_rows.iloc[0]["bowler"]
                dismissal_fielder = dismissal_rows.iloc[0]["fielder"]
            else:
                out = False
                dismissal_kind = ""
                dismissal_bowler = ""
                dismissal_fielder = ""

            record = {
                **match_ctx,
                "batter": batter_name,
                "entry_score": entry_score,
                "entry_wickets": entry_wickets,
                "entry_over": entry_over,
                "entry_bowler": entry_bowler,
                **milestone_scores,
                "total_runs": total_runs,
                "total_balls_faced": total_balls,
                "out": out,
                "dismissal_kind": dismissal_kind,
                "dismissal_bowler": dismissal_bowler,
                "dismissal_fielder": dismissal_fielder,
            }
            records.append(record)

    return pd.DataFrame(records)


def main():
    csv_path = DATA_DIR / "ball_by_ball.csv"
    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} deliveries across {df['match_id'].nunique()} matches")

    # Fill NaN in string columns to avoid comparison issues
    df["player_out"] = df["player_out"].fillna("")
    df["dismissal_kind"] = df["dismissal_kind"].fillna("")
    df["fielder"] = df["fielder"].fillna("")
    df["wides"] = df["wides"].fillna(0).astype(int)
    df["season"] = df["season"].astype(str)

    scorecard = build_scorecards(df)
    print(f"Generated {len(scorecard)} batter scorecards")
    print(f"Matches: {scorecard['match_id'].nunique()}")
    print(f"Sample columns: {list(scorecard.columns)}")

    # Summary stats
    print(f"\nBalls faced distribution:")
    print(scorecard["total_balls_faced"].describe().to_string())
    print(f"\nDismissal types:")
    print(scorecard[scorecard["out"]]["dismissal_kind"].value_counts().head(10).to_string())

    # Save
    out_csv = DATA_DIR / "batter_scorecard.csv"
    out_parquet = DATA_DIR / "batter_scorecard.parquet"
    scorecard.to_csv(out_csv, index=False)
    scorecard.to_parquet(out_parquet, index=False)
    print(f"\nSaved to {out_csv} and {out_parquet}")


if __name__ == "__main__":
    main()
