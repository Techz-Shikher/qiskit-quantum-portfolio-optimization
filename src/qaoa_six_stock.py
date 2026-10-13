
import itertools
import time
import numpy as np
from scipy.optimize import minimize

# Hackathon dataset: deterministic
rng = np.random.default_rng(2026)
n, K, q = 6, 3, 0.5
mu = rng.uniform(0.05, 0.25, n)
A = rng.normal(0, 0.1, (n, n))
sigma = A @ A.T
penalty = 1.0

# Use lexicographic bitstrings: x[0] is the first bit.
bitstrings = np.array(
    list(itertools.product([0, 1], repeat=n)), dtype=int
)
costs = np.array([
    q * (x @ sigma @ x) - mu @ x
    + penalty * (x.sum() - K) ** 2
    for x in bitstrings
], dtype=float)

feasible = np.sum(bitstrings, axis=1) == K
best_idx = np.argmin(np.where(feasible, costs, np.inf))
best_x = bitstrings[best_idx]
best_cost = costs[best_idx]

# Apply a single-qubit matrix to a tensor axis.
def apply_one_qubit(state, matrix, axis, n):
    tensor = state.reshape((2,) * n)
    tensor = np.moveaxis(tensor, axis, 0)
    tensor = matrix @ tensor.reshape(2, -1)
    tensor = tensor.reshape((2,) + (2,) * (n - 1))
    tensor = np.moveaxis(tensor, 0, axis)
    return tensor.reshape(-1)

def qaoa_state(params, p):
    gammas = params[:p]
    betas = params[p:]

    # Uniform superposition
    state = np.ones(2**n, dtype=complex) / np.sqrt(2**n)

    # Lexicographic tensor axes: axis 0 corresponds to x[0].
    for layer in range(p):
        # Cost separator: exp(-i * gamma * C(x))
        state *= np.exp(-1j * gammas[layer] * costs)

        # Standard transverse-field mixer:
        # exp(-i * beta * sum_i X_i) = product_i RX(2 beta)
        beta = betas[layer]
        rx = np.array([
            [np.cos(beta), -1j * np.sin(beta)],
            [-1j * np.sin(beta), np.cos(beta)]
        ], dtype=complex)

        for axis in range(n):
            state = apply_one_qubit(state, rx, axis, n)

    return state

def run_depth(p, maxiter=100):
    # Multiple deterministic starting points reduce dependence on one start.
    starts = [
        np.array([0.5] * p + [0.5] * p),
        np.array([1.0] * p + [0.25] * p),
        np.array([2.0] * p + [0.75] * p),
    ]

    best_result = None
    start_time = time.perf_counter()

    for initial in starts:
        result = minimize(
            lambda params: float(np.dot(
                np.abs(qaoa_state(params, p))**2, costs
            )),
            initial,
            method="COBYLA",
            options={"maxiter": maxiter, "rhobeg": 0.5}
        )

        if best_result is None or result.fun < best_result.fun:
            best_result = result

    state = qaoa_state(best_result.x, p)
    probs = np.abs(state)**2
    feasible_probability = float(probs[feasible].sum())
    exact_probability = float(probs[best_idx])

    return {
        "p": p,
        "expected_cost": float(np.dot(probs, costs)),
        "feasible_probability": feasible_probability,
        "exact_optimum_probability": exact_probability,
        "best_cost": float(best_result.fun),
        "success": bool(best_result.success),
        "evaluations": int(best_result.nfev),
        "seconds": time.perf_counter() - start_time,
        "parameters": best_result.x,
    }

print("Exact classical optimum:", tuple(best_x))
print("Exact classical cost:", round(float(best_cost), 6))
print("\n=== QAOA depth sweep ===")

results = []
for p in range(1, 5):
    result = run_depth(p, maxiter=100)
    results.append(result)

    print(
        f"p={p} | expected cost={result['expected_cost']:.6f}"
        f" | feasible={result['feasible_probability']:.2%}"
        f" | exact optimum={result['exact_optimum_probability']:.2%}"
        f" | evals={result['evaluations']}"
        f" | runtime={result['seconds']:.2f}s"
    )

np.savez(
    "results/qaoa_depth_sweep.npz",
    p=np.array([r["p"] for r in results]),
    expected_cost=np.array([r["expected_cost"] for r in results]),
    feasible_probability=np.array(
        [r["feasible_probability"] for r in results]
    ),
    exact_optimum_probability=np.array(
        [r["exact_optimum_probability"] for r in results]
    ),
)

print("\nSaved results/qaoa_depth_sweep.npz")
print("QAOA DEPTH SWEEP FINISHED")
