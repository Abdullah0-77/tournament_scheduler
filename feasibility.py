from collections import Counter, defaultdict
from datetime import timedelta
from problem_model import get_match_times


def validate_schedule(schedule, problem):
    violations = []

    expected = {m["match_id"] for m in problem["matches"]}
    counts = Counter(m["match_id"] for m in schedule)

    # 1. Missing / duplicated / unknown matches
    for match_id in expected:
        if counts[match_id] == 0:
            violations.append({"type": "missing_match", "match_id": match_id})
        elif counts[match_id] > 1:
            violations.append({"type": "duplicate_match", "match_id": match_id})
    for match_id in counts:
        if match_id not in expected:
            violations.append({"type": "unknown_match", "match_id": match_id})

    team_games = defaultdict(list)    # team_id  -> [(start, end, match_id)]
    venue_games = defaultdict(list)   # venue_id -> [(start, end, match_id)]

    for m in schedule:
        start, end = get_match_times(m, problem)
        date, slot, venue = str(m["date"]), m["slot_id"], m["venue_id"]

        # 2. Availability
        for team in (m["team_a"], m["team_b"]):
            if not problem["team_availability"].get((team, date, slot), False):
                violations.append({"type": "team_unavailable",
                                   "match_id": m["match_id"], "team": team})
            team_games[team].append((start, end, m["match_id"]))

        if not problem["venue_availability"].get((venue, date, slot), False):
            violations.append({"type": "venue_unavailable",
                               "match_id": m["match_id"], "venue": venue})
        venue_games[venue].append((start, end, m["match_id"]))

    # 3. Team overlap + minimum rest
    for team, games in team_games.items():
        games.sort()
        min_rest = timedelta(hours=problem["team_rest"][team])
        for prev, nxt in zip(games, games[1:]):
            gap = nxt[0] - prev[1]          # next start - previous end
            if gap < timedelta(0):
                violations.append({"type": "team_overlap", "team": team,
                                   "matches": [prev[2], nxt[2]]})
            elif gap < min_rest:
                violations.append({"type": "rest_violation", "team": team,
                                   "matches": [prev[2], nxt[2]],
                                   "rest_hours": gap.total_seconds() / 3600})

    # 4. Venue overlap
    for venue, games in venue_games.items():
        games.sort()
        for prev, nxt in zip(games, games[1:]):
            if nxt[0] < prev[1]:
                violations.append({"type": "venue_overlap", "venue": venue,
                                   "matches": [prev[2], nxt[2]]})

    return {"feasible": len(violations) == 0, "violations": violations}


def print_validation_report(report, max_lines=10):
    if report["feasible"]:
        print("Schedule is FEASIBLE. No hard-constraint violations.")
        return

    violations = report["violations"]
    print(f"Schedule is NOT feasible. {len(violations)} violations found.")
    for v in violations[:max_lines]:
        print("  -", v)
    if len(violations) > max_lines:
        print(f"  ... and {len(violations) - max_lines} more.")
