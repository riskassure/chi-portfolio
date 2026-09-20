"""Compile reconstructed legacy PlanetMath figures from LaTeX to SVG."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from build_knot_line_art import convert as build_knot_line_art


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n{result.stdout}\n{result.stderr}"
        )


def build(source_dir: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    with tempfile.TemporaryDirectory(prefix="legacy-math-") as temp_name:
        build_dir = Path(temp_name)

        for source in sorted(source_dir.glob("*.tex")):
            run(
                [
                    "latex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    f"-output-directory={build_dir}",
                    str(source),
                ],
                source_dir,
            )
            dvi = build_dir / f"{source.stem}.dvi"
            target = output_dir / f"{source.stem}.svg"
            run(
                ["dvisvgm", "--no-fonts", "--exact", "-o", str(target), str(dvi)],
                build_dir,
            )
            print(f"Built {target}")
            count += 1

        # A few restored historical diagrams are retained as their exact
        # source images because their crossing data is part of the content.
        for pattern in ("*.gif", "*.jpg", "*.jpeg", "*.png"):
            for source in sorted(source_dir.glob(pattern)):
                target = output_dir / source.name
                shutil.copy2(source, target)
                print(f"Copied {target}")
                count += 1

        for source_name, target_name in (
            ("knot10_89.gif", "knot10_89.png"),
            ("trefoil.gif", "trefoil.png"),
        ):
            source = source_dir / source_name
            if source.exists():
                target = output_dir / target_name
                build_knot_line_art(source, target)
                print(f"Built line diagram {target}")
                count += 1

    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    count = build(args.source_dir.resolve(), args.output_dir.resolve())
    print(f"Prepared {count} reconstructed legacy figures.")


if __name__ == "__main__":
    main()
