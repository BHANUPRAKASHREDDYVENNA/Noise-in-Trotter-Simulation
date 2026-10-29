from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.online_ab import run_source_ab  # noqa: E402


def run_benchmark() -> pd.DataFrame:
    return run_source_ab(ROOT / "data" / "practice_config.json")


def main() -> None:
    df = run_benchmark()
    output = ROOT / "results" / "tables"
    output.mkdir(parents=True, exist_ok=True)
    df.to_csv(output / "practice_ab_comparison.csv", index=False)

    for _, row in df.iterrows():
        key = row["processor"]
        pd.DataFrame([row]).to_csv(
            output / f"practice_processor_{key}_metrics.csv",
            index=False,
        )

    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
