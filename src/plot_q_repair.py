
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "results" / "q_repair_results.csv").iloc[0]

labels = ["Raw QAOA", "After Q-Repair"]
optimum_probs = [
    df["raw_exact_optimum_probability"] * 100,
    df["repaired_exact_optimum_probability"] * 100,
]
expected_costs = [
    df["raw_conditional_feasible_cost"],
    df["repaired_expected_portfolio_cost"],
]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

axes[0].bar(labels, optimum_probs)
axes[0].set_ylabel("Probability (%)")
axes[0].set_title("Probability mass at exact optimum")
axes[0].bar_label(
    axes[0].containers[0],
    labels=[f"{v:.2f}%" for v in optimum_probs],
    padding=3,
)
axes[0].set_ylim(0, max(optimum_probs) * 1.25)

axes[1].bar(labels, expected_costs)
axes[1].set_ylabel("Original portfolio cost")
axes[1].set_title("Cost comparison")
axes[1].bar_label(
    axes[1].containers[0],
    labels=[f"{v:.4f}" for v in expected_costs],
    padding=3,
)

fig.suptitle("Q-Repair: Classical Post-Processing of QAOA Samples")
fig.tight_layout()

out = ROOT / "plots" / "q_repair_comparison.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"Saved: {out}")
