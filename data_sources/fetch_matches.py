"""
Fetch IPL 2026 match data from CricAPI, clean it, and save as CSV.
Run manually: python3 data_sources/fetch_matches.py
"""

import csv
import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone

API_URL = (
    "https://api.cricapi.com/v1/series_info"
    "?apikey=b6d24a6c-2569-483b-b017-05871d8b8a4e"
    "&id=87c62aac-bc3c-4738-ab93-19da0690488f"
)
OUTPUT_CSV = "data_sources/ipl_2026_matches.csv"
IST = timezone(timedelta(hours=5, minutes=30))


def fetch_data():
    with urllib.request.urlopen(API_URL, timeout=30) as resp:
        return json.loads(resp.read().decode())


def parse_match_number(name):
    """Extract integer match number from name like '31st Match'."""
    m = re.search(r"(\d+)(?:st|nd|rd|th)\s+Match", name)
    return int(m.group(1)) if m else None


def parse_venue(venue):
    """Split 'Stadium, City' into (stadium, city)."""
    parts = venue.rsplit(", ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return venue, ""


def parse_result(status, match_ended):
    """Return result string for completed matches, empty otherwise."""
    if match_ended:
        return status
    return ""


def to_ist(datetime_gmt_str):
    """Convert GMT datetime string to IST."""
    if not datetime_gmt_str:
        return ""
    dt = datetime.fromisoformat(datetime_gmt_str).replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M")


def day_of_week(date_str):
    if not date_str:
        return ""
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")


def transform(raw):
    matches = raw["data"]["matchList"]
    rows = []

    for m in matches:
        teams = m.get("teams", [])
        team1 = teams[0] if len(teams) > 0 else ""
        team2 = teams[1] if len(teams) > 1 else ""

        team_info = {ti["name"]: ti for ti in m.get("teamInfo", [])}
        team1_short = team_info.get(team1, {}).get("shortname", "")
        team2_short = team_info.get(team2, {}).get("shortname", "")

        match_ended = m.get("matchEnded", False)
        match_started = m.get("matchStarted", False)
        stadium, city = parse_venue(m.get("venue", ""))

        rows.append({
            "match_id": m.get("id", ""),
            "match_number": parse_match_number(m.get("name", "")),
            "date": m.get("date", ""),
            "datetime_gmt": m.get("dateTimeGMT", ""),
            "datetime_ist": to_ist(m.get("dateTimeGMT", "")),
            "day_of_week": day_of_week(m.get("date", "")),
            "team1": team1,
            "team1_short": team1_short,
            "team2": team2,
            "team2_short": team2_short,
            "stadium": stadium,
            "city": city,
            "match_type": m.get("matchType", ""),
            "match_started": match_started,
            "match_ended": match_ended,
            "is_completed": match_started and match_ended,
            "result": parse_result(m.get("status", ""), match_ended),
            "has_squad": m.get("hasSquad", False),
        })

    rows.sort(key=lambda r: (r["date"], r["datetime_gmt"]))
    return rows


def write_csv(rows):
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("Fetching IPL 2026 data from CricAPI...")
    raw = fetch_data()
    status = raw.get("status", "")
    if status != "success":
        print(f"API returned status: {status}")
        return

    rows = transform(raw)
    write_csv(rows)
    completed = sum(1 for r in rows if r["is_completed"])
    print(f"Saved {len(rows)} matches ({completed} completed) → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
