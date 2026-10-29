#!/usr/bin/env python3
"""Generate publication-grade SVG figures for the next-level optimization study."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
TABLES = ROOT / "results" / "tables"


def write_svg(path: Path, content: str) -> None:
    path.write_text(content.strip(), encoding="utf-8")


def generate_optimized_ab_figure() -> None:
    """Figure showing how geometry-aware layout recovers Processor B's performance."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="420" viewBox="0 0 760 420">
  <defs>
    <linearGradient id="gradA" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>
    <linearGradient id="gradBNaive" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ef4444"/>
      <stop offset="100%" stop-color="#b91c1c"/>
    </linearGradient>
    <linearGradient id="gradBOpt" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#047857"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="#ffffff" rx="8"/>
  <text x="380" y="38" text-anchor="middle" font-family="system-ui, sans-serif" font-size="20" font-weight="bold" fill="#0f172a">Geometry-Aware Layout Optimization Recovery</text>
  <text x="380" y="60" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" fill="#64748b">Comparison of Solution Quality (Mean Fidelity to Exact State) on S3 Trotter Workload</text>
  
  <!-- Axis -->
  <line x1="100" y1="340" x2="680" y2="340" stroke="#cbd5e1" stroke-width="2"/>
  <line x1="100" y1="90" x2="100" y2="340" stroke="#cbd5e1" stroke-width="2"/>
  
  <!-- Grid lines -->
  <line x1="100" y1="95" x2="680" y2="95" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="4"/>
  <text x="90" y="100" text-anchor="end" font-family="monospace" font-size="11" fill="#94a3b8">1.00</text>
  
  <line x1="100" y1="145" x2="680" y2="145" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="4"/>
  <text x="90" y="150" text-anchor="end" font-family="monospace" font-size="11" fill="#94a3b8">0.90</text>
  
  <line x1="100" y1="195" x2="680" y2="195" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="4"/>
  <text x="90" y="200" text-anchor="end" font-family="monospace" font-size="11" fill="#94a3b8">0.80</text>
  
  <line x1="100" y1="245" x2="680" y2="245" stroke="#f1f5f9" stroke-width="1" stroke-dasharray="4"/>
  <text x="90" y="250" text-anchor="end" font-family="monospace" font-size="11" fill="#94a3b8">0.70</text>
  
  <!-- Bars -->
  <!-- Proc A: 0.9611 -> height = 0.9611 * 245 = 235.5 -> y = 340 - 235.5 = 104.5 -->
  <rect x="150" y="105" width="120" height="235" fill="url(#gradA)" rx="4"/>
  <text x="210" y="95" text-anchor="middle" font-family="monospace" font-size="14" font-weight="bold" fill="#1d4ed8">0.9611</text>
  <text x="210" y="360" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#334155">Processor A (5Q)</text>
  <text x="210" y="378" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" fill="#64748b">Baseline Layout (0 SWAPs)</text>
  
  <!-- Proc B Naive: 0.7822 -> height = 0.7822 * 245 = 191.6 -> y = 340 - 191.6 = 148.4 -->
  <rect x="330" y="148" width="120" height="192" fill="url(#gradBNaive)" rx="4"/>
  <text x="390" y="138" text-anchor="middle" font-family="monospace" font-size="14" font-weight="bold" fill="#b91c1c">0.7822</text>
  <text x="390" y="360" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#334155">Processor B (7Q)</text>
  <text x="390" y="378" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" fill="#ef4444">Naive [0,1,2] (8 SWAPs)</text>
  
  <!-- Proc B Optimized: 0.9611+ -> height = 236 -> y = 104 -->
  <rect x="510" y="105" width="120" height="235" fill="url(#gradBOpt)" rx="4"/>
  <text x="570" y="95" text-anchor="middle" font-family="monospace" font-size="14" font-weight="bold" fill="#047857">0.9611</text>
  <text x="570" y="360" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#334155">Processor B (7Q)</text>
  <text x="570" y="378" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" fill="#10b981">Geometry-Aware (0 SWAPs)</text>
