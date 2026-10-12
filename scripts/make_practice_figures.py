from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "results" / "tables" / "practice_ab_comparison.csv"
FIG = ROOT / "results" / "figures"
CONFIG = ROOT / "data" / "practice_config.json"


def processor_definition(label: str) -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    path = ROOT / cfg["processor_files"][label]
    return json.loads(path.read_text(encoding="utf-8"))


def write_exact_svg(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def save_ab_performance(df: pd.DataFrame) -> None:
    a = df.loc[df["processor"] == "A"].iloc[0]
    b = df.loc[df["processor"] == "B"].iloc[0]
    a_value = round(float(a["mean_fidelity"]), 4)
    b_value = round(float(b["mean_fidelity"]), 4)
    if (a_value, b_value) != (0.9611, 0.7822):
        raise ValueError("A/B performance figure inputs drifted from the controlled benchmark.")
    write_exact_svg(
        FIG / "AB_performance.svg",
        f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="420" viewBox="0 0 720 420">
<rect width="100%" height="100%" fill="white"/>
<text x="360" y="35" text-anchor="middle" font-size="22">Source-document A/B performance</text>
<line x1="90" y1="360" x2="650" y2="360" stroke="black"/>
<line x1="90" y1="70" x2="90" y2="360" stroke="black"/>
<rect x="145" y="96" width="110" height="264" fill="#777"/>
<rect x="485" y="146" width="110" height="214" fill="#aaa"/>
<text x="200" y="85" text-anchor="middle">{a_value:.4f}</text>
<text x="540" y="135" text-anchor="middle">{b_value:.4f}</text>
<text x="200" y="390" text-anchor="middle">A — 5Q</text>
<text x="540" y="390" text-anchor="middle">B — 7Q</text>
<text x="360" y="415" text-anchor="middle">Mean fidelity to embedded exact reference</text>
</svg>
''',
    )


def save_architecture_tradeoffs(df: pd.DataFrame) -> None:
    by = df.set_index("processor")
    values = (
        float(by.loc["A", "depth"]),
        float(by.loc["B", "depth"]),
        float(by.loc["A", "two_qubit_gate_count"]),
        float(by.loc["B", "two_qubit_gate_count"]),
        float(by.loc["A", "swap_count"]),
        float(by.loc["B", "swap_count"]),
    )
    if values != (8.0, 32.0, 4.0, 28.0, 0.0, 8.0):
        raise ValueError("Architecture-tradeoff figure inputs drifted from the controlled benchmark.")
    write_exact_svg(
        FIG / "architecture_tradeoffs.svg",
        '''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="460" viewBox="0 0 760 460">
<rect width="100%" height="100%" fill="white"/>
<text x="380" y="34" text-anchor="middle" font-size="22">Source-document A/B architecture trade-offs</text>
<text x="150" y="82" text-anchor="middle" font-size="16">Depth</text>
<text x="380" y="82" text-anchor="middle" font-size="16">2Q gates</text>
<text x="610" y="82" text-anchor="middle" font-size="16">SWAPs</text>
<line x1="55" y1="370" x2="245" y2="370" stroke="black"/>
<line x1="285" y1="370" x2="475" y2="370" stroke="black"/>
<line x1="515" y1="370" x2="705" y2="370" stroke="black"/>
<rect x="85" y="290" width="55" height="80" fill="#777"/>
<rect x="170" y="50" width="55" height="320" fill="#aaa"/>
<rect x="315" y="330" width="55" height="40" fill="#777"/>
<rect x="400" y="50" width="55" height="320" fill="#aaa"/>
<rect x="545" y="350" width="55" height="20" fill="#777"/>
<rect x="630" y="50" width="55" height="320" fill="#aaa"/>
<text x="112" y="283" text-anchor="middle">8</text>
<text x="197" y="43" text-anchor="middle">32</text>
<text x="342" y="323" text-anchor="middle">4</text>
<text x="427" y="43" text-anchor="middle">28</text>
<text x="572" y="343" text-anchor="middle">0</text>
<text x="657" y="43" text-anchor="middle">8</text>
<text x="112" y="400" text-anchor="middle">A</text><text x="197" y="400" text-anchor="middle">B</text>
<text x="342" y="400" text-anchor="middle">A</text><text x="427" y="400" text-anchor="middle">B</text>
<text x="572" y="400" text-anchor="middle">A</text><text x="657" y="400" text-anchor="middle">B</text>
<text x="380" y="438" text-anchor="middle">B pays for non-adjacent 0–2 interactions through routing</text>
</svg>
''',
    )


def save_processor_graph(label: str) -> None:
    definition = processor_definition(label)
    if label == "A":
        expected = (5, "fixed baseline graph", [(0, 1), (0, 2), (0, 3), (3, 4)])
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="700" height="320" viewBox="0 0 700 320">
<rect width="100%" height="100%" fill="white"/>
<text x="350" y="36" text-anchor="middle" font-size="22">Processor A — 5Q fixed baseline graph</text>
<g stroke="black" stroke-width="3">
<line x1="120" y1="160" x2="280" y2="90"/>
<line x1="120" y1="160" x2="350" y2="240"/>
<line x1="120" y1="160" x2="500" y2="110"/>
<line x1="500" y1="110" x2="580" y2="230"/>
</g>
<g fill="#777"><circle cx="120" cy="160" r="25"/><circle cx="280" cy="90" r="25"/><circle cx="350" cy="240" r="25"/><circle cx="500" cy="110" r="25"/><circle cx="580" cy="230" r="25"/></g>
<g fill="white" font-size="16" text-anchor="middle"><text x="120" y="166">0</text><text x="280" y="96">1</text><text x="350" y="246">2</text><text x="500" y="116">3</text><text x="580" y="236">4</text></g>
</svg>
'''
    else:
        expected = (7, "heavy-hex-inspired graph", [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (2, 6)])
        svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="700" height="360" viewBox="0 0 700 360">
<rect width="100%" height="100%" fill="white"/>
<text x="350" y="36" text-anchor="middle" font-size="22">Processor B — 7Q heavy-hex-inspired graph</text>
<g stroke="black" stroke-width="3">
<line x1="120" y1="150" x2="230" y2="70"/>
<line x1="230" y1="70" x2="370" y2="70"/>
<line x1="370" y1="70" x2="510" y2="150"/>
<line x1="510" y1="150" x2="450" y2="270"/>
<line x1="450" y1="270" x2="280" y2="270"/>
<line x1="280" y1="270" x2="120" y2="150"/>
<line x1="370" y1="70" x2="370" y2="185"/>
</g>
<g fill="#777"><circle cx="120" cy="150" r="25"/><circle cx="230" cy="70" r="25"/><circle cx="370" cy="70" r="25"/><circle cx="510" cy="150" r="25"/><circle cx="450" cy="270" r="25"/><circle cx="280" cy="270" r="25"/><circle cx="370" cy="185" r="25"/></g>
<g fill="white" font-size="16" text-anchor="middle"><text x="120" y="156">0</text><text x="230" y="76">1</text><text x="370" y="76">2</text><text x="510" y="156">3</text><text x="450" y="276">4</text><text x="280" y="276">5</text><text x="370" y="191">6</text></g>
</svg>
'''
    exp_n, exp_arch, exp_edges = expected
    if definition["num_qubits"] != exp_n or definition["architecture"] != exp_arch:
        raise ValueError(f"Processor {label} definition drifted from the source contract.")
    if [tuple(edge) for edge in definition["coupling_map"]] != exp_edges:
        raise ValueError(f"Processor {label} coupling map drifted from the source contract.")
    write_exact_svg(FIG / f"processor_{label}_graph.svg", svg)


def main() -> None:
    if not TABLE.is_file():
        raise FileNotFoundError(f"Practice result table not found: {TABLE}")
    df = pd.read_csv(TABLE)
    if set(df["processor"]) != {"A", "B"}:
        raise ValueError("Practice result table must contain Processor A and B.")
    FIG.mkdir(parents=True, exist_ok=True)
    save_ab_performance(df)
    save_architecture_tradeoffs(df)
    save_processor_graph("A")
    save_processor_graph("B")


if __name__ == "__main__":
    main()
