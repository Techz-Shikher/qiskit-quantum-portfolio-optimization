
import itertools
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

# ============================================================
# 1. Configuration and reproducible dataset
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(2026)

n, K, q = 6, 3, 0.5
penalty = 1.0
p = 3
MAXITER = 100

mu = rng.uniform(0.05, 0.25, n)
A = rng.normal(0, 0.1, (n, n))
sigma = A @ A.T

# x[0] corresponds to the first stock.
bitstrings = np.array(
    list(itertools.product([0, 1], repeat=n)),
    dtype=int,
)

def portfolio_cost(x):
    """Original objective, excluding the cardinality penalty."""
    return float(q * (x @ sigma @ x) - mu @ x)

# Penalized objective minimized by QAOA.
base_costs = np.array(
    [portfolio_cost(x) for x in bitstrings],
    dtype=float,
)

costs = base_costs + penalty * (
    bitstrings.sum(axis=1) - K
) ** 2

feasible = bitstrings.sum(axis=1) == K

# Exact classical solution among feasible portfolios.
best_idx = int(
    np.argmin(np.where(feasible, base_costs, np.inf))
)
best_x = bitstrings[best_idx].copy()
best_cost = float(base_costs[best_idx])

# ============================================================
# 2. Statevector QAOA implementation
# ============================================================

def apply_one_qubit(state, matrix, axis):
    """Apply a 2x2 matrix to one tensor axis."""
    tensor = state.reshape((2,) * n)
    tensor = np.moveaxis(tensor, axis, 0)

    tensor = matrix @ tensor.reshape(2, -1)
    tensor = tensor.reshape((2,) + (2,) * (n - 1))

    tensor = np.moveaxis(tensor, 0, axis)
    return tensor.reshape(-1)


def qaoa_state(params):
    """Return the QAOA state for p cost/mixer layers."""
    gammas = params[:p]
    betas = params[p:]

    state = np.ones(2**n, dtype=complex) / np.sqrt(2**n)

    for layer in range(p):
        # Cost phase: exp(-i * gamma * C(x)).
        state *= np.exp(-1j * gammas[layer] * costs)

        # Transverse-field mixer: product of RX(2 * beta).
        beta = betas[layer]
        rx = np.array(
            [
                [np.cos(beta), -1j * np.sin(beta)],
                [-1j * np.sin(beta), np.cos(beta)],
            ],
            dtype=complex,
        )

        for axis in range(n):
            state = apply_one_qubit(state, rx, axis)

    return state


def expected_penalized_cost(params):
    state = qaoa_state(params)
    probabilities = np.abs(state) ** 2
    return float(np.dot(probabilities, costs))


# ============================================================
# 3. Eight-start optimizer stability experiment
# ============================================================

starts = [
    np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5]),
    np.array([1.0, 1.0, 1.0, 0.25, 0.25, 0.25]),
    np.array([2.0, 2.0, 2.0, 0.75, 0.75, 0.75]),
    np.array([0.2, 0.8, 1.4, 0.3, 0.6, 0.9]),
    np.array([1.5, 0.4, 2.1, 0.7, 0.2, 0.5]),
    np.array([2.5, 1.2, 0.6, 0.1, 0.8, 1.1]),
    np.array([0.9, 1.8, 0.3, 1.0, 0.4, 0.7]),
    np.array([1.7, 0.6, 1.3, 0.8, 1.2, 0.2]),
]

runs = []
start_time = time.perf_counter()

print("=== QAOA INITIALIZATION STABILITY ===")

for i, initial in enumerate(starts, start=1):
    result = minimize(
        expected_penalized_cost,
        initial,
        method="COBYLA",
        options={
            "maxiter": MAXITER,
            "rhobeg": 0.5,
        },
    )

    runs.append(result)

    print(
        f"Start {i} | objective={result.fun:.6f} | "
        f"success={result.success} | "
        f"evaluations={result.nfev}"
    )

# Select the run with the lowest observed objective.
best_result = min(runs, key=lambda result: result.fun)

# Save all optimizer outcomes, not just the best one.
stability_df = pd.DataFrame(
    [
        {
            "start": i,
            "objective": float(result.fun),
            "success": bool(result.success),
            "evaluations": int(result.nfev),
        }
        for i, result in enumerate(runs, start=1)
    ]
)

stability_path = RESULTS_DIR / "qaoa_initialization_stability.csv"
stability_df.to_csv(stability_path, index=False)

# ============================================================
# 4. Compute the best run's probability distribution
# ============================================================

state = qaoa_state(best_result.x)
probs = np.abs(state) ** 2
probs /= probs.sum()

raw_feasible_probability = float(probs[feasible].sum())
raw_optimum_probability = float(probs[best_idx])

if raw_feasible_probability > 0:
    raw_conditional_cost = float(
        np.dot(probs[feasible], base_costs[feasible])
        / raw_feasible_probability
    )
else:
    raw_conditional_cost = float("nan")

# ============================================================
# 5. Constraint-aware classical repair
# ============================================================