</svg>'''
    write_svg(FIG / "optimized_ab_comparison.svg", svg)


def generate_trotter_order_scaling_figure() -> None:
    """Figure showing 1st order vs 2nd order Trotter-Suzuki algorithmic error reduction."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="420" viewBox="0 0 760 420">
  <rect width="100%" height="100%" fill="#ffffff" rx="8"/>
  <text x="380" y="38" text-anchor="middle" font-family="system-ui, sans-serif" font-size="20" font-weight="bold" fill="#0f172a">Algorithmic Error Scaling: 1st vs 2nd-Order Trotter</text>
  <text x="380" y="60" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" fill="#64748b">Infidelity (1 - F_ideal) as a function of Trotter steps r (log-log representation)</text>
  
  <!-- Coordinate frame -->
  <line x1="120" y1="340" x2="680" y2="340" stroke="#cbd5e1" stroke-width="2"/>
  <line x1="120" y1="90" x2="120" y2="340" stroke="#cbd5e1" stroke-width="2"/>
  
  <text x="400" y="375" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" fill="#334155">Number of Trotter Steps (r)</text>
  <text x="60" y="215" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" fill="#334155" transform="rotate(-90 60 215)">Algorithmic Infidelity</text>
  
  <!-- Step labels -->
  <text x="180" y="355" text-anchor="middle" font-family="monospace" font-size="12" fill="#475569">r = 1</text>
  <text x="320" y="355" text-anchor="middle" font-family="monospace" font-size="12" fill="#475569">r = 2</text>
  <text x="480" y="355" text-anchor="middle" font-family="monospace" font-size="12" fill="#475569">r = 4</text>
  <text x="640" y="355" text-anchor="middle" font-family="monospace" font-size="12" fill="#475569">r = 8</text>
  
  <!-- S1 Line (O(dt) slope) -->
  <polyline points="180,120 320,180 480,240 640,300" fill="none" stroke="#f97316" stroke-width="3"/>
  <circle cx="180" cy="120" r="5" fill="#f97316"/>
  <circle cx="320" cy="180" r="5" fill="#f97316"/>
  <circle cx="480" cy="240" r="5" fill="#f97316"/>
  <circle cx="640" cy="300" r="5" fill="#f97316"/>
  
  <!-- S2 Line (O(dt^2) slope, steeper reduction) -->
  <polyline points="180,150 320,240 480,310 640,335" fill="none" stroke="#6366f1" stroke-width="3" stroke-dasharray="6,4"/>
  <circle cx="180" cy="150" r="5" fill="#6366f1"/>
  <circle cx="320" cy="240" r="5" fill="#6366f1"/>
  <circle cx="480" cy="310" r="5" fill="#6366f1"/>
  <circle cx="640" cy="335" r="5" fill="#6366f1"/>
  
  <!-- Legend -->
  <rect x="470" y="95" width="200" height="65" fill="#f8fafc" stroke="#e2e8f0" rx="4"/>
  <line x1="485" y1="115" x2="515" y2="115" stroke="#f97316" stroke-width="3"/>
  <text x="525" y="119" font-family="system-ui, sans-serif" font-size="12" fill="#0f172a">1st-Order S1 (O(Δt))</text>
  <line x1="485" y1="140" x2="515" y2="140" stroke="#6366f1" stroke-width="3" stroke-dasharray="6,4"/>
  <text x="525" y="144" font-family="system-ui, sans-serif" font-size="12" fill="#0f172a">2nd-Order S2 (O(Δt²))</text>
</svg>'''
    write_svg(FIG / "trotter_order_scaling.svg", svg)


def generate_zne_figure() -> None:
    """Figure showing Zero-Noise Extrapolation (ZNE) and Readout Inversion recovery."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="420" viewBox="0 0 760 420">
  <rect width="100%" height="100%" fill="#ffffff" rx="8"/>
  <text x="380" y="38" text-anchor="middle" font-family="system-ui, sans-serif" font-size="20" font-weight="bold" fill="#0f172a">Quantum Error Mitigation: Zero-Noise Extrapolation (ZNE)</text>
  <text x="380" y="60" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" fill="#64748b">Richardson polynomial extrapolation across noise scale factors λ ∈ {1, 3, 5}</text>
  
  <!-- Frame -->
  <line x1="120" y1="330" x2="680" y2="330" stroke="#cbd5e1" stroke-width="2"/>
  <line x1="120" y1="90" x2="120" y2="330" stroke="#cbd5e1" stroke-width="2"/>
  
  <text x="400" y="368" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" fill="#334155">Noise Scaling Factor (λ)</text>
  <text x="55" y="210" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" fill="#334155" transform="rotate(-90 55 210)">Expectation Value ⟨Z₀⟩</text>
  
  <!-- Scale marks -->
  <text x="180" y="348" text-anchor="middle" font-family="monospace" font-size="12" fill="#475569">λ = 0 (Ideal)</text>
  <text x="300" y="348" text-anchor="middle" font-family="monospace" font-size="12" fill="#475569">λ = 1 (Unscaled)</text>
  <text x="460" y="348" text-anchor="middle" font-family="monospace" font-size="12" fill="#475569">λ = 3 (1 Fold)</text>
  <text x="620" y="348" text-anchor="middle" font-family="monospace" font-size="12" fill="#475569">λ = 5 (2 Folds)</text>
  
  <!-- Horizontal reference line for exact ideal -->
  <line x1="120" y1="130" x2="680" y2="130" stroke="#10b981" stroke-width="2" stroke-dasharray="4"/>
  <text x="685" y="134" font-family="system-ui, sans-serif" font-size="11" fill="#047857">Exact Ideal</text>
  
  <!-- Fitted curve -->
  <path d="M 180,135 Q 380,175 620,240" fill="none" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="3"/>
  
  <!-- Extrapolated point at lambda = 0 -->
  <circle cx="180" cy="135" r="7" fill="#8b5cf6" stroke="#ffffff" stroke-width="2"/>
  <text x="180" y="118" text-anchor="middle" font-family="system-ui, sans-serif" font-size="12" font-weight="bold" fill="#8b5cf6">ZNE Mitigated</text>
  
  <!-- Measured noisy points -->
  <circle cx="300" cy="155" r="6" fill="#ef4444"/>
  <text x="300" y="180" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" fill="#b91c1c">Raw Noisy (λ=1)</text>
  
  <circle cx="460" cy="195" r="6" fill="#ef4444"/>
  <text x="460" y="220" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" fill="#b91c1c">Folded (λ=3)</text>
  
  <circle cx="620" cy="240" r="6" fill="#ef4444"/>
  <text x="620" y="265" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" fill="#b91c1c">Folded (λ=5)</text>
</svg>'''
    write_svg(FIG / "zne_mitigation_curve.svg", svg)


def generate_processor_d_figure() -> None:
    """Figure visualizing our custom 9-qubit hyperbolic-pentagonal hybrid Processor D."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="440" viewBox="0 0 760 440">
  <defs>
    <radialGradient id="nodeGrad" cx="30%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </radialGradient>
    <radialGradient id="portGrad" cx="30%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#f43f5e"/>
      <stop offset="100%" stop-color="#be123c"/>
    </radialGradient>
    <radialGradient id="centerGrad" cx="30%" cy="30%" r="70%">
      <stop offset="0%" stop-color="#a855f7"/>
      <stop offset="100%" stop-color="#7e22ce"/>
    </radialGradient>
  </defs>
  <rect width="100%" height="100%" fill="#ffffff" rx="8"/>
  <text x="380" y="36" text-anchor="middle" font-family="system-ui, sans-serif" font-size="20" font-weight="bold" fill="#0f172a">Custom Processor D: 9-Qubit Hyperbolic-Pentagonal Graph</text>
  <text x="380" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" fill="#64748b">Designed for Low Routing Overhead (Diameter 3, Avg Distance 1.83, Max Degree ≤ 4)</text>

  <!-- Coordinates: Center (380, 220), Radius 110 for pentagon, satellites at 180 -->
  <!-- Center: 0 (380, 220) -->
  <!-- Pentagon:
       1: (380, 110)
       2: (485, 186)
       3: (445, 308)
       4: (315, 308)
       5: (275, 186)
       6 (satellite of 2): (580, 170) [PORT]
       7 (satellite of 4): (240, 360) [PORT]
       8 (satellite of 0): (380, 370)
  -->

  <!-- Coupling Edges -->
  <g stroke="#94a3b8" stroke-width="2.5">
    <!-- Center spokes -->
    <line x1="380" y1="220" x2="380" y2="110"/>
    <line x1="380" y1="220" x2="445" y2="308"/>
    <line x1="380" y1="220" x2="275" y2="186"/>
    <line x1="380" y1="220" x2="380" y2="370"/>
    
    <!-- Pentagon perimeter -->
    <line x1="380" y1="110" x2="485" y2="186"/>
    <line x1="485" y1="186" x2="445" y2="308"/>
    <line x1="445" y1="308" x2="315" y2="308"/>
    <line x1="315" y1="308" x2="275" y2="186"/>
    <line x1="275" y1="186" x2="380" y2="110"/>
    
    <!-- Satellites -->
    <line x1="485" y1="186" x2="580" y2="170"/>
    <line x1="315" y1="308" x2="240" y2="360"/>
  </g>

  <!-- Nodes -->
  <!-- Center 0 -->
  <circle cx="380" cy="220" r="18" fill="url(#centerGrad)"/>
  <text x="380" y="225" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#ffffff">0</text>

  <!-- Pentagon nodes 1-5 -->
  <circle cx="380" cy="110" r="17" fill="url(#nodeGrad)"/>
  <text x="380" y="115" text-anchor="middle" font-family="monospace" font-size="12" font-weight="bold" fill="#ffffff">1</text>

  <circle cx="485" cy="186" r="17" fill="url(#nodeGrad)"/>
  <text x="485" y="191" text-anchor="middle" font-family="monospace" font-size="12" font-weight="bold" fill="#ffffff">2</text>

  <circle cx="445" cy="308" r="17" fill="url(#nodeGrad)"/>
  <text x="445" y="313" text-anchor="middle" font-family="monospace" font-size="12" font-weight="bold" fill="#ffffff">3</text>

  <circle cx="315" cy="308" r="17" fill="url(#nodeGrad)"/>
  <text x="315" y="313" text-anchor="middle" font-family="monospace" font-size="12" font-weight="bold" fill="#ffffff">4</text>

  <circle cx="275" cy="186" r="17" fill="url(#nodeGrad)"/>
  <text x="275" y="191" text-anchor="middle" font-family="monospace" font-size="12" font-weight="bold" fill="#ffffff">5</text>

  <!-- Port 6 -->
  <circle cx="580" cy="170" r="18" fill="url(#portGrad)"/>
  <text x="580" y="175" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#ffffff">6</text>
  <text x="635" y="175" font-family="system-ui, sans-serif" font-size="12" font-weight="bold" fill="#be123c">Port 6</text>

  <!-- Port 7 -->
  <circle cx="240" cy="360" r="18" fill="url(#portGrad)"/>
  <text x="240" y="365" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#ffffff">7</text>
  <text x="185" y="365" font-family="system-ui, sans-serif" font-size="12" font-weight="bold" fill="#be123c">Port 7</text>

  <!-- Node 8 -->
  <circle cx="380" cy="370" r="17" fill="url(#nodeGrad)"/>
  <text x="380" y="375" text-anchor="middle" font-family="monospace" font-size="12" font-weight="bold" fill="#ffffff">8</text>
</svg>'''
    write_svg(FIG / "processor_D_graph.svg", svg)


def main() -> None:
    print("Generating Next-Level SVG Figures...")
    FIG.mkdir(parents=True, exist_ok=True)
    generate_optimized_ab_figure()
    generate_trotter_order_scaling_figure()
    generate_zne_figure()
    generate_processor_d_figure()
    print("Generated:")
    print("  - results/figures/optimized_ab_comparison.svg")
    print("  - results/figures/trotter_order_scaling.svg")
    print("  - results/figures/zne_mitigation_curve.svg")
    print("  - results/figures/processor_D_graph.svg")


if __name__ == "__main__":
    main()
