from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "main.ipynb"

EXPECTED_SECTIONS = [
    "1. How to Use This Notebook",
    "2. Phase 1 Challenge Overview",
    "3. Repository Structure",
    "4. Core Mental Model",
    "5. Quantum Foundations",
    "6. Processor as a Graph",
    "7. Bell-State Example",
    "8. Routing and SWAP Overhead",
    "9. Transpilation",
    "10. Noise",
    "11. Required Measurements",
    "12. Processor Definitions",
    "13. Problem Statement",
    "14. A/B Experiment",
    "15. A/B Comparison",
    "16. Protection / Error Detection",
    "17. Scientific Reporting",
    "18. Results and Figures",
    "19. Experience-Level Approaches",
    "20. Workflow Checklist",
    "21. Final Experiment Structure",
    "22. Submission Checklist",
    "23. Participant Lab Notes",
]


def verify() -> None:
    if not NOTEBOOK.is_file():
        raise SystemExit("main.ipynb is missing.")

    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    if notebook.get("nbformat") != 4:
        raise SystemExit("Notebook must use nbformat 4.")

    cells = notebook.get("cells")
    if not isinstance(cells, list) or not cells:
        raise SystemExit("Notebook has no cells.")

    markdown = "\n".join(
        "".join(cell.get("source", []))
        for cell in cells
        if cell.get("cell_type") == "markdown"
    )
    missing = [title for title in EXPECTED_SECTIONS if f"## {title}" not in markdown]
    if missing:
        raise SystemExit("Notebook is missing required sections: " + ", ".join(missing))

    for index, cell in enumerate(cells):
        if cell.get("cell_type") == "code":
            source = "".join(cell.get("source", []))
            try:
                ast.parse(source)
            except SyntaxError as exc:
                raise SystemExit(f"Notebook code cell {index} is invalid: {exc}") from exc

    raw = NOTEBOOK.read_text(encoding="utf-8").lower()
    forbidden = ("to" + "do", "fix" + "me", "implement " + "later")
    hits = [marker for marker in forbidden if marker in raw]
    if hits:
        raise SystemExit("Notebook contains incomplete-work markers: " + ", ".join(hits))

    print("Notebook verification passed.")


if __name__ == "__main__":
    verify()
