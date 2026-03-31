"""
Generate home ground mapping for IPL teams by season.
Outputs data_sources/home_grounds.json.

Logic:
- For each team in each season, count matches per city (team1 or team2).
- Top city = primary home, second city = secondary home (if ≥2 matches there).
- Skip fully overseas/neutral seasons: 2009 (South Africa), 2020 (UAE), 2021 (India bubble), 2022 (Mumbai/Pune bubble).
- For 2026, use the full schedule (not just completed matches).

Run: python3 data_sources/generate_home_grounds.py
"""

import csv
import json
import os
from collections import Counter
from datetime import datetime

HISTORY_CSV = "data_modeling/match_info.csv"
SCHEDULE_CSV = "data_sources/ipl_2026_matches.csv"
OUTPUT_JSON = "data_sources/home_grounds.json"

OVERSEAS_CITIES = {
    "Abu Dhabi", "Dubai", "Sharjah",
    "Cape Town", "Centurion", "Durban", "Johannesburg",
    "Bloemfontein", "East London", "Kimberley", "Port Elizabeth",
}

# Seasons to skip entirely — no meaningful home ground data
SKIP_YEARS = {
    2009,  # Entire season in South Africa
    2020,  # Entire season in UAE
    2021,  # Split: India bubble (neutral venues) + UAE
    2022,  # All matches in Mumbai/Pune — not home grounds
}

TEAM_ALIASES = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
}

CITY_ALIASES = {
    "Mohali": "Chandigarh",
    "New Chandigarh": "Chandigarh",
    "Bangalore": "Bengaluru",
    "Navi Mumbai": "Mumbai",
}


def normalize_city(city):
    return CITY_ALIASES.get(city, city)


def normalize_team(name):
    return TEAM_ALIASES.get(name, name)


def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def compute_home_grounds(rows, year):
    """Given match rows for a year, return {team: {primary, secondary}} mapping."""
    teams = set()
    team_city_counts = {}

    for m in rows:
        city = m.get("city", "")
        if not city or city in OVERSEAS_CITIES:
            continue
        city = normalize_city(city)

        for field in ("team1", "team2"):
            team = normalize_team(m[field])
            teams.add(team)
            if team not in team_city_counts:
                team_city_counts[team] = Counter()
            team_city_counts[team][city] += 1

    result = {}
    for team in sorted(teams):
        counts = team_city_counts.get(team, Counter())
        top = counts.most_common(3)
        entry = {"primary": None, "secondary": None}
        if len(top) >= 1:
            entry["primary"] = {"city": top[0][0], "matches": top[0][1]}
        if len(top) >= 2 and top[1][1] >= 2:
            entry["secondary"] = {"city": top[1][0], "matches": top[1][1]}
        result[team] = entry

    return result


def main():
    history = load_csv(HISTORY_CSV)
    schedule = load_csv(SCHEDULE_CSV)

    # Group history by year
    by_year = {}
    for m in history:
        year = int(m["date"][:4])
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(m)

    output = {}

    for year in sorted(by_year.keys()):
        if year in SKIP_YEARS:
            continue
        if year == 2026:
            # Use full schedule instead of just completed matches
            grounds = compute_home_grounds(schedule, year)
        else:
            grounds = compute_home_grounds(by_year[year], year)
        output[str(year)] = grounds

    # Add 2026 from schedule if not already in history
    if "2026" not in output:
        output["2026"] = compute_home_grounds(schedule, 2026)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    # Print summary
    for year in sorted(output.keys(), key=int):
        print(f"\n{year}:")
        for team, grounds in sorted(output[year].items()):
            primary = grounds["primary"]
            secondary = grounds["secondary"]
            line = f"  {team}: {primary['city']} ({primary['matches']})"
            if secondary:
                line += f" | {secondary['city']} ({secondary['matches']})"
            print(line)

    print(f"\nWrote {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