def repair(x):
    """
    Produce a feasible portfolio with exactly K selected stocks.

    Change the minimum possible number of bits. Among equally
    close feasible portfolios, choose the lowest original cost.
    """
    x = np.asarray(x, dtype=int)
    count = int(x.sum())

    if count == K:
        return x.copy()

    distance = abs(count - K)

    candidate_ids = np.flatnonzero(
        np.sum(bitstrings != x, axis=1) == distance
    )

    candidate_ids = [
        i for i in candidate_ids
        if bitstrings[i].sum() == K
    ]

    chosen_idx = min(
        candidate_ids,
        key=lambda i: (
            base_costs[i],
            tuple(bitstrings[i]),
        ),
    )

    return bitstrings[chosen_idx].copy()


repaired = np.array(
    [repair(x) for x in bitstrings],
    dtype=int,
)

repaired_costs = np.array(
    [portfolio_cost(x) for x in repaired],
    dtype=float,
)

repaired_is_optimum = np.all(repaired == best_x, axis=1)

# These are distribution-weighted metrics over all 64 basis states.
repaired_expected_cost = float(np.dot(probs, repaired_costs))

repaired_optimum_probability = float(
    np.dot(probs, repaired_is_optimum.astype(float))
)

# Aggregate probability mass by repaired portfolio.
repaired_mass = {}

for i, x in enumerate(repaired):
    key = tuple(int(bit) for bit in x)
    repaired_mass[key] = repaired_mass.get(key, 0.0) + float(probs[i])

# Most probable repaired portfolio, with deterministic tie-breaking.
most_probable_repaired = min(
    repaired_mass,
    key=lambda key: (-repaired_mass[key], key),
)

most_probable_repaired_probability = float(
    repaired_mass[most_probable_repaired]
)

# Lowest-cost portfolio among the repaired outputs.
best_repaired_tuple = min(
    repaired_mass,
    key=lambda key: (
        portfolio_cost(np.asarray(key, dtype=int)),
        key,
    ),
)

best_repaired_probability = float(
    repaired_mass[best_repaired_tuple]
)

best_repaired_cost = portfolio_cost(
    np.asarray(best_repaired_tuple, dtype=int)
)

# ============================================================
# 6. Print summary
# ============================================================

runtime = time.perf_counter() - start_time

print("\n=== Q-REPAIR SUMMARY ===")
print("Exact classical optimum:", tuple(int(v) for v in best_x))
print(f"Exact classical cost: {best_cost:.6f}")
print(f"Best run success flag: {best_result.success}")
print(f"Best run evaluations: {best_result.nfev}")
print(f"Total runtime: {runtime:.2f}s")

print("\n--- Raw QAOA distribution ---")
print(f"Feasible probability: {raw_feasible_probability:.2%}")
print(f"Exact-optimum probability: {raw_optimum_probability:.2%}")
print(f"Conditional feasible cost: {raw_conditional_cost:.6f}")

print("\n--- After Q-Repair ---")
print(f"Expected original portfolio cost: {repaired_expected_cost:.6f}")
print(f"Exact-optimum probability mass: {repaired_optimum_probability:.2%}")
print(
    "Most probable repaired portfolio:",
    most_probable_repaired,
)
print(
    f"Probability of most probable repaired portfolio: "
    f"{most_probable_repaired_probability:.2%}"
)
print("Lowest-cost repaired portfolio:", best_repaired_tuple)
print(f"Lowest repaired cost: {best_repaired_cost:.6f}")

# ============================================================
# 7. Save results and probability distributions
# ============================================================

summary = {
    "p": p,
    "penalty": penalty,
    "num_starts": len(starts),
    "optimizer_success": bool(best_result.success),
    "optimizer_evaluations": int(best_result.nfev),
    "total_runtime_seconds": runtime,
    "exact_classical_cost": best_cost,
    "raw_feasible_probability": raw_feasible_probability,
    "raw_exact_optimum_probability": raw_optimum_probability,
    "raw_conditional_feasible_cost": raw_conditional_cost,
    "repaired_expected_portfolio_cost": repaired_expected_cost,
    "repaired_exact_optimum_probability": repaired_optimum_probability,
    "most_probable_repaired_portfolio": "-".join(
        map(str, most_probable_repaired)
    ),
    "most_probable_repaired_probability": most_probable_repaired_probability,
    "lowest_cost_repaired_portfolio": "-".join(
        map(str, best_repaired_tuple)
    ),
    "lowest_repaired_cost": best_repaired_cost,
}

summary_path = RESULTS_DIR / "q_repair_results.csv"
pd.DataFrame([summary]).to_csv(summary_path, index=False)

distribution_path = RESULTS_DIR / "q_repair_distribution.npz"
np.savez(
    distribution_path,
    bitstrings=bitstrings,
    probabilities=probs,
    repaired_bitstrings=repaired,
    original_costs=base_costs,
    penalized_costs=costs,
    repaired_costs=repaired_costs,
    exact_optimum=best_x,
)

print("\nSaved artifacts:")
print(f"  {stability_path}")
print(f"  {summary_path}")
print(f"  {distribution_path}")
print("\nQ-REPAIR FINISHED")
