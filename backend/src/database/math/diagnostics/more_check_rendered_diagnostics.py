import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import MATH_DATA_DIR


csv_path = MATH_DATA_DIR / "rendered_tex_diagnostics.csv"

df = pd.read_csv(csv_path)

if df.empty:
    print("No diagnostic issues found.")
else:
    columns = [
        "concept_id",
        "title",
        "matched_pattern",
        "rendered_excerpt",
    ]

    print(df[columns].to_string(index=False))