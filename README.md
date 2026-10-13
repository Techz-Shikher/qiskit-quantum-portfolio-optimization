\# Quantum Portfolio Optimization Using QAOA



\*\*Event:\*\* Qiskit Fall Fest 2026  

\*\*Track:\*\* Track 2 — Quantum Optimization  

\*\*Problem:\*\* Select an optimal portfolio of stocks under a fixed-cardinality constraint.



\## 1. Overview



This project explores the use of the Quantum Approximate Optimization Algorithm (QAOA) for a portfolio optimization problem. It combines a classical brute-force baseline, a statevector-based QAOA simulation, a QAOA depth experiment, and a penalty-parameter sweep.



The beginner track uses six stocks and selects exactly three. A separate intermediate-track experiment evaluates a 12-stock portfolio using classical optimization methods.



\## 2. Problem Statement



Given expected returns and a covariance matrix, select exactly \\(K\\) stocks to balance return and risk.



The binary decision variable is:



\\\[

x\_i \\in \\{0,1\\}

\\]



where \\(x\_i=1\\) means stock \\(i\\) is selected.



The objective is:



\\\[

C(x)=q\\,x^T\\Sigma x-\\mu^Tx+

\\lambda\\left(\\sum\_{i=1}^{n}x\_i-K\\right)^2

\\]



Where:



\- \\(x\\): binary portfolio-selection vector

\- \\(\\mu\\): expected-return vector

\- \\(\\Sigma\\): covariance matrix

\- \\(q\\): risk-weight parameter

\- \\(K\\): required number of selected stocks

\- \\(\\lambda\\): penalty for violating the cardinality constraint



The objective is minimized. The penalty term discourages solutions that select a number of stocks different from \\(K\\).



\## 3. Six-Stock Beginner Track



The experiment uses a deterministic synthetic dataset generated with random seed `2026`.



| Parameter | Value |

|---|---:|

| Number of stocks | 6 |

| Required portfolio size | 3 |

| Risk-weight parameter | 0.5 |

| Number of possible binary strings | 64 |

| Number of feasible portfolios | 20 |

| QAOA depths tested | 1, 2, 3, 4 |



\### Classical brute-force baseline



All 20 portfolios satisfying the exact-three-stock constraint were evaluated.



The best portfolio found was:



\- \*\*Selected stocks:\*\* 2, 3, 6

\- \*\*Binary representation:\*\* `011001`

\- \*\*Objective cost:\*\* approximately `-0.503015`



This solution provides the exact optimum for the six-stock instance and serves as a reference for the QAOA experiments.



\## 4. QAOA Approach



The implementation uses a statevector representation with QAOA-style cost-phase and transverse-field mixer layers.



The cost phase applies the objective value to each computational-basis state. The mixer applies RX rotations to the individual qubits.



The circuit depth is represented by \\(p\\), the number of alternating cost and mixer layers.



The depth experiment evaluates \\(p=1,2,3,4\\), using classical optimization of the QAOA parameters. Multiple initializations are used for each depth.



\### Depth-sweep results



| Depth \\(p\\) | Expected cost | Feasible probability | Exact-optimum probability |

|---:|---:|---:|---:|

| 1 | 0.110713 | 57.90% | 3.68% |

| 2 | 0.202474 | 67.94% | 3.38% |

| 3 | -0.101954 | 92.69% | 5.03% |

| 4 | -0.213192 | 88.23% | 4.55% |



The results show that the measured performance is not strictly monotonic with depth. The \\(p=3\\) run achieved the highest feasible probability in this sweep, while the \\(p=4\\) run achieved the lowest expected cost among the four reported runs.



The classical brute-force solution remains the reference optimum. These QAOA runs are approximate and should not be presented as outperforming the exact solution.



\*\*Optimization limitation:\*\* The \\(p=2,3,4\\) runs reached the configured maximum of 100 objective evaluations. The reported parameters are therefore not guaranteed to be globally optimal.



\## 5. Penalty-Parameter Experiment



The penalty parameter \\(\\lambda\\) controls how strongly the optimization discourages portfolios that do not contain exactly three stocks.



The experiment sweeps:



`0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5`



Each tested value uses a depth-one QAOA configuration with two optimizer initializations and a maximum of 80 iterations per initialization.



\### Observations



\- At \\(\\lambda=0.01\\), the feasible probability was 3.88%.

\- At \\(\\lambda=1\\), the exact-optimum probability was 3.68%, the highest observed in this sweep.

\- At \\(\\lambda=5\\), the feasible probability was 67.10%, the highest observed in this sweep.

\- The results are non-monotonic, demonstrating that increasing the penalty does not guarantee improved performance for a finite-budget optimization run.



The best penalty depends on the evaluation metric: feasibility and exact-optimum probability are different measures.



\## 6. Intermediate Track: 12-Stock Classical Baseline



A separate 12-stock experiment evaluates portfolios containing exactly six stocks.



The number of feasible portfolios is:



\\\[

\\binom{12}{6}=924

\\]



All 924 feasible portfolios were enumerated. The best solution found selected zero-indexed stocks `(1, 5, 6, 8, 10, 11)`.



Using one-based stock numbering, the portfolio is:



\*\*Stocks 2, 6, 7, 9, 11, 12\*\*



The objective cost was approximately `-1.066392`.



The expected-return greedy baseline and marginal-cost greedy baseline both found the same solution on this particular synthetic instance. This agreement is specific to the generated data and does not establish that greedy methods generally find optimal portfolios.



