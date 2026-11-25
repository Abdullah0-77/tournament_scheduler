import pandas as pd
from datetime import timedelta


def build_problem(data):
    """Convert the DataFrames into plain Python structures."""
    config = data["config"]
    default_rest = config.get("minimum_rest_hours", 24)

    problem = {
        "teams": data["teams"].to_dict("records"),
        "matches": data["matches"].to_dict("records"),
        "venues": data["venues"].to_dict("records"),
        "slots": data["time_slots"].to_dict("records"),
        "dates": sorted(data["team_availability"]["date"].astype(str).unique()),
        "config": config,
    }

    # Minimum rest for each team (team column, else config default)
    problem["team_rest"] = {
        t["team_id"]: t.get("minimum_rest_hours", default_rest) for t in problem["teams"]
    }

    # Availability: (id, date, slot_id) -> True/False
    problem["team_availability"] = {
        (r.team_id, str(r.date), r.slot_id): bool(r.is_available)
        for r in data["team_availability"].itertuples()
    }
    problem["venue_availability"] = {
        (r.venue_id, str(r.date), r.slot_id): bool(r.is_available)
        for r in data["venue_availability"].itertuples()
    }

    # Preferences: team_id -> row (preferred_slot, preferred_venue, preference_weight)
    problem["preferences"] = {
        r["team_id"]: r for r in data["preferences"].to_dict("records")
    }

    # Slot details: slot_id -> slot row (start_time, duration_minutes)
    problem["slot_details"] = {s["slot_id"]: s for s in problem["slots"]}

    return problem


def generate_rounds(problem):
    """Circle Method: n-1 rounds, each team plays once per round."""
    team_ids = [t["team_id"] for t in problem["teams"]]
    n = len(team_ids)

    # (team_a, team_b) in any order -> the original match dictionary
    lookup = {frozenset((m["team_a"], m["team_b"])): m for m in problem["matches"]}

    fixed = team_ids[0]
    rotating = team_ids[1:]
    rounds = []

    for _ in range(n - 1):
        order = [fixed] + rotating
        pairs = [(order[i], order[n - 1 - i]) for i in range(n // 2)]
        rounds.append([lookup[frozenset(p)] for p in pairs])
        rotating = [rotating[-1]] + rotating[:-1]   # rotate

    return rounds


def create_match_dictionary(match, round_no, date, slot_id, venue_id):
    """One scheduled match = one dictionary (this is the chromosome gene)."""
    return {
        "match_id": match["match_id"],
        "team_a": match["team_a"],
        "team_b": match["team_b"],
        "round": round_no,
        "date": date,
        "slot_id": slot_id,
        "venue_id": venue_id,
    }


def get_match_times(entry, problem):
    """Return (start, end) datetime of a scheduled match."""
    slot = problem["slot_details"][entry["slot_id"]]
    start = pd.to_datetime(f"{entry['date']} {slot['start_time']}")
    minutes = slot.get("duration_minutes", problem["config"].get("match_duration_minutes", 90))
    return start, start + timedelta(minutes=int(minutes))
