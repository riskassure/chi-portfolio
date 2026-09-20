"""Convert outlined Knot Atlas diagrams to single-line PNG diagrams."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def narrow_enclosed_regions(image: np.ndarray, maximum_radius: int = 8) -> np.ndarray:
    """Return narrow light regions enclosed by the black ribbon outlines."""
    light = image > 0
    height, width = light.shape
    distance = np.full((height, width), height + width, dtype=np.int32)
    queue: deque[tuple[int, int]] = deque()

    for y, x in zip(*np.where(~light)):
        distance[y, x] = 0
        queue.append((int(y), int(x)))

    while queue:
        y, x = queue.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if not (0 <= ny < height and 0 <= nx < width):
                continue
            if distance[ny, nx] > distance[y, x] + 1:
                distance[ny, nx] = distance[y, x] + 1
                queue.append((ny, nx))

    selected = np.zeros_like(light)
    visited = np.zeros_like(light)

    for start_y in range(height):
        for start_x in range(width):
            if not light[start_y, start_x] or visited[start_y, start_x]:
                continue

            component = [(start_y, start_x)]
            visited[start_y, start_x] = True
            cursor = 0
            while cursor < len(component):
                y, x = component[cursor]
                cursor += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and light[ny, nx]
                        and not visited[ny, nx]
                    ):
                        visited[ny, nx] = True
                        component.append((ny, nx))

            if len(component) < 250:
                continue
            if max(distance[y, x] for y, x in component) > maximum_radius:
                continue
            for y, x in component:
                selected[y, x] = True

    return selected


def skeletonize(mask: np.ndarray) -> np.ndarray:
    """Thin a binary mask with the Zhang-Suen skeletonization algorithm."""
    pixels = mask.astype(np.uint8)

    while True:
        changed = False
        for second_pass in (False, True):
            padded = np.pad(pixels, 1)
            p2 = padded[:-2, 1:-1]
            p3 = padded[:-2, 2:]
            p4 = padded[1:-1, 2:]
            p5 = padded[2:, 2:]
            p6 = padded[2:, 1:-1]
            p7 = padded[2:, :-2]
            p8 = padded[1:-1, :-2]
            p9 = padded[:-2, :-2]

            neighbors = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            transitions = np.stack(
                (
                    (p2 == 0) & (p3 == 1),
                    (p3 == 0) & (p4 == 1),
                    (p4 == 0) & (p5 == 1),
                    (p5 == 0) & (p6 == 1),
                    (p6 == 0) & (p7 == 1),
                    (p7 == 0) & (p8 == 1),
                    (p8 == 0) & (p9 == 1),
                    (p9 == 0) & (p2 == 1),
                )
            ).sum(axis=0)

            if second_pass:
                side_one = p2 * p4 * p8
                side_two = p2 * p6 * p8
            else:
                side_one = p2 * p4 * p6
                side_two = p4 * p6 * p8

            remove = (
                (pixels == 1)
                & (neighbors >= 2)
                & (neighbors <= 6)
                & (transitions == 1)
                & (side_one == 0)
                & (side_two == 0)
            )
            if np.any(remove):
                pixels[remove] = 0
                changed = True

        if not changed:
            return pixels.astype(bool)


def convert(source: Path, target: Path) -> None:
    source_image = np.asarray(Image.open(source).convert("L"))
    centerlines = skeletonize(narrow_enclosed_regions(source_image))

    output = Image.fromarray(np.where(centerlines, 0, 255).astype(np.uint8), "L")
    output = output.filter(ImageFilter.MinFilter(3))
    output = output.resize((720, 720), Image.Resampling.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    output.save(target, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    arguments = parser.parse_args()
    convert(arguments.source, arguments.target)


if __name__ == "__main__":
    main()
