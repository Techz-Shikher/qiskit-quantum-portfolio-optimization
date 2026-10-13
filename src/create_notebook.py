from pathlib import Path
import nbformat as nbf
import sys

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)

nb = nbf.v4.new_notebook()
cells = []

def markdown(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))

def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))

markdown("""
# Quantum Portfolio Optimization Using QAOA

**Qiskit Fall Fest 2026 — Track 2: Quantum Optimization**

This notebook documents the six-stock portfolio optimization experiment,
classical exact baseline, QAOA depth and penalty sweeps, and Q-Repair
classical post-processing.

## Research questions

1. Can the six-stock portfolio objective be mapped to a QAOA cost function?
2. How do circuit depth and penalty strength affect feasibility and objective cost?
3. Can a constraint-aware classical repair rule improve the distribution of
   feasible portfolio candidates?
4. How sensitive are the observed results to optimizer initialization?

**Scope:** The QAOA experiments use a six-qubit statevector simulation.
The 12-stock result is a separate classical baseline; no completed
12-stock QAOA result is claimed.
""")

markdown("""
## 1. Mathematical formulation

For a binary portfolio vector \(x\\in\\{0,1\\}^n\), minimize

\\[
C(x)=q x^T\\Sigma x-\\mu^T x+
\\lambda\\left(\\sum_i x_i-K\\right)^2.
\\]

Here, \\(\\mu\\) contains expected returns, \\(\\Sigma\\) is a positive
semidefinite covariance-like matrix, \(q\) weights risk, and \(K\) is
the required portfolio size. The penalty discourages selecting a number
of stocks other than \(K\).

The experiments use a deterministic synthetic dataset with seed 2026,
six stocks, exactly three selections, and \(q=0.5\).
""")

code("""
import itertools
import runpy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Image

ROOT = Path.cwd().resolve()
while ROOT != ROOT.parent and not (ROOT / "src").is_dir():
    ROOT = ROOT.parent

if not (ROOT / "src").is_dir():
    raise RuntimeError(
        "Cannot find project root. Open this notebook from "
        "E:/Qiskit-Fall-Fest or a subfolder of that directory."
    )

sys.path.insert(0, str(ROOT / "src"))
print("Project root:", ROOT)
print("Python:", sys.version)
""")

markdown("""
## 2. Reproduce the exact six-stock classical baseline

All \\(2^6=64\\) binary portfolios are considered, of which
\\(\\binom{6}{3}=20\\) satisfy the exact-three-stock constraint.
The best feasible portfolio is the reference optimum.
""")

code("""
rng = np.random.default_rng(2026)
n, K, q = 6, 3, 0.5
mu = rng.uniform(0.05, 0.25, n)
A = rng.normal(0, 0.1, (n, n))
sigma = A @ A.T

bitstrings = np.array(
    list(itertools.product([0, 1], repeat=n)), dtype=int
)

def portfolio_cost(x):
    return float(q * (x @ sigma @ x) - mu @ x)

base_costs = np.array([portfolio_cost(x) for x in bitstrings])
feasible_mask = bitstrings.sum(axis=1) == K
best_idx = np.argmin(np.where(feasible_mask, base_costs, np.inf))
best_x = bitstrings[best_idx]
best_cost = base_costs[best_idx]

print("Total binary portfolios:", len(bitstrings))
print("Feasible portfolios:", int(feasible_mask.sum()))
print("Optimal bitstring:", "".join(map(str, best_x)))
print("Selected stocks (1-based):",
      tuple(np.flatnonzero(best_x) + 1))
print(f"Exact feasible objective: {best_cost:.6f}")

assert len(bitstrings) == 64
assert feasible_mask.sum() == 20
assert tuple(np.flatnonzero(best_x) + 1) == (2, 3, 6)
assert np.isclose(best_cost, -0.503015, atol=1e-5)
""")

markdown("""
## 3. Run the QAOA depth experiment

The script uses direct statevector cost-phase and transverse-field mixer
operations. The depth sweep uses a finite COBYLA optimization budget.
Optimizer success flags and evaluation limits must be retained when
interpreting the results.
""")

