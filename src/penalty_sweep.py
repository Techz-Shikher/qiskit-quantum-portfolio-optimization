
import csv
import itertools
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from pathlib import Path

root = Path(__file__).resolve().parent.parent
results_dir = root / "results"
plots_dir = root / "plots"
results_dir.mkdir(exist_ok=True)
plots_dir.mkdir(exist_ok=True)

rng = np.random.default_rng(2026)
n, K, q = 6, 3, 0.5
mu = rng.uniform(0.05, 0.25, n)
A = rng.normal(0, 0.1, (n, n))
sigma = A @ A.T

bitstrings = np.array(list(itertools.product([0, 1], repeat=n)), dtype=int)
feasible = bitstrings.sum(axis=1) == K
penalties = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
p = 1

def run_penalty(lam):
    costs = np.array([
        q * (x @ sigma @ x) - mu @ x
        + lam * (x.sum() - K)**2
        for x in bitstrings
    ])

    def state_for(params):
        gamma, beta = params
        state = np.ones(2**n, dtype=complex) / np.sqrt(2**n)
        state *= np.exp(-1j * gamma * costs)

        rx = np.array([
            [np.cos(beta), -1j * np.sin(beta)],
            [-1j * np.sin(beta), np.cos(beta)]
        ], dtype=complex)

        tensor = state.reshape((2,) * n)
        for axis in range(n):
            tensor = np.moveaxis(tensor, axis, 0)
            tensor = rx @ tensor.reshape(2, -1)
            tensor = tensor.reshape((2,) + (2,) * (n - 1))
            tensor = np.moveaxis(tensor, 0, axis)
        return tensor.reshape(-1)

    def objective(params):
        probs = np.abs(state_for(params))**2
        return float(probs @ costs)

    start = time.perf_counter()
    best = None
    for initial in ([0.5, 0.5], [1.0, 0.25]):
        result = minimize(
            objective, initial, method="COBYLA",
            options={"maxiter": 80, "rhobeg": 0.5}
        )
        if best is None or result.fun < best.fun:
            best = result

    probs = np.abs(state_for(best.x))**2
    elapsed = time.perf_counter() - start

    feasible_prob = float(probs[feasible].sum())
    exact_feasible_costs = np.where(feasible, costs, np.inf)
    exact_idx = int(np.argmin(exact_feasible_costs))

    return {
        "lambda": lam,
        "feasible_probability": feasible_prob,
        "exact_optimum_probability": float(probs[exact_idx]),
        "expected_penalized_cost": float(probs @ costs),
        "optimizer_success": bool(best.success),
        "runtime_seconds": elapsed,
    }

rows = []
for lam in penalties:
    row = run_penalty(lam)
    rows.append(row)
    print(
        f"lambda={lam:>4} | feasible={row['feasible_probability']:.2%}"
        f" | exact optimum={row['exact_optimum_probability']:.2%}"
        f" | expected cost={row['expected_penalized_cost']:.5f}"
        f" | time={row['runtime_seconds']:.2f}s"
    )

csv_path = results_dir / "qaoa_penalty_sweep.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

plt.figure()
plt.plot(
    [r["lambda"] for r in rows],
    [100 * r["feasible_probability"] for r in rows],
    marker="o"
)
plt.xscale("log")
plt.xlabel("Penalty lambda (log scale)")
plt.ylabel("Feasible probability (%)")
plt.title("QAOA feasibility vs penalty strength")
plt.grid(True)
plt.tight_layout()
plt.savefig(plots_dir / "qaoa_penalty_sweep.png", dpi=200)
plt.close()

print("\nSaved:", csv_path)
print("Saved:", plots_dir / "qaoa_penalty_sweep.png")
print("PENALTY SWEEP FINISHED")
