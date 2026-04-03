"""
Daily ingestion Lambda: fetch new IPL matches from Cricsheet, update S3 parquets.

Handles three datasets incrementally:
  - matches/match_info    — from Cricsheet YAML zip (ipl_male.zip)
  - deliveries/ball_by_ball   — from Cricsheet JSON zip (ipl_male_json.zip)
  - batter_scorecard/batter_scorecard — derived from ball_by_ball

Env vars:
  PROCESSED_BUCKET   — S3 bucket name for processed data
"""

import io
import json
import os
import urllib.request
import zipfile
from datetime import datetime, timezone

import boto3
import pandas as pd
import yaml

S3_BUCKET = os.environ["PROCESSED_BUCKET"]
YAML_ZIP_URL = "https://cricsheet.org/downloads/ipl_male.zip"
JSON_ZIP_URL = "https://cricsheet.org/downloads/ipl_male_json.zip"

MATCH_INFO_KEY = "matches/match_info"
MATCH_INFO_CSV_KEY = "csv/match_info"   # separate prefix — keep CSV out of the Parquet table folder
DELIVERIES_KEY = "deliveries/ball_by_ball"
SCORECARD_KEY = "batter_scorecard/batter_scorecard"
RUN_LOG_KEY = "pipeline_runs.log"

MATCH_INFO_COLUMNS = [
    "filename", "season", "match_number", "date", "team1", "team2",
    "city", "venue", "neutral_venue", "toss_winner", "toss_decision",
    "winner", "win_type", "win_margin", "result", "method",
    "eliminator", "player_of_match", "umpire1", "umpire2",
]

MILESTONE_BALLS = [5, 10, 20, 30, 40, 50]

_s3 = None


def get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3")
    return _s3


def read_parquet(key_prefix):
    """Read parquet from S3; return DataFrame or None if key missing."""
    try:
        obj = get_s3().get_object(Bucket=S3_BUCKET, Key=f"{key_prefix}.parquet")
        return pd.read_parquet(io.BytesIO(obj["Body"].read()))
    except get_s3().exceptions.NoSuchKey:
        return None
    except Exception as e:
        print(f"[warn] could not read {key_prefix}.parquet: {e}")
        return None


def write_parquet(df, key_prefix):
    buf = io.BytesIO()
    df.to_parquet(buf, index=False, engine="pyarrow")
    buf.seek(0)
    get_s3().put_object(Bucket=S3_BUCKET, Key=f"{key_prefix}.parquet", Body=buf.getvalue())
    print(f"[s3] wrote {len(df)} rows → {key_prefix}.parquet")


def write_csv(df, key_prefix):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    get_s3().put_object(Bucket=S3_BUCKET, Key=f"{key_prefix}.csv", Body=buf.getvalue())
    print(f"[s3] wrote {len(df)} rows → {key_prefix}.csv")


# ---------------------------------------------------------------------------
# match_info
# ---------------------------------------------------------------------------

