import copy
from data_loader import load_dataset
from problem_model import build_problem
from feasibility import validate_schedule
from greedy_baseline import generate_greedy_schedule, preference_cost
from local_search import move_match, swap_matches, local_search


def temp_preference_fitness(schedule, problem):
    total_cost = 0.0
    for match in schedule:
        total_cost += preference_cost(match, match["slot_id"], match["venue_id"], problem)
    return total_cost


def run_tests():
    print("Loading project dataset...")
    data = load_dataset("dataset")
    problem = build_problem(data)

    base_schedule = generate_greedy_schedule(problem)
    assert base_schedule is not None, "Greedy solver failed to produce a baseline schedule."
    assert validate_schedule(base_schedule, problem)["feasible"], "Baseline schedule is not feasible."

    res = local_search(base_schedule, problem, temp_preference_fitness, max_iterations=20)
    assert isinstance(res, list) and len(res) == len(base_schedule), "Output schedule structure mismatch."
    print("[PASS] Test 1 & 2: Valid schedule in GA structure accepted.")

    snapshot = copy.deepcopy(base_schedule)
    _ = move_match(base_schedule, problem)
    assert base_schedule == snapshot, "move_match mutated the original schedule!"
    print("[PASS] Test 3: move_match preserved the original schedule.")

    swapped = swap_matches(base_schedule)
    for orig, swp in zip(base_schedule, swapped):
        assert orig["match_id"] == swp["match_id"], "match_id was modified!"
        assert orig["team_a"] == swp["team_a"], "team_a was modified!"
        assert orig["team_b"] == swp["team_b"], "team_b was modified!"
        assert orig["round"] == swp["round"], "round was modified!"
    print("[PASS] Test 4: swap_matches preserved match and team metadata.")

    always_invalid = lambda sched, prob: False
    unchanged = local_search(
        base_schedule,
        problem,
        temp_preference_fitness,
        max_iterations=50,
        feasibility_fn=always_invalid
    )
    assert unchanged == base_schedule, "An infeasible neighbor was accepted!"
    print("[PASS] Test 5: Infeasible neighbors were properly rejected.")

    initial_fit = temp_preference_fitness(base_schedule, problem)
    best_schedule = local_search(
        base_schedule,
        problem,
        temp_preference_fitness,
        max_iterations=500,
        minimize=True
    )
    final_fit = temp_preference_fitness(best_schedule, problem)

    assert final_fit <= initial_fit, "Fitness worsened instead of improving!"
    assert validate_schedule(best_schedule, problem)["feasible"], "Final schedule violated hard constraints!"
    print(f"[PASS] Test 6 & 7: Optimization succeeded (Preference cost: {initial_fit} -> {final_fit}).")


if __name__ == "__main__":
    run_tests()