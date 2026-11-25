from problem_model import generate_rounds, create_match_dictionary


def get_candidate_resources(match, date, problem):
    """All (slot_id, venue_id) available for this match on this date."""
    candidates = []
    for slot in problem["slots"]:
        slot_id = slot["slot_id"]

        if not problem["team_availability"].get((match["team_a"], date, slot_id), False):
            continue
        if not problem["team_availability"].get((match["team_b"], date, slot_id), False):
            continue

        for venue in problem["venues"]:
            venue_id = venue["venue_id"]
            if problem["venue_availability"].get((venue_id, date, slot_id), False):
                candidates.append((slot_id, venue_id))
    return candidates


def preference_cost(match, slot_id, venue_id, problem):
    """Local heuristic only (NOT the team's fitness function)."""
    cost = 0
    for team in (match["team_a"], match["team_b"]):
        pref = problem["preferences"].get(team)
        if not pref:
            continue
        weight = pref.get("preference_weight", 1)
        if pref.get("preferred_slot") != slot_id:
            cost += weight
        if pref.get("preferred_venue") != venue_id:
            cost += weight
    return cost


def assign_round_to_date(round_matches, date, problem):
    """Backtracking: give every match in the round its own (slot, venue)."""
    options = {}
    for m in round_matches:
        found = get_candidate_resources(m, date, problem)
        found.sort(key=lambda c: preference_cost(m, c[0], c[1], problem))
        options[m["match_id"]] = found

    # Most constrained match first
    ordered = sorted(round_matches, key=lambda m: len(options[m["match_id"]]))

    used = set()      # (slot_id, venue_id) already taken on this date
    chosen = []       # (match, slot_id, venue_id)

    def search(i):
        if i == len(ordered):
            return True
        m = ordered[i]
        for slot_id, venue_id in options[m["match_id"]]:
            if (slot_id, venue_id) in used:
                continue
            used.add((slot_id, venue_id))
            chosen.append((m, slot_id, venue_id))
            if search(i + 1):
                return True
            used.remove((slot_id, venue_id))
            chosen.pop()
        return False

    return chosen if search(0) else None


def generate_greedy_schedule(problem):
    rounds = generate_rounds(problem)
    dates = problem["dates"]
    schedule = []
    date_index = 0

    for round_no, round_matches in enumerate(rounds, start=1):
        assigned = None
        while date_index < len(dates) and assigned is None:
            assigned = assign_round_to_date(round_matches, dates[date_index], problem)
            if assigned is None:
                date_index += 1        # this date doesn't work, try the next one

        if assigned is None:
            print(f"Greedy failed at round {round_no}.")
            return None

        for m, slot_id, venue_id in assigned:
            schedule.append(create_match_dictionary(
                m, round_no, dates[date_index], slot_id, venue_id))
        date_index += 2                # keep a 2-day gap -> always >= 24h rest

    return schedule
