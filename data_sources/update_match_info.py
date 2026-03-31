"""
Download IPL YAML data from Cricsheet, parse new matches, and update match_info CSV + Parquet.
Run manually: python3 data_sources/update_match_info.py

Optionally upload to S3 after:
  aws s3 cp data_modeling/match_info.parquet s3://ipl-processed-data-814871720600/matches/match_info.parquet

"""

import csv
import io
import os
import tempfile
import urllib.request
import zipfile

import yaml

ZIP_URL = "https://cricsheet.org/downloads/ipl_male.zip"
CSV_PATH = "data_modeling/match_info.csv"
PARQUET_PATH = "data_modeling/match_info.parquet"


def get_existing_filenames():
    """Read current CSV and return set of filenames already processed."""
    if not os.path.exists(CSV_PATH):
        return set()
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        return {row["filename"] for row in reader}


def parse_yaml(content):
    """Parse a single Cricsheet YAML file into a match_info row dict."""
    match = yaml.safe_load(content)
    info = match["info"]
    toss = info.get("toss", {})
    outcome = info.get("outcome", {})
    umpires = info.get("umpires", [])
    pom = info.get("player_of_match", [])

    winner = outcome.get("winner")
    result = outcome.get("result")
    by = outcome.get("by", {})
    if "runs" in by:
        win_type, win_margin = "runs", by["runs"]
    elif "wickets" in by:
        win_type, win_margin = "wickets", by["wickets"]
    else:
        win_type, win_margin = None, None

    if not winner and result:
        if "eliminator" in outcome:
            winner = outcome["eliminator"]
        elif "bowl_out" in outcome:
            winner = outcome["bowl_out"]

    return {
        "season": str(info.get("season", "")) or None,
        "match_number": (info.get("event") or {}).get("match_number"),
        "date": info["dates"][0],
        "team1": info["teams"][0],
        "team2": info["teams"][1],
        "city": info.get("city"),
        "venue": info.get("venue"),
        "neutral_venue": info.get("neutral_venue"),
        "toss_winner": toss.get("winner"),
        "toss_decision": toss.get("decision"),
        "winner": winner,
        "win_type": win_type,
        "win_margin": win_margin,
        "result": result,
        "method": outcome.get("method"),
        "eliminator": outcome.get("eliminator"),
        "player_of_match": pom[0] if pom else None,
        "umpire1": umpires[0] if len(umpires) > 0 else None,
        "umpire2": umpires[1] if len(umpires) > 1 else None,
    }


FIELDNAMES = [
    "filename", "season", "match_number", "date", "team1", "team2",
    "city", "venue", "neutral_venue", "toss_winner", "toss_decision",
    "winner", "win_type", "win_margin", "result", "method",
    "eliminator", "player_of_match", "umpire1", "umpire2",
]


def main():
    existing = get_existing_filenames()
    print(f"Existing matches in CSV: {len(existing)}")

    # Download zip
    print("Downloading Cricsheet IPL zip...")
    with urllib.request.urlopen(ZIP_URL, timeout=120) as resp:
        zip_bytes = resp.read()
    print(f"Downloaded {len(zip_bytes) / 1024 / 1024:.1f} MB")

    # Find new YAML files
    new_rows = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        yaml_files = [n for n in zf.namelist() if n.endswith(".yaml")]
        print(f"Total YAML files in zip: {len(yaml_files)}")

        for name in yaml_files:
            filename = os.path.basename(name)
            if filename in existing:
                continue
            with zf.open(name) as yf:
                row = parse_yaml(yf.read().decode("utf-8"))
                row["filename"] = filename
                new_rows.append(row)

    if not new_rows:
        print("No new matches found. CSV is up to date.")
        return

    # Sort new rows by filename number
    new_rows.sort(key=lambda r: int(r["filename"].replace(".yaml", "")))
    print(f"New matches to add: {len(new_rows)}")
    for r in new_rows:
        print(f"  + {r['filename']}  {r['date']}  {r['team1']} vs {r['team2']}")

    # Append to CSV
    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)
    print(f"Appended {len(new_rows)} rows to {CSV_PATH}")

    # Rebuild Parquet from full CSV
    try:
        import pandas as pd
        df = pd.read_csv(CSV_PATH)
        df.to_parquet(PARQUET_PATH, index=False, engine="pyarrow")
        print(f"Updated {PARQUET_PATH} ({len(df)} total rows)")
    except ImportError:
        print("pandas/pyarrow not installed — skipped Parquet generation.")
        print("Install with: pip install pandas pyarrow")


if __name__ == "__main__":
    main()
