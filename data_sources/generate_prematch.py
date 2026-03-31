"""
Generate pre-match analysis JSON for today's IPL matches.
Reads schedule (ipl_2026_matches.csv) + history (match_info.csv), outputs frontend/public/prematch.json.

Run after fetch_matches.py and update_match_info.py:
  python3 data_sources/generate_prematch.py
"""

import csv
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

SCHEDULE_CSV = "data_sources/ipl_2026_matches.csv"
HISTORY_CSV = "data_modeling/match_info.csv"
OUTPUT_JSON = "frontend/public/prematch.json"

IST = timezone(timedelta(hours=5, minutes=30))

# Teams that renamed but are the same franchise
TEAM_ALIASES = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
}

CITY_ALIASES = {
    "Mohali": "Chandigarh",
    "New Chandigarh": "Chandigarh",
    "Bangalore": "Bengaluru",
    "Navi Mumbai": "Mumbai",
}


def normalize_team(name):
    return TEAM_ALIASES.get(name, name)


def normalize_city(city):
    return CITY_ALIASES.get(city, city)


def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def get_todays_matches(schedule):
    today = datetime.now(IST).strftime("%Y-%m-%d")
    matches = [m for m in schedule if m["date"] == today and m["is_completed"] == "False"]
    matches.sort(key=lambda m: m["datetime_gmt"])
    return today, matches


def head_to_head(history, team1, team2):
    """All-time head-to-head between two franchises (accounting for renames)."""
    matches = []
    for m in history:
        t1 = normalize_team(m["team1"])
        t2 = normalize_team(m["team2"])
        if {t1, t2} == {team1, team2}:
            matches.append(m)

    total = len(matches)
    wins = Counter()
    for m in matches:
        w = normalize_team(m["winner"]) if m["winner"] else None
        if w:
            wins[w] += 1

    no_result = total - wins[team1] - wins[team2]

    # Last 5 encounters
    matches.sort(key=lambda m: m["date"], reverse=True)
    last_5 = []
    for m in matches[:5]:
        w = normalize_team(m["winner"]) if m["winner"] else None
        margin = ""
        if m["win_margin"] and m["win_type"]:
            margin = f" by {m['win_margin'].rstrip('.0')} {m['win_type']}"
            # Clean up "140.0" → "140"
            try:
                margin = f" by {int(float(m['win_margin']))} {m['win_type']}"
            except (ValueError, TypeError):
                pass
        last_5.append({
            "date": m["date"],
            "winner": w,
            "margin": margin.strip(),
            "city": m.get("city", ""),
        })

    return {
        "total": total,
        "team1_wins": wins.get(team1, 0),
        "team2_wins": wins.get(team2, 0),
        "no_results": no_result,
        "last_5_encounters": last_5,
    }


def venue_record(history, team, city):
    """Team's record in a city (normalized)."""
    norm_city = normalize_city(city)
    played = 0
    won = 0
    for m in history:
        mc = normalize_city(m.get("city", ""))
        t1 = normalize_team(m["team1"])
        t2 = normalize_team(m["team2"])
        if mc == norm_city and team in (t1, t2):
            played += 1
            w = normalize_team(m["winner"]) if m["winner"] else None
            if w == team:
                won += 1
    return {"played": played, "won": won}


def toss_analysis(history, city):
    """Toss stats at a venue city."""
    norm_city = normalize_city(city)
    total = 0
    field_first = 0
    toss_winner_won_match = 0
    bat_first_won = 0
    field_first_won = 0

    for m in history:
        mc = normalize_city(m.get("city", ""))
        if mc != norm_city:
            continue
        total += 1
        decision = m.get("toss_decision", "")
        if decision == "field":
            field_first += 1

        winner = m.get("winner")
        toss_winner = m.get("toss_winner")
        if winner and toss_winner and normalize_team(winner) == normalize_team(toss_winner):
            toss_winner_won_match += 1

        # Who wins more — batting first or fielding first?
        if winner and decision:
            batting_first = m["team1"] if decision == "bat" else m["team2"]
            if decision == "bat":
                batting_first = normalize_team(m.get("toss_winner", ""))
            else:
                # toss winner chose to field, so the other team bats first
                t1 = normalize_team(m["team1"])
                t2 = normalize_team(m["team2"])
                tw = normalize_team(m.get("toss_winner", ""))
                batting_first = t1 if tw == t2 else t2

            if normalize_team(winner) == batting_first:
                bat_first_won += 1
            else:
                field_first_won += 1

    return {
        "total_matches": total,
        "chose_field_pct": round(field_first / total * 100) if total else 0,
        "toss_winner_won_pct": round(toss_winner_won_match / total * 100) if total else 0,
        "bat_first_won": bat_first_won,
        "field_first_won": field_first_won,
    }


def recent_form(history, team, n=5):
    """Last n completed matches for a team."""
    matches = []
    for m in history:
        t1 = normalize_team(m["team1"])
        t2 = normalize_team(m["team2"])
        if team in (t1, t2) and m.get("winner"):
            w = normalize_team(m["winner"])
            opponent = t2 if t1 == team else t1
            matches.append({
                "date": m["date"],
                "opponent": opponent,
                "result": "W" if w == team else "L",
            })
    matches.sort(key=lambda m: m["date"], reverse=True)
    return matches[:n]


def build_analysis(schedule_match, history):
    team1 = schedule_match["team1"]
    team2 = schedule_match["team2"]
    city = schedule_match["city"]

    h2h = head_to_head(history, team1, team2)
    t1_venue = venue_record(history, team1, city)
    t2_venue = venue_record(history, team2, city)
    toss = toss_analysis(history, city)
    t1_form = recent_form(history, team1)
    t2_form = recent_form(history, team2)

    return {
        "head_to_head": h2h,
        "team1_venue_record": t1_venue,
        "team2_venue_record": t2_venue,
        "toss_at_venue": toss,
        "team1_recent_form": t1_form,
        "team2_recent_form": t2_form,
    }


def main():
    schedule = load_csv(SCHEDULE_CSV)
    history = load_csv(HISTORY_CSV)

    today, todays_matches = get_todays_matches(schedule)

    if not todays_matches:
        print(f"No upcoming matches on {today}.")
        # Still write empty JSON so frontend doesn't break
        output = {"generated_at": datetime.now(IST).isoformat(), "date": today, "matches": []}
        with open(OUTPUT_JSON, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Wrote empty {OUTPUT_JSON}")
        return

    match_data = []
    for m in todays_matches:
        time_ist = m["datetime_ist"].split(" ")[1] if " " in m["datetime_ist"] else ""
        entry = {
            "match_number": int(m["match_number"]) if m["match_number"] else None,
            "date": m["date"],
            "time_ist": time_ist,
            "team1": m["team1"],
            "team1_short": m["team1_short"],
            "team2": m["team2"],
            "team2_short": m["team2_short"],
            "stadium": m["stadium"],
            "city": m["city"],
            "analysis": build_analysis(m, history),
        }
        match_data.append(entry)

    output = {
        "generated_at": datetime.now(IST).isoformat(),
        "date": today,
        "matches": match_data,
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(output, f, indent=2)

    for m in match_data:
        h2h = m["analysis"]["head_to_head"]
        print(f"  Match {m['match_number']}: {m['team1_short']} vs {m['team2_short']} — "
              f"H2H: {h2h['total']} played, {h2h['team1_wins']}-{h2h['team2_wins']}")

    print(f"Wrote {len(match_data)} match(es) to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
