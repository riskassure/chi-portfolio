import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[3]  # backend/src
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import MATH_DATA_DIR


csv_path = MATH_DATA_DIR / "rendered_tex_diagnostics.csv"

print("Reading:", csv_path)

df = pd.read_csv(csv_path)

print("Total flagged rows:", len(df))
print()

if df.empty:
    print("No diagnostic issues found.")
else:
    print("Findings by issue type:")
    print(df["issue_type"].value_counts())
    print()
    print("Unique concepts flagged:", df["concept_id"].nunique())

    for issue_type, group in df.groupby("issue_type"):
        print("\n" + "=" * 80)
        print(issue_type)
        print("=" * 80)

        sample = (
            group[["concept_id", "title", "matched_pattern"]]
            .drop_duplicates()
            .head(20)
        )

        for _, row in sample.iterrows():
            print(f'{row["concept_id"]}: {row["title"]}  |  {row["matched_pattern"]}')