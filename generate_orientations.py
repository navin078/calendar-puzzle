"""Generate all unique rotations and reflections (flips) for base shapes.

Computes the full dihedral symmetry group (D4: 4 rotations x 2 reflections)
and deduplicates identical configurations. Also manages display character mappings.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

Matrix = List[List[int]]

# Default single-character display IDs for Instance 1 shapes (can be customized)
INSTANCE1_DISPLAY_IDS = {
    "L": "L",
    "Big L": "B",
    "I": "I",
    "U": "U",
    "P": "P",
    "T": "T",
    "Z": "Z",
    "Big Z": "N",
    "S": "S",
    "Flat L": "V",
}


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


def generate_display_ids(shape_names: List[str], custom_ids: Dict[str, str] = None) -> Dict[str, str]:
    """Generate unique 1-character display IDs for each shape name."""
    display_ids = {}
    used_chars = set()

    # Apply custom overrides first if provided
    if custom_ids:
        for name, char in custom_ids.items():
            if name in shape_names and char not in used_chars:
                display_ids[name] = char
                used_chars.add(char)

    for name in shape_names:
        if name in display_ids:
            continue
        # Try characters from the name
        assigned = None
        for char in name.upper():
            if char.isalnum() and char not in used_chars:
                assigned = char
                break
        # Fallback to letters A-Z
        if assigned is None:
            for code in range(ord('A'), ord('Z') + 1):
                char = chr(code)
                if char not in used_chars:
                    assigned = char
                    break
        if assigned is None:
            assigned = "?"

        display_ids[name] = assigned
        used_chars.add(assigned)

    return display_ids


def process_instance(instance_dir: Path):
    """Process base_shapes.json in an instance folder and write orientations.json."""
    base_shapes_path = instance_dir / "base_shapes.json"
    output_path = instance_dir / "orientations.json"

    if not base_shapes_path.exists():
        raise FileNotFoundError(f"Missing base shapes file: {base_shapes_path}")

    with open(base_shapes_path, "r") as f:
        base_shapes_raw = json.load(f)

    # Support both {"shape_name": matrix} and {"shape_name": {"display_id": "X", "matrix": matrix}}
    base_shapes: Dict[str, Matrix] = {}
    custom_display_ids: Dict[str, str] = {}

    for name, data in base_shapes_raw.items():
        if isinstance(data, dict) and "matrix" in data:
            base_shapes[name] = data["matrix"]
            if "display_id" in data:
                custom_display_ids[name] = data["display_id"]
        else:
            base_shapes[name] = data
            if instance_dir.name == "instance1" and name in INSTANCE1_DISPLAY_IDS:
                custom_display_ids[name] = INSTANCE1_DISPLAY_IDS[name]

    display_ids = generate_display_ids(list(base_shapes.keys()), custom_display_ids)

    all_orientations = {}
    print(f"Generating orientations for {len(base_shapes)} shapes in [{instance_dir.name}]:\n")

    total_orientations = 0
    for shape_name, matrix in base_shapes.items():
        orientations = get_all_orientations(matrix)
        all_orientations[shape_name] = orientations
        total_orientations += len(orientations)
        char = display_ids[shape_name]
        print(f"  - [{char}] {shape_name:10s}: {len(orientations)} unique orientations")

    print(f"\nTotal unique orientations across all shapes: {total_orientations}")

    payload = {
        "display_ids": display_ids,
        "shapes": all_orientations,
    }

    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Successfully saved to: {output_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Generate shape orientations and display mappings.")
    parser.add_argument(
        "--instance",
        type=str,
        default="instance1",
        help="Instance directory name (e.g. instance1). Defaults to 'instance1'."
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    instance_dir = project_root / args.instance

    if not instance_dir.exists():
        print(f"Error: Directory {instance_dir} does not exist.")
        return

    process_instance(instance_dir)


if __name__ == "__main__":
    main()