\*\*Scope limitation:\*\* The 12-stock result is a classical baseline. A completed 12-stock QAOA result is not claimed in this report.



\## 7. Visualizations



The project generates the following plots:



| File | Purpose |

|---|---|

| `plots/qaoa\_probabilities.png` | Feasibility and exact-optimum probabilities across QAOA depths |

| `plots/qaoa\_expected\_cost.png` | Expected objective cost across QAOA depths |

| `plots/qaoa\_penalty\_sweep.png` | Effect of penalty strength on observed performance |



The numerical results are saved under `results/`.



\## 8. Project Structure



```text

Qiskit-Fall-Fest/

├── src/

│   ├── portfolio\_test.py

│   ├── qaoa\_six\_stock.py

│   ├── plot\_results.py

│   └── penalty\_sweep.py

├── results/

│   ├── qaoa\_depth\_sweep.csv

│   ├── qaoa\_depth\_sweep.npz

│   └── qaoa\_penalty\_sweep.csv

├── plots/

│   ├── qaoa\_probabilities.png

│   ├── qaoa\_expected\_cost.png

│   └── qaoa\_penalty\_sweep.png

└── README.md

```



\## 9. Technology Stack



\- Python

\- NumPy

\- SciPy

\- Matplotlib

\- Qiskit

\- Qiskit Aer



The current depth and penalty experiments use direct statevector operations to apply the QAOA cost-phase and mixer layers. Qiskit is installed in the environment, but the reported experiments should not be described as GPU-accelerated or as completed Aer circuit simulations.



\## 10. Reproducibility



The six-stock synthetic dataset uses random seed `2026`.



The experiments can be rerun from the project directory after activating the virtual environment and installing the required packages.



On Windows PowerShell:



```powershell

cd E:\\Qiskit-Fall-Fest

.\\.venv\\Scripts\\Activate.ps1

python src\\portfolio\_test.py

python src\\qaoa\_six\_stock.py

python src\\plot\_results.py

python src\\penalty\_sweep.py

```



These commands rerun the tests, depth sweep, plotting step, and penalty sweep. Optimizer settings and random initialization can affect the QAOA results, so the reported numbers should be associated with their corresponding run configuration.



\## 11. Limitations and Future Work



1\. The experiments use synthetic rather than real historical market data.

2\. The six-stock QAOA results are approximate and use finite optimizer budgets.

3\. Results can vary with initialization, optimizer settings, circuit depth, and penalty strength.

4\. The 12-stock experiment establishes a classical baseline only.

5\. Future work could test gate-level Qiskit circuits, compare simulator backends, improve parameter optimization, and evaluate the approach on historical financial data.



## 12. Novel Contribution: Q-Repair

### Motivation

Approximate optimization algorithms can assign probability to bitstrings that violate portfolio constraints. This project investigates whether a classical post-processing step can turn such samples into useful feasible portfolios.

### Method

Q-Repair operates on each six-bit portfolio candidate:

1. Count the number of selected stocks.
2. If the portfolio contains exactly three stocks, preserve it.
3. Otherwise, find feasible portfolios at the minimum Hamming distance from the original candidate.
4. Among equally close candidates, select the portfolio with the lowest original risk-return objective.
5. Aggregate the QAOA probability mass according to the repaired portfolio.

The repair rule uses the original portfolio objective, excluding the cardinality penalty, to compare feasible candidates.

### Experimental results

| Metric | Raw QAOA | After Q-Repair |
|---|---:|---:|
| Probability mass at exact optimum | 5.03% | 8.81% |
| Expected original portfolio cost | −0.382748* | −0.389191 |
| Exact optimum | Stocks 2, 3, 6 | Stocks 2, 3, 6 |

\*The raw expected cost is conditional on obtaining a feasible portfolio; the repaired expected cost is computed over the complete input distribution after every candidate has been repaired. These quantities are useful operationally but are not identical sampling metrics.

The probability mass mapped to the exact optimum increased by approximately 3.78 percentage points, or 1.75 times the raw optimum probability.

### Initialization sensitivity

Eight deterministic starting points were evaluated with COBYLA, using a maximum of 100 objective evaluations per run. The best observed penalized objective was −0.101954, while the worst was 0.522604. All eight runs reached the evaluation limit with `success=False`.

This indicates substantial sensitivity to initialization under the tested budget. The results should therefore be interpreted as preliminary rather than as evidence of convergence.

### Limitations

- Q-Repair is classical post-processing and does not establish quantum advantage.
- It uses the known objective function to rank feasible candidates.
- The results are from a six-stock synthetic dataset and a statevector simulation.
- The probability mass after repair is not the raw measurement probability of the repaired portfolio.
- The optimizer did not report successful convergence within the configured evaluation budget.

### Reproducibility artifacts

- `src/q_repair.py` — implementation and experiment
- `src/plot_q_repair.py` — comparison visualization
- `results/q_repair_results.csv` — summary metrics
- `results/q_repair_distribution.npz` — state probabilities and repaired candidates
- `results/qaoa_initialization_stability.csv` — optimizer results for all eight starting points
- `plots/q_repair_comparison.png` — raw-versus-repaired comparison



\## 13. Conclusion

This project formulates fixed-cardinality portfolio selection as a binary optimization problem and investigates QAOA-style statevector optimization on a six-stock instance.
The brute-force baseline establishes a reference optimum, while depth and penalty sweeps show how algorithm settings affect feasibility and solution quality. The separate 12-stock experiment provides a classical comparison without making unsupported claims about larger-scale quantum performance.



