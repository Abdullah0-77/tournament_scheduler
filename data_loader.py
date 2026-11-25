import json
from pathlib import Path
import pandas as pd

CSV_FILES = [
    "teams", "matches", "venues", "time_slots",
    "team_availability", "venue_availability", "preferences",
]


def load_dataset(folder="dataset"):
    folder = Path(folder)
    data = {}

    for name in CSV_FILES:
        data[name] = pd.read_csv(folder / f"{name}.csv")

    with open(folder / "config.json", encoding="utf-8") as f:
        data["config"] = json.load(f)

    reference = folder / "feasible_schedule.csv"
    data["feasible_schedule"] = pd.read_csv(reference) if reference.exists() else None

    validate_dataset(data)
    return data


def validate_dataset(data):
    teams = data["teams"]
    matches = data["matches"]

    # 1. Missing values
    for name in CSV_FILES:
        if data[name].isnull().any().any():
            raise ValueError(f"Missing values found in {name}.csv")

    # 2. Duplicate IDs
    if teams["team_id"].duplicated().any():
        raise ValueError("Duplicate team IDs found.")
    if matches["match_id"].duplicated().any():
        raise ValueError("Duplicate match IDs found.")
    if data["venues"]["venue_id"].duplicated().any():
        raise ValueError("Duplicate venue IDs found.")
    if data["time_slots"]["slot_id"].duplicated().any():
        raise ValueError("Duplicate slot IDs found.")

    # 3. Matches must refer to existing teams
    team_ids = set(teams["team_id"])
    used_ids = set(matches["team_a"]) | set(matches["team_b"])
    if not used_ids <= team_ids:
        raise ValueError(f"Matches refer to unknown teams: {used_ids - team_ids}")

    # 4. Single Round Robin: n(n-1)/2 matches, every pair exactly once
    n = len(teams)
    if len(matches) != n * (n - 1) // 2:
        raise ValueError("Number of matches is not n(n-1)/2.")

    pairs = {frozenset(p) for p in zip(matches["team_a"], matches["team_b"])}
    if len(pairs) != len(matches):
        raise ValueError("Some team pairings are repeated.")
