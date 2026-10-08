from __future__ import annotations
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / 'results/tables/practice_ab_comparison.csv'
FIG = ROOT / 'results/figures'
FIG.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(TABLE).set_index('processor')

ax = df[['mean_fidelity']].plot.bar(rot=0, legend=False)
ax.set_ylabel('Mean fidelity to exact state')
ax.set_title('Practice-only A/B performance')
ax.set_ylim(0, 1.05)
plt.tight_layout(); plt.savefig(FIG/'practice_ab_performance.png', dpi=180); plt.close()

m = df[['depth','two_qubit_gate_count','swap_count']]
ax = m.plot.bar(rot=0)
ax.set_ylabel('Count / depth')
ax.set_title('Practice-only architecture trade-offs')
plt.tight_layout(); plt.savefig(FIG/'practice_architecture_tradeoffs.png', dpi=180); plt.close()

logical = pd.Series({'rzz': 4, 'rx': 4, 'cx': 0}, name='logical')
compiled_A = pd.Series({'rzz': 4, 'rx': 4, 'cx': 0}, name='Processor A')
compiled_B = pd.Series({'rzz': 4, 'rx': 4, 'cx': 24}, name='Processor B')
ops = pd.concat([logical, compiled_A, compiled_B], axis=1)
ax = ops.plot.bar(rot=0)
ax.set_ylabel('Gate count')
ax.set_title('Practice-only logical vs compiled operation counts')
plt.tight_layout(); plt.savefig(FIG/'practice_logical_vs_transpiled.png', dpi=180); plt.close()
print('Figures written to', FIG)
