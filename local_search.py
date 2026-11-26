import copy
import random
from typing import List, Dict, Callable, Any, Optional
from feasibility import validate_schedule


def is_feasible(schedule: List[Dict[str, Any]], problem: Dict[str, Any]) -> bool:
    return validate_schedule(schedule, problem)["feasible"]


def move_match(schedule: List[Dict[str, Any]], problem: Dict[str, Any]) -> List[Dict[str, Any]]:
    new_schedule = copy.deepcopy(schedule)
    if not new_schedule:
        return new_schedule

    match = random.choice(new_schedule)

    dates = problem["dates"]
    slot_ids = [s["slot_id"] for s in problem["slots"]]
    venue_ids = [v["venue_id"] for v in problem["venues"]]

    move_type = random.choice(["date", "slot", "venue", "combo"])

    if move_type in ("date", "combo") and dates:
        match["date"] = random.choice(dates)
    if move_type in ("slot", "combo") and slot_ids:
        match["slot_id"] = random.choice(slot_ids)
    if move_type in ("venue", "combo") and venue_ids:
        match["venue_id"] = random.choice(venue_ids)

    return new_schedule


def swap_matches(schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    new_schedule = copy.deepcopy(schedule)
    if len(new_schedule) < 2:
        return new_schedule

    m1, m2 = random.sample(new_schedule, 2)

    m1["date"], m2["date"] = m2["date"], m1["date"]
    m1["slot_id"], m2["slot_id"] = m2["slot_id"], m1["slot_id"]
    m1["venue_id"], m2["venue_id"] = m2["venue_id"], m1["venue_id"]

    return new_schedule


def generate_neighbor(
    schedule: List[Dict[str, Any]],
    problem: Dict[str, Any],
    move_prob: float = 0.5
) -> List[Dict[str, Any]]:
    if random.random() < move_prob:
        return move_match(schedule, problem)
    return swap_matches(schedule)


def local_search(
    initial_schedule: List[Dict[str, Any]],
    problem: Dict[str, Any],
    fitness_fn: Callable[[List[Dict[str, Any]], Dict[str, Any]], float],
    max_iterations: int = 300,
    minimize: bool = True,
    feasibility_fn: Optional[Callable[[List[Dict[str, Any]], Dict[str, Any]], bool]] = None
) -> List[Dict[str, Any]]:
    check_feasible = feasibility_fn if feasibility_fn is not None else is_feasible

    current_schedule = copy.deepcopy(initial_schedule)
    current_fitness = fitness_fn(current_schedule, problem)

    for _ in range(max_iterations):
        neighbor = generate_neighbor(current_schedule, problem)

        if not check_feasible(neighbor, problem):
            continue

        neighbor_fitness = fitness_fn(neighbor, problem)

        is_better = (
            neighbor_fitness < current_fitness
            if minimize
            else neighbor_fitness > current_fitness
        )

        if is_better:
            current_schedule = neighbor
            current_fitness = neighbor_fitness

    return current_schedule