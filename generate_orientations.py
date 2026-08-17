"""Generate all unique rotations and reflections (flips) for base shapes."""

import json
from pathlib import Path
from typing import List

Matrix = List[List[int]]


def rotate_90(matrix: Matrix) -> Matrix:
    """Rotate a 2D matrix 90 degrees clockwise."""
    rows = len(matrix)
    cols = len(matrix[0])
    return [[matrix[rows - 1 - r][c] for r in range(rows)] for c in range(cols)]


def flip_horizontal(matrix: Matrix) -> Matrix:
    """Flip a 2D matrix horizontally (reverse each row)."""
    return [row[::-1] for row in matrix]


def get_all_orientations(base_matrix: Matrix) -> List[Matrix]:
    """
    Generate all unique orientations (rotations and flips).
    Applies 0°, 90°, 180°, 270° rotations to both original and flipped versions.
    """
    unique_orientations = []
    seen = set()

    versions = [base_matrix, flip_horizontal(base_matrix)]

    for version in versions:
        curr = version
        for _ in range(4):
            # Convert to tuple of tuples for hashing/deduplication
            curr_tuple = tuple(tuple(row) for row in curr)
            if curr_tuple not in seen:
                seen.add(curr_tuple)
                unique_orientations.append(curr)
            curr = rotate_90(curr)

    return unique_orientations


def main():
    base_dir = Path(__file__).resolve().parent
    base_shapes_path = base_dir / "instance1" / "base_shapes.json"
    output_path = base_dir / "instance1" / "orientations.json"

    with open(base_shapes_path, "r") as f:
        base_shapes = json.load(f)

    all_orientations = {}
    print(f"Generating orientations for {len(base_shapes)} shapes:\n")

    total_orientations = 0
    for shape_name, matrix in base_shapes.items():
        orientations = get_all_orientations(matrix)
        all_orientations[shape_name] = orientations
        total_orientations += len(orientations)
        print(f"  - {shape_name}: {len(orientations)} unique orientations")

    print(f"\nTotal orientations across all shapes: {total_orientations}")

    with open(output_path, "w") as f:
        json.dump(all_orientations, f, indent=2)

    print(f"Successfully saved orientations to: {output_path}")


if __name__ == "__main__":
    main()
