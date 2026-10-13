
import itertools
import time
import numpy as np
from qiskit.quantum_info import SparsePauliOp

# Hackathon's deterministic dataset
rng = np.random.default_rng(2026)
n, K, q = 6, 3, 0.5

mu = rng.uniform(0.05, 0.25, n)
A = rng.normal(0, 0.1, (n, n))
sigma = A @ A.T

def portfolio_cost(x, penalty=1.0):
    x = np.asarray(x, dtype=float)
    risk = q * (x @ sigma @ x)
    returns = mu @ x
    constraint = penalty * (x.sum() - K) ** 2
    return risk - returns + constraint

# Exact classical solution: enumerate all portfolios of size K
start = time.perf_counter()
candidates = []

for stocks in itertools.combinations(range(n), K):
    x = np.zeros(n, dtype=int)
    x[list(stocks)] = 1
    candidates.append((portfolio_cost(x), stocks))

best_cost, best_stocks = min(candidates)
elapsed = time.perf_counter() - start

print("=== Six-stock portfolio test ===")
print("Python:", __import__("sys").version.split()[0])
print("Number of feasible portfolios:", len(candidates))
print("Expected returns (mu):", np.round(mu, 4))
print("Best stocks (zero-based):", best_stocks)
print("Best stocks (one-based):", tuple(i + 1 for i in best_stocks))
print("Best feasible cost:", round(best_cost, 6))
print("Enumeration time:", round(elapsed, 6), "seconds")

# Verify the Qiskit Pauli representation for x_i = (I - Z_i)/2.
# Build the Hamiltonian term by term and check every bitstring.
I = np.eye(2)
Z = np.diag([1.0, -1.0])
x_ops = []

for i in range(n):
    ops = [I] * n
    ops[i] = (I - Z) / 2
    op = ops[0]
    for matrix in ops[1:]:
        op = np.kron(op, matrix)
    x_ops.append(op)

H = np.zeros((2**n, 2**n))

for i in range(n):
    H -= mu[i] * x_ops[i]

for i in range(n):
    for j in range(n):
        H += q * sigma[i, j] * (x_ops[i] @ x_ops[j])

# Penalty: lambda * (sum(x_i) - K)^2
sum_x = sum(x_ops)
H += (sum_x - K * np.eye(2**n)) @ (sum_x - K * np.eye(2**n))

# Qiskit uses Pauli labels in reversed qubit order relative to x[0], x[1], ...
pauli = SparsePauliOp.from_operator(H)
max_error = 0.0

for bits in itertools.product([0, 1], repeat=n):
    # The diagonal matrix above indexes bitstrings in normal binary order.
    index = int("".join(map(str, bits)), 2)
    expected = portfolio_cost(bits)
    actual = H[index, index].real
    max_error = max(max_error, abs(expected - actual))

print("Hamiltonian matrix dimensions:", H.shape)
print("Maximum objective verification error:", max_error)
print("Qiskit Pauli terms:", len(pauli))
print("\nPORTFOLIO TEST PASSED" if max_error < 1e-9 else "\nCHECK FAILED")