code("""
print("Running six-stock QAOA depth sweep...")
runpy.run_path(str(ROOT / "src" / "qaoa_six_stock.py"),
               run_name="__main__")

depth_csv = ROOT / "results" / "qaoa_depth_sweep.csv"
if depth_csv.exists():
    depth_df = pd.read_csv(depth_csv)
    display(depth_df)
else:
    print("Depth CSV was not created; inspect the script output.")
""")

code("""
for filename in [
    "qaoa_probabilities.png",
    "qaoa_expected_cost.png",
]:
    path = ROOT / "plots" / filename
    if path.exists():
        print(filename)
        display(Image(filename=str(path)))
    else:
        print("Plot not found:", path)
""")

markdown("""
## 4. Penalty-strength sweep

The penalty parameter controls how strongly infeasible portfolios are
discouraged. Feasibility probability and exact-optimum probability are
different metrics; the best penalty can depend on which metric matters.
""")

code("""
print("Running penalty sweep...")
runpy.run_path(str(ROOT / "src" / "penalty_sweep.py"),
               run_name="__main__")

penalty_csv = ROOT / "results" / "qaoa_penalty_sweep.csv"
if penalty_csv.exists():
    penalty_df = pd.read_csv(penalty_csv)
    display(penalty_df)
else:
    print("Penalty CSV was not created; inspect the script output.")

penalty_plot = ROOT / "plots" / "qaoa_penalty_sweep.png"
if penalty_plot.exists():
    display(Image(filename=str(penalty_plot)))
""")

markdown("""
## 5. Q-Repair: constraint-aware classical post-processing

Q-Repair maps each bitstring to a feasible portfolio by changing the
minimum number of bits needed to select exactly three stocks. Among
equally close candidates, it selects the lowest-cost feasible portfolio.

This is a classical post-processing heuristic, not a quantum speedup.
The repaired optimum probability is probability mass mapped to the
optimum after repair, not the raw probability of measuring that bitstring.
""")

code("""
print("Running Q-Repair and eight-start stability experiment...")
runpy.run_path(str(ROOT / "src" / "q_repair.py"),
               run_name="__main__")

for filename in [
    "q_repair_results.csv",
    "qaoa_initialization_stability.csv",
]:
    path = ROOT / "results" / filename
    if path.exists():
        print("\\\\n", filename)
        display(pd.read_csv(path))
    else:
        print("Result file not found:", path)

repair_plot = ROOT / "plots" / "q_repair_comparison.png"
if repair_plot.exists():
    display(Image(filename=str(repair_plot)))
""")

markdown("""
## 6. Intermediate track: 12-stock classical baseline

For twelve stocks and six required selections, exhaustive search considers

\\[
\\binom{12}{6}=924
\\]

feasible portfolios. The separate classical experiment reported the
best portfolio as one-based stocks 2, 6, 7, 9, 11, and 12, with objective
approximately -1.066392.

This is a classical result only. This notebook does not claim a completed
12-stock QAOA experiment.
""")

markdown("""
## 7. Results interpretation

- The exact six-stock baseline is the reference optimum for this synthetic instance.
- QAOA performance is sensitive to depth, penalty strength, and initialization.
- The reported depth and penalty sweeps use finite optimizer budgets.
- All eight reported stability runs reached the configured evaluation limit
  with `success=False`; convergence is not established.
- Q-Repair increases the observed probability mass mapped to the exact optimum
  from 5.03% to 8.81% for the selected run, but uses the known objective
  function as part of classical repair.
- Simulation results do not establish quantum advantage over classical methods.

## 8. Reproducibility and artifacts

The source scripts are in `src/`, numerical data in `results/`, and plots in
`plots/`. The synthetic data uses NumPy seed 2026. Optimizer results may depend
on library versions, settings, and initialization.

For submission, ensure the notebook runs from top to bottom in a clean
environment, then save it with its outputs if required by the event rules.
""")

nb.cells = cells
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "name": "python",
        "version": sys.version.split()[0],
    },
}

output = NOTEBOOK_DIR / "quantum_portfolio_optimization.ipynb"
nbf.write(nb, output)

print("Notebook created:", output)
print("Cell count:", len(nb.cells))
