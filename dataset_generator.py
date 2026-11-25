import json
from datetime import date, timedelta
from pathlib import Path
import pandas as pd


def generate_instance(output_folder="generated_dataset", num_teams=8, num_venues=6,
                      num_slots=4, num_days=33, start_date="2027-01-01",
                      minimum_rest_hours=24, match_duration_minutes=90):
    if num_teams < 2 or num_teams % 2 != 0:
        raise ValueError("num_teams must be an even number.")

    folder = Path(output_folder)
    folder.mkdir(parents=True, exist_ok=True)

    team_ids = [f"T{i+1:02d}" for i in range(num_teams)]
    venue_ids = [f"V{i+1:02d}" for i in range(num_venues)]
    slot_ids = [f"S{i+1}" for i in range(num_slots)]
    first = date.fromisoformat(start_date)
    dates = [(first + timedelta(days=d)).isoformat() for d in range(num_days)]

    # Matches: all unique pairs (Single Round Robin), round filled by Circle Method
    rotating = team_ids[1:]
    matches = []
    for round_no in range(1, num_teams):
        order = [team_ids[0]] + rotating
        for i in range(num_teams // 2):
            matches.append({"match_id": f"M{len(matches)+1:03d}", "round": round_no,
                            "team_a": order[i], "team_b": order[num_teams - 1 - i]})
        rotating = [rotating[-1]] + rotating[:-1]

    pd.DataFrame({"team_id": team_ids,
                  "team_name": [f"Team_{i+1:02d}" for i in range(num_teams)],
                  "minimum_rest_hours": minimum_rest_hours}
                 ).to_csv(folder / "teams.csv", index=False)
    pd.DataFrame(matches).to_csv(folder / "matches.csv", index=False)
    pd.DataFrame({"venue_id": venue_ids,
                  "venue_name": [f"Venue_{i+1:02d}" for i in range(num_venues)],
                  "capacity": 3000}).to_csv(folder / "venues.csv", index=False)
    pd.DataFrame([{"slot_id": s, "slot_number": i + 1,
                   "start_time": f"{8 + 3 * i:02d}:00",
                   "duration_minutes": match_duration_minutes}
                  for i, s in enumerate(slot_ids)]
                 ).to_csv(folder / "time_slots.csv", index=False)

    # Everyone and every venue is available all the time
    pd.DataFrame([{"team_id": t, "date": d, "slot_id": s, "is_available": 1}
                  for t in team_ids for d in dates for s in slot_ids]
                 ).to_csv(folder / "team_availability.csv", index=False)
    pd.DataFrame([{"venue_id": v, "date": d, "slot_id": s, "is_available": 1}
                  for v in venue_ids for d in dates for s in slot_ids]
                 ).to_csv(folder / "venue_availability.csv", index=False)

    pd.DataFrame([{"team_id": t, "preferred_slot": slot_ids[0],
                   "preferred_venue": venue_ids[0], "preference_weight": 1.0}
                  for t in team_ids]).to_csv(folder / "preferences.csv", index=False)

    config = {"tournament_format": "single_round_robin", "num_teams": num_teams,
              "num_venues": num_venues, "num_slots_per_day": num_slots,
              "num_matches": len(matches), "num_rounds": num_teams - 1,
              "calendar_span_days": num_days,
              "minimum_rest_hours": minimum_rest_hours,
              "match_duration_minutes": match_duration_minutes}
    with open(folder / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"Generated {num_teams} teams, {len(matches)} matches in '{folder}'.")
