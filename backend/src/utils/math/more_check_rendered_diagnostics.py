import pandas as pd
from pathlib import Path

csv_path = Path(r"C:\Development\chi-portfolio\backend\data\math\rendered_tex_diagnostics.csv")

df = pd.read_csv(csv_path)

print(
    df[["concept_id", "title", "matched_pattern", "rendered_excerpt"]]
    .to_string(index=False)
)