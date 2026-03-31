"""
Extract ball-by-ball data from Cricsheet JSON files into a CSV + Parquet.

Reads all JSON files from ipl_json/ directory and produces a flat DataFrame
with one row per delivery, including match context from the info block.

Output: data_modeling/ball_by_ball.csv and data_modeling/ball_by_ball.parquet
"""

import json
import os
import pandas as pd
from pathlib import Path

JSON_DIR = Path(__file__).resolve().parent.parent.parent / "ipl_json"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data_modeling"


def extract_match(filepath: Path) -> list[dict]:
    """Extract all deliveries from a single match JSON file."""
    with open(filepath) as f:
        data = json.load(f)

    match_id = filepath.stem
    info = data["info"]

    # Match-level context
    match_ctx = {
        "match_id": int(match_id),
        "date": info["dates"][0],
        "venue": info.get("venue", ""),
        "city": info.get("city", ""),
        "team1": info["teams"][0],
        "team2": info["teams"][1],
        "season": str(info.get("season", "")),
    }

    rows = []
    for innings_num, innings in enumerate(data["innings"], start=1):
        batting_team = innings["team"]
        bowling_team = match_ctx["team2"] if batting_team == match_ctx["team1"] else match_ctx["team1"]

        for over_data in innings.get("overs", []):
            over_num = over_data["over"]  # 0-indexed
            for ball_idx, delivery in enumerate(over_data["deliveries"], start=1):
                runs = delivery["runs"]
                extras = delivery.get("extras", {})

                row = {
                    **match_ctx,
                    "innings": innings_num,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "over": over_num + 1,  # 1-indexed for readability
                    "ball": ball_idx,
                    "batter": delivery["batter"],
                    "bowler": delivery["bowler"],
                    "non_striker": delivery["non_striker"],
                    "batter_runs": runs["batter"],
                    "extras_total": runs["extras"],
                    "total_runs": runs["total"],
                    "wides": extras.get("wides", 0),
                    "noballs": extras.get("noballs", 0),
                    "byes": extras.get("byes", 0),
                    "legbyes": extras.get("legbyes", 0),
                    "penalty": extras.get("penalty", 0),
                    "is_wicket": 0,
                    "player_out": "",
                    "dismissal_kind": "",
                    "fielder": "",
                }

                # Handle wickets (can be multiple per delivery, e.g., run out both ends)
                if "wickets" in delivery:
                    wickets = delivery["wickets"]
                    row["is_wicket"] = 1
                    # Take first wicket for main columns
                    w = wickets[0]
                    row["player_out"] = w["player_out"]
                    row["dismissal_kind"] = w["kind"]
                    fielders = w.get("fielders", [])
                    row["fielder"] = fielders[0]["name"] if fielders else ""

                    # If multiple wickets on same ball, add extra rows
                    for w2 in wickets[1:]:
                        row2 = row.copy()
                        row2["player_out"] = w2["player_out"]
                        row2["dismissal_kind"] = w2["kind"]
                        fielders2 = w2.get("fielders", [])
                        row2["fielder"] = fielders2[0]["name"] if fielders2 else ""
                        rows.append(row2)

                rows.append(row)

    return rows


def main():
    json_files = sorted(JSON_DIR.glob("*.json"))
    print(f"Found {len(json_files)} JSON files in {JSON_DIR}")

    all_rows = []
    errors = []
    for i, fp in enumerate(json_files):
        try:
            all_rows.extend(extract_match(fp))
        except Exception as e:
            errors.append((fp.name, str(e)))
        if (i + 1) % 200 == 0:
            print(f"  Processed {i + 1}/{len(json_files)} files...")

    print(f"Processed {len(json_files)} files, {len(errors)} errors")
    if errors:
        for name, err in errors[:10]:
            print(f"  ERROR {name}: {err}")

    df = pd.DataFrame(all_rows)
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    # Save
    csv_path = OUTPUT_DIR / "ball_by_ball.csv"
    parquet_path = OUTPUT_DIR / "ball_by_ball.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    print(f"Saved to {csv_path} and {parquet_path}")


if __name__ == "__main__":
    main()