def parse_match_yaml(content, filename):
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
        winner = outcome.get("eliminator") or outcome.get("bowl_out")

    return {
        "filename": filename,
        "season": str(info.get("season", "")) or None,
        "match_number": (info.get("event") or {}).get("match_number"),
        "date": str(info["dates"][0]),
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


def update_match_info():
    """
    Returns dict with:
      new_match_ids, new_matches (list of row dicts), yaml_zip_total,
      existing_before, matches_total_after
    """
    existing_df = read_parquet(MATCH_INFO_KEY)
    existing_filenames = set(existing_df["filename"].tolist()) if existing_df is not None else set()
    existing_before = len(existing_filenames)
    print(f"[match_info] existing rows: {existing_before}")

    print("[match_info] downloading YAML zip...")
    with urllib.request.urlopen(YAML_ZIP_URL, timeout=120) as r:
        zip_bytes = r.read()
    print(f"[match_info] downloaded {len(zip_bytes) / 1024 / 1024:.1f} MB")

    new_rows = []
    new_match_ids = []
    yaml_zip_total = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        yaml_files = [n for n in zf.namelist() if n.endswith(".yaml")]
        yaml_zip_total = len(yaml_files)
        print(f"[match_info] total YAML files: {yaml_zip_total}")
        for name in yaml_files:
            filename = os.path.basename(name)
            if filename in existing_filenames:
                continue
            try:
                with zf.open(name) as yf:
                    row = parse_match_yaml(yf.read().decode("utf-8"), filename)
                    new_rows.append(row)
                    new_match_ids.append(int(filename.replace(".yaml", "")))
            except Exception as e:
                print(f"[warn] error parsing {filename}: {e}")

    if not new_rows:
        print("[match_info] nothing new.")
        return {
            "new_match_ids": [],
            "new_matches": [],
            "yaml_zip_total": yaml_zip_total,
            "existing_before": existing_before,
            "matches_total_after": existing_before,
        }

    new_rows.sort(key=lambda r: int(r["filename"].replace(".yaml", "")))
    print(f"[match_info] adding {len(new_rows)} new matches")

    new_df = pd.DataFrame(new_rows, columns=MATCH_INFO_COLUMNS)
    full_df = pd.concat([existing_df, new_df], ignore_index=True) if existing_df is not None else new_df
    write_parquet(full_df, MATCH_INFO_KEY)
    write_csv(full_df, MATCH_INFO_CSV_KEY)

    return {
        "new_match_ids": new_match_ids,
        "new_matches": new_rows,
        "yaml_zip_total": yaml_zip_total,
        "existing_before": existing_before,
        "matches_total_after": len(full_df),
    }


# ---------------------------------------------------------------------------
# ball_by_ball
# ---------------------------------------------------------------------------

def extract_match_json(data, match_id):
    info = data["info"]
    ctx = {
        "match_id": match_id,
        "date": str(info["dates"][0]),
        "venue": info.get("venue", ""),
        "city": info.get("city", ""),
        "team1": info["teams"][0],
        "team2": info["teams"][1],
        "season": str(info.get("season", "")),
    }
    rows = []
    for innings_num, innings in enumerate(data["innings"], start=1):
        batting_team = innings["team"]
        bowling_team = ctx["team2"] if batting_team == ctx["team1"] else ctx["team1"]
        for over_data in innings.get("overs", []):
            over_num = over_data["over"]
            for ball_idx, delivery in enumerate(over_data["deliveries"], start=1):
                runs = delivery["runs"]
                extras = delivery.get("extras", {})
                row = {
                    **ctx,
                    "innings": innings_num,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "over": over_num + 1,
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
                if "wickets" in delivery:
                    row["is_wicket"] = 1
                    w = delivery["wickets"][0]
                    row["player_out"] = w["player_out"]
                    row["dismissal_kind"] = w["kind"]
                    fielders = w.get("fielders", [])
                    row["fielder"] = fielders[0]["name"] if fielders else ""
                    for w2 in delivery["wickets"][1:]:
                        r2 = row.copy()
                        r2["player_out"] = w2["player_out"]
                        r2["dismissal_kind"] = w2["kind"]
                        f2 = w2.get("fielders", [])
                        r2["fielder"] = f2[0]["name"] if f2 else ""
                        rows.append(r2)
                rows.append(row)
    return rows


def update_ball_by_ball(new_match_ids):
    """
    Returns dict with:
      json_zip_total, new_deliveries_added, deliveries_total_after
    """
    if not new_match_ids:
        existing_df = read_parquet(DELIVERIES_KEY)
        return {
            "json_zip_total": 0,
            "new_deliveries_added": 0,
            "deliveries_total_after": len(existing_df) if existing_df is not None else 0,
        }

    existing_df = read_parquet(DELIVERIES_KEY)
    new_ids_set = set(new_match_ids)

    print("[ball_by_ball] downloading JSON zip...")
    with urllib.request.urlopen(JSON_ZIP_URL, timeout=120) as r:
        zip_bytes = r.read()
    print(f"[ball_by_ball] downloaded {len(zip_bytes) / 1024 / 1024:.1f} MB")

    new_rows = []
    json_zip_total = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        json_files = [n for n in zf.namelist() if n.endswith(".json") and "info" not in n]
        json_zip_total = len(json_files)
        for name in json_files:
            try:
                match_id = int(os.path.basename(name).replace(".json", ""))
            except ValueError:
                continue
            if match_id not in new_ids_set:
                continue
            try:
                with zf.open(name) as jf:
                    new_rows.extend(extract_match_json(json.load(jf), match_id))
            except Exception as e:
                print(f"[warn] error parsing {name}: {e}")

    if not new_rows:
        print("[ball_by_ball] nothing new.")
        return {
            "json_zip_total": json_zip_total,
            "new_deliveries_added": 0,
            "deliveries_total_after": len(existing_df) if existing_df is not None else 0,
        }

    new_df = pd.DataFrame(new_rows)
    full_df = pd.concat([existing_df, new_df], ignore_index=True) if existing_df is not None else new_df
    write_parquet(full_df, DELIVERIES_KEY)
    print(f"[ball_by_ball] added {len(new_rows)} new deliveries")

    return {
        "json_zip_total": json_zip_total,
        "new_deliveries_added": len(new_rows),
        "deliveries_total_after": len(full_df),
    }


# ---------------------------------------------------------------------------
# batter_scorecard
# ---------------------------------------------------------------------------

def build_scorecard_for_innings(innings_df):
    innings_df = innings_df.sort_values(["over", "ball"]).reset_index(drop=True)
    team_runs_cum = innings_df["total_runs"].cumsum()
    wickets_cum = innings_df["is_wicket"].cumsum()

    first = innings_df.iloc[0]
    ctx = {
        "match_id": first["match_id"],
        "date": first["date"],
        "venue": first["venue"],
        "city": first["city"],
        "season": str(first["season"]),
        "batting_team": first["batting_team"],
        "bowling_team": first["bowling_team"],
        "innings": first["innings"],
    }

    records = []
    for batter_name, batter_df in innings_df.groupby("batter"):
        balls_mask = batter_df["wides"] == 0
        balls_df = batter_df[balls_mask].reset_index(drop=True)
        if len(balls_df) == 0:
            continue

        first_idx = batter_df.index[0]
        entry_score = 0 if first_idx == 0 else int(team_runs_cum.iloc[first_idx - 1])
        entry_wickets = 0 if first_idx == 0 else int(wickets_cum.iloc[first_idx - 1])

        runs_cum = balls_df["batter_runs"].cumsum()
        milestone_scores = {
            f"runs_after_{m}_balls": int(runs_cum.iloc[m - 1]) if len(runs_cum) >= m else None
            for m in MILESTONE_BALLS
        }

        dismissal_rows = innings_df[innings_df["player_out"] == batter_name]
        if len(dismissal_rows) > 0:
            d = dismissal_rows.iloc[0]
            out, dk, db, df_ = True, d["dismissal_kind"], d["bowler"], d["fielder"]
        else:
            out, dk, db, df_ = False, "", "", ""

        records.append({
            **ctx,
            "batter": batter_name,
            "entry_score": entry_score,
            "entry_wickets": entry_wickets,
            "entry_over": int(batter_df.iloc[0]["over"]),
            "entry_bowler": batter_df.iloc[0]["bowler"],
            **milestone_scores,
            "total_runs": int(batter_df["batter_runs"].sum()),
            "total_balls_faced": int(balls_mask.sum()),
            "out": out,
            "dismissal_kind": dk,
            "dismissal_bowler": db,
            "dismissal_fielder": df_,
        })
    return records


def update_batter_scorecard(new_match_ids):
    """
    Returns dict with:
      new_scorecard_rows_added, scorecard_total_after
    """
    if not new_match_ids:
        existing_sc = read_parquet(SCORECARD_KEY)
        return {
            "new_scorecard_rows_added": 0,
            "scorecard_total_after": len(existing_sc) if existing_sc is not None else 0,
        }

    full_bbb = read_parquet(DELIVERIES_KEY)
    if full_bbb is None:
        print("[scorecard] no ball_by_ball data found, skipping.")
        existing_sc = read_parquet(SCORECARD_KEY)
        return {
            "new_scorecard_rows_added": 0,
            "scorecard_total_after": len(existing_sc) if existing_sc is not None else 0,
        }

    for col in ("player_out", "dismissal_kind", "fielder"):
        full_bbb[col] = full_bbb[col].fillna("").astype(str)
    full_bbb["wides"] = full_bbb["wides"].fillna(0).astype(int)
    full_bbb["season"] = full_bbb["season"].astype(str)

    new_bbb = full_bbb[full_bbb["match_id"].isin(set(new_match_ids))]
    if len(new_bbb) == 0:
        print("[scorecard] no new deliveries found for new match_ids.")
        existing_sc = read_parquet(SCORECARD_KEY)
        return {
            "new_scorecard_rows_added": 0,
            "scorecard_total_after": len(existing_sc) if existing_sc is not None else 0,
        }

    all_records = []
    for (_, _innings), innings_df in new_bbb.groupby(["match_id", "innings"]):
        all_records.extend(build_scorecard_for_innings(innings_df))

    if not all_records:
        existing_sc = read_parquet(SCORECARD_KEY)
        return {
            "new_scorecard_rows_added": 0,
            "scorecard_total_after": len(existing_sc) if existing_sc is not None else 0,
        }

    new_sc = pd.DataFrame(all_records)
    existing_sc = read_parquet(SCORECARD_KEY)
    full_sc = pd.concat([existing_sc, new_sc], ignore_index=True) if existing_sc is not None else new_sc
    write_parquet(full_sc, SCORECARD_KEY)
    print(f"[scorecard] added {len(all_records)} new rows")

    return {
        "new_scorecard_rows_added": len(all_records),
        "scorecard_total_after": len(full_sc),
    }


# ---------------------------------------------------------------------------
# run log
# ---------------------------------------------------------------------------

def format_run_log_entry(summary):
    lines = []
    lines.append("=" * 80)
    lines.append(f"RUN: {summary['run_at']}")
    lines.append("=" * 80)

    yaml_total = summary.get("yaml_zip_total", 0)
    json_total = summary.get("json_zip_total", 0)
    if yaml_total or json_total:
        lines.append(f"Zip sizes:   YAML {yaml_total} files  |  JSON {json_total} files")

    lines.append(f"Existing matches before run: {summary['existing_matches_before']}")
    lines.append("")

    new_matches = summary.get("new_matches", [])
    if new_matches:
        lines.append(f"NEW MATCHES ({len(new_matches)}):")
        for m in new_matches:
            venue = m.get("venue") or ""
            lines.append(
                f"  {m['filename']}  {m['date']}  {m['team1']} vs {m['team2']}  @  {venue}"
            )
            winner = m.get("winner") or "no result"
            win_type = m.get("win_type") or ""
            win_margin = m.get("win_margin")
            pom = m.get("player_of_match") or "—"
            if win_type and win_margin is not None:
                result_str = f"Winner: {winner} by {int(win_margin)} {win_type}"
            else:
                result_str = f"Result: {winner}"
            lines.append(f"    {result_str}  |  POM: {pom}")
    else:
        lines.append("NEW MATCHES: none")

    lines.append("")
    lines.append(
        f"DELIVERIES: +{summary['new_deliveries_added']} rows"
        f"  (total: {summary['deliveries_total_after']:,})"
    )
    lines.append(
        f"SCORECARD:  +{summary['new_scorecard_rows_added']} rows"
        f"   (total: {summary['scorecard_total_after']:,})"
    )

    errors = summary.get("errors", [])
    lines.append(f"ERRORS: {', '.join(errors) if errors else 'none'}")
    lines.append("-" * 80)
    lines.append("")
    return "\n".join(lines)


def write_run_log(summary):
    new_entry = format_run_log_entry(summary)

    # Read existing log (if any)
    existing_content = ""
    try:
        obj = get_s3().get_object(Bucket=S3_BUCKET, Key=RUN_LOG_KEY)
        existing_content = obj["Body"].read().decode("utf-8")
    except Exception:
        pass  # first run, or key doesn't exist yet

    combined = new_entry + existing_content
    get_s3().put_object(
        Bucket=S3_BUCKET,
        Key=RUN_LOG_KEY,
        Body=combined.encode("utf-8"),
        ContentType="text/plain",
    )
    print(f"[run_log] written to s3://{S3_BUCKET}/{RUN_LOG_KEY}")


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def handler(event, context):
    print("[ingestion] starting daily IPL data update")
    run_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    errors = []

    match_result = update_match_info()
    new_match_ids = match_result["new_match_ids"]

    bbb_result = {"json_zip_total": 0, "new_deliveries_added": 0, "deliveries_total_after": 0}
    sc_result = {"new_scorecard_rows_added": 0, "scorecard_total_after": 0}

    if new_match_ids:
        bbb_result = update_ball_by_ball(new_match_ids)
        sc_result = update_batter_scorecard(new_match_ids)
    else:
        print("[ingestion] no new matches — nothing else to do")
        # still need totals for the log
        existing_bbb = read_parquet(DELIVERIES_KEY)
        existing_sc = read_parquet(SCORECARD_KEY)
        bbb_result["deliveries_total_after"] = len(existing_bbb) if existing_bbb is not None else 0
        sc_result["scorecard_total_after"] = len(existing_sc) if existing_sc is not None else 0

    summary = {
        "run_at": run_at,
        "yaml_zip_total": match_result["yaml_zip_total"],
        "json_zip_total": bbb_result["json_zip_total"],
        "existing_matches_before": match_result["existing_before"],
        "new_match_count": len(new_match_ids),
        "new_matches": match_result["new_matches"],
        "new_deliveries_added": bbb_result["new_deliveries_added"],
        "new_scorecard_rows_added": sc_result["new_scorecard_rows_added"],
        "matches_total_after": match_result["matches_total_after"],
        "deliveries_total_after": bbb_result["deliveries_total_after"],
        "scorecard_total_after": sc_result["scorecard_total_after"],
        "errors": errors,
    }

    try:
        write_run_log(summary)
    except Exception as e:
        print(f"[warn] failed to write run log: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "new_matches_added": len(new_match_ids),
            "new_deliveries_added": bbb_result["new_deliveries_added"],
            "new_scorecard_rows_added": sc_result["new_scorecard_rows_added"],
        }),
    }
