from pathlib import Path
import pandas as pd

from data_loader import load_dataset
from problem_model import build_problem
from feasibility import validate_schedule, print_validation_report
from greedy_baseline import generate_greedy_schedule


def save_schedule(schedule, output_file):
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(schedule).to_csv(path, index=False)
    print(f"Schedule saved to: {path.resolve()}")


def main():
    print("\nSPORTS TOURNAMENT SCHEDULING")
    print("================================")

    print("\n1. Loading dataset...")
    data = load_dataset("dataset")
    print("Dataset validation successful.")

    print("\n2. Building problem...")
    problem = build_problem(data)
    print(f"Teams: {len(problem['teams'])} | Matches: {len(problem['matches'])} | "
          f"Venues: {len(problem['venues'])} | Slots: {len(problem['slots'])} | "
          f"Dates: {len(problem['dates'])}")

    print("\n3. Checking the reference schedule...")
    if data["feasible_schedule"] is not None:
        reference = data["feasible_schedule"].to_dict("records")
        print_validation_report(validate_schedule(reference, problem))

    print("\n4. Generating greedy baseline...")
    schedule = generate_greedy_schedule(problem)

    if schedule is None:
        print("Greedy baseline could not find a schedule.")
        return

    print("\n5. Checking the greedy schedule...")
    print_validation_report(validate_schedule(schedule, problem))

    print("\n6. Saving...")
    save_schedule(schedule, "outputs/greedy_baseline.csv")


if __name__ == "__main__":
    main()
