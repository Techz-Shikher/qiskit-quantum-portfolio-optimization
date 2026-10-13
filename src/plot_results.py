
import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

root = Path(__file__).resolve().parent.parent
results_dir = root / "results"
plots_dir = root / "plots"
results_dir.mkdir(exist_ok=True)
plots_dir.mkdir(exist_ok=True)

data = np.load(results_dir / "qaoa_depth_sweep.npz")

fields = [
    "p",
    "expected_cost",
    "feasible_probability",
    "exact_optimum_probability",
]

rows = zip(*(data[field].tolist() for field in fields))

with open(results_dir / "qaoa_depth_sweep.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(fields)
    writer.writerows(rows)

depth = data["p"]
feasible = data["feasible_probability"] * 100
exact = data["exact_optimum_probability"] * 100
expected = data["expected_cost"]

plt.figure()
plt.plot(depth, feasible, marker="o", label="Feasible probability")
plt.plot(depth, exact, marker="s", label="Exact optimum probability")
plt.xlabel("QAOA depth p")
plt.ylabel("Probability (%)")
plt.title("QAOA probability metrics vs depth")
plt.xticks(depth)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig(plots_dir / "qaoa_probabilities.png", dpi=200)
plt.close()

plt.figure()
plt.plot(depth, expected, marker="o")
plt.xlabel("QAOA depth p")
plt.ylabel("Expected penalized cost")
plt.title("Expected cost vs QAOA depth")
plt.xticks(depth)
plt.grid(True)
plt.tight_layout()
plt.savefig(plots_dir / "qaoa_expected_cost.png", dpi=200)
plt.close()

print("Saved:")
print(results_dir / "qaoa_depth_sweep.csv")
print(plots_dir / "qaoa_probabilities.png")
print(plots_dir / "qaoa_expected_cost.png")
