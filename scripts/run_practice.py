from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.practice_s3 import PracticeProcessor, ideal_exact_state, logical_trotter_circuit, benchmark_processor

cfg = json.loads((ROOT / 'data' / 'practice_config.json').read_text())
s = cfg['system']
logical = logical_trotter_circuit(s['trotter_steps'], s['total_time'], s['J'], s['h'])
exact = ideal_exact_state(s['n_qubits'], s['total_time'], s['J'], s['h'])

processors = {}
for key in ['A', 'B']:
    p = cfg['processors'][key]
    processors[key] = PracticeProcessor(
        name=p['name'],
        num_qubits=s['n_qubits'],
        coupling_map=tuple(tuple(edge) for edge in p['coupling_map']),
        p1=p['p1'],
        p2=p['p2'],
        readout_error=p['readout_error'],
    )

rows = []
for idx, key in enumerate(['A', 'B']):
    result = benchmark_processor(
        processors[key], logical, exact, s['n_qubits'], int(cfg['shots_or_trajectories']), int(cfg['seed']) + idx
    )
    result['processor'] = key
    result['processor_name'] = processors[key].name
    rows.append(result)

df = pd.DataFrame(rows)
out = ROOT / 'results' / 'tables'
out.mkdir(parents=True, exist_ok=True)
df.to_csv(out / 'practice_ab_comparison.csv', index=False)
for _, row in df.iterrows():
    pd.DataFrame([row]).to_csv(out / f"practice_processor_{row['processor']}_metrics.csv", index=False)
print(df.to_string(index=False))
print(f"Saved: {out / 'practice_ab_comparison.csv'}")
