"""Calendar Puzzle Solver.

A generic polyomino tiling backtracking solver. Instance-specific date mapping,
board layout, shape display representations, and color pairings are loaded directly
from the instance folder.
"""

import argparse
import datetime
import importlib.util
import json
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

Coordinate = Tuple[int, int]
Board = List[List[int]]


def load_instance_date_mapper(instance_dir: Path, labels: List[List[Optional[str]]]) -> Optional[Any]:
    """Dynamically load the instance-specific DateMapper if present in the instance directory."""
    mapper_path = instance_dir / "date_mapper.py"
    if mapper_path.exists():
        spec = importlib.util.spec_from_file_location(f"{instance_dir.name}_date_mapper", mapper_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "DateMapper"):
                return module.DateMapper(labels)
    return None


def are_pieces_adjacent(
    coords1: List[Coordinate], coords2: List[Coordinate], diagonal: bool = False
) -> bool:
    """Check if two sets of cells touch (orthogonally by default, or diagonally)."""
    s2 = set(coords2)
    for r, c in coords1:
        neighbors = [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
        if diagonal:
            neighbors.extend([(r + 1, c + 1), (r + 1, c - 1), (r - 1, c + 1), (r - 1, c - 1)])
        for nr, nc in neighbors:
            if (nr, nc) in s2:
                return True
    return False


class CalendarSolver:
    """Generic backtracking solver for calendar polyomino puzzles."""

    def __init__(self, instance_dir: Path):
        self.instance_dir = instance_dir
        with open(instance_dir / "calendar.json", "r") as f:
            calendar_data = json.load(f)
            self.grid_template: List[List[int]] = calendar_data["grid"]
            self.labels: List[List[Optional[str]]] = calendar_data["labels"]

        with open(instance_dir / "orientations.json", "r") as f:
            orientations_data = json.load(f)

        if "shapes" in orientations_data and "display_ids" in orientations_data:
            self.raw_orientations: Dict[str, List[List[List[int]]]] = orientations_data["shapes"]
            self.shape_display_ids: Dict[str, str] = orientations_data["display_ids"]
        else:
            self.raw_orientations = orientations_data
            self.shape_display_ids = {k: k[0] for k in self.raw_orientations}

        # Load color pairs if present
        colors_path = instance_dir / "colors.json"
        self.color_pairs: Dict[str, List[str]] = {}
        self.shape_to_partner: Dict[str, str] = {}
        self.shape_to_color: Dict[str, str] = {}
        if colors_path.exists():
            with open(colors_path, "r") as f:
                self.color_pairs = json.load(f)
            for color, shapes in self.color_pairs.items():
                if len(shapes) == 2:
                    s1, s2 = shapes
                    self.shape_to_partner[s1] = s2
                    self.shape_to_partner[s2] = s1
                    self.shape_to_color[s1] = color
                    self.shape_to_color[s2] = color

        self.rows = len(self.grid_template)
        self.cols = len(self.grid_template[0])
        self.date_mapper = load_instance_date_mapper(instance_dir, self.labels)

        # Precompute normalized coordinate offsets for each orientation
        # For each orientation, we store offsets relative to its topmost-leftmost cell (0, 0).
        self.shape_offsets: Dict[str, List[List[Coordinate]]] = {}
        for shape_name, orientations in self.raw_orientations.items():
            self.shape_offsets[shape_name] = []
            for matrix in orientations:
                coords = []
                for r, row in enumerate(matrix):
                    for c, val in enumerate(row):
                        if val == 1:
                            coords.append((r, c))
                # Sort in reading order (top-to-bottom, left-to-right)
                coords.sort()
                # Shift so the first cell is at (0, 0)
                r0, c0 = coords[0]
                normalized = [(r - r0, c - c0) for r, c in coords]
                self.shape_offsets[shape_name].append(normalized)

        self.shape_names = list(self.shape_offsets.keys())

    def is_color_adjacent(
        self, solution: Dict[str, List[Coordinate]], diagonal: bool = False
    ) -> bool:
        """Verify that all same-colored piece pairs touch in the solution."""
        if not self.color_pairs:
            return True
        for color, shapes in self.color_pairs.items():
            if len(shapes) == 2:
                s1, s2 = shapes
                if s1 not in solution or s2 not in solution:
                    return False
                if not are_pieces_adjacent(solution[s1], solution[s2], diagonal=diagonal):
                    return False
        return True

    def solve(
        self,
        target_coords: List[Coordinate],
        max_solutions: Optional[int] = None,
        require_color_adjacency: bool = False,
        diagonal_adjacency: bool = False,
    ) -> List[Dict[str, List[Coordinate]]]:
        """Find solutions for the given target coordinates."""
        return list(
            self.solve_generator(
                target_coords,
                max_solutions=max_solutions,
                require_color_adjacency=require_color_adjacency,
                diagonal_adjacency=diagonal_adjacency,
            )
        )

    def solve_one(
        self,
        target_coords: List[Coordinate],
        require_color_adjacency: bool = False,
        diagonal_adjacency: bool = False,
    ) -> Optional[Dict[str, List[Coordinate]]]:
        """Find and return the very first solution immediately."""
        for sol in self.solve_generator(
            target_coords,
            max_solutions=1,
            require_color_adjacency=require_color_adjacency,
            diagonal_adjacency=diagonal_adjacency,
        ):
            return sol
        return None

    def solve_generator(
        self,
        target_coords: List[Coordinate],
        max_solutions: Optional[int] = None,
        require_color_adjacency: bool = False,
        diagonal_adjacency: bool = False,
    ) -> Generator[Dict[str, List[Coordinate]], None, None]:
        """Generator that yields solutions one by one using cell-first backtracking."""
        # Initialize board: 1 = empty playable cell, 0 = blocked / covered / out-of-bounds
        board = [row[:] for row in self.grid_template]

        # Target cells must remain uncovered (set to 0 so shapes cannot cover them)
        for r, c in target_coords:
            board[r][c] = 0

        placed_shapes: Dict[str, List[Coordinate]] = {}
        unused_shapes = set(self.shape_names)

        count = 0

        def find_first_empty_cell() -> Optional[Coordinate]:
            for r in range(self.rows):
                for c in range(self.cols):
                    if board[r][c] == 1:
                        return (r, c)
            return None

        def search() -> Generator[Dict[str, List[Coordinate]], None, None]:
            nonlocal count

            if max_solutions is not None and count >= max_solutions:
                return

            first_empty = find_first_empty_cell()

            # If no empty cells remain and all shapes are placed, we found a valid solution
            if first_empty is None:
                if len(unused_shapes) == 0:
                    count += 1
                    yield dict(placed_shapes)
                return

            r0, c0 = first_empty

            # Try every unused shape
            for shape_name in list(unused_shapes):
                unused_shapes.remove(shape_name)
                partner = self.shape_to_partner.get(shape_name)

                # Try every orientation of this shape
                for offsets in self.shape_offsets[shape_name]:
                    can_place = True
                    placed_cells = []
                    for dr, dc in offsets:
                        nr, nc = r0 + dr, c0 + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and board[nr][nc] == 1:
                            placed_cells.append((nr, nc))
                        else:
                            can_place = False
                            break

                    # Search-time pruning for color adjacency constraint
                    if can_place and require_color_adjacency and partner and (partner in placed_shapes):
                        if not are_pieces_adjacent(placed_cells, placed_shapes[partner], diagonal=diagonal_adjacency):
                            can_place = False

                    if can_place:
                        # Place the shape
                        for nr, nc in placed_cells:
                            board[nr][nc] = 0
                        placed_shapes[shape_name] = placed_cells

                        # Recurse
                        yield from search()

                        # Backtrack
                        for nr, nc in placed_cells:
                            board[nr][nc] = 1
                        del placed_shapes[shape_name]

                        if max_solutions is not None and count >= max_solutions:
                            break

                unused_shapes.add(shape_name)

                if max_solutions is not None and count >= max_solutions:
                    break

        yield from search()

    def format_solution(
        self,
        solution: Dict[str, List[Coordinate]],
        target_coords: List[Coordinate],
        show_colors: bool = False,
    ) -> str:
        """Format a solution into a readable ASCII grid with optional color pair status."""
        display_grid = [["." if self.grid_template[r][c] == 1 else " " for c in range(self.cols)]
                        for r in range(self.rows)]

        # Place shape identifiers
        for shape_name, coords in solution.items():
            char = self.shape_display_ids.get(shape_name, shape_name[0])
            for r, c in coords:
                display_grid[r][c] = char

        # Highlight target coordinates with their labels
        target_set = set(target_coords)
        lines = []
        lines.append("+" + "---+" * self.cols)
        for r in range(self.rows):
            row_str = "|"
            for c in range(self.cols):
                if (r, c) in target_set:
                    lbl = str(self.labels[r][c])
                    row_str += f"{lbl:^3}|"
                elif self.grid_template[r][c] == 0:
                    row_str += "   |"
                else:
                    char = display_grid[r][c]
                    row_str += f" {char} |"
            lines.append(row_str)
            lines.append("+" + "---+" * self.cols)

        # Legend
        legend_items = [f"{self.shape_display_ids.get(name, name[0])}={name}" for name in self.shape_names]
        lines.append("\nPieces Legend: " + ", ".join(legend_items))

        # Color Pairs Breakdown
        if self.color_pairs and show_colors:
            lines.append("\nColor Pairs Status:")
            for color, shapes in self.color_pairs.items():
                if len(shapes) == 2:
                    s1, s2 = shapes
                    d1 = self.shape_display_ids.get(s1, s1[0])
                    d2 = self.shape_display_ids.get(s2, s2[0])
                    if s1 in solution and s2 in solution:
                        edge_touch = are_pieces_adjacent(solution[s1], solution[s2], diagonal=False)
                        diag_touch = are_pieces_adjacent(solution[s1], solution[s2], diagonal=True)
                        if edge_touch:
                            status = "✓ Touching (Edge)"
                        elif diag_touch:
                            status = "~ Touching (Diagonal only)"
                        else:
                            status = "✗ Separated"
                    else:
                        status = "Unplaced"
                    lines.append(f"  - {color:7s} ({d1}={s1} & {d2}={s2}): {status}")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Calendar Puzzle Solver")
    parser.add_argument("--month", type=str, help="Target month (e.g. AUG or 8)")
    parser.add_argument("--day", type=int, help="Target day of month (1-31)")
    parser.add_argument("--weekday", type=str, help="Target day of week (e.g. MON)")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format (uses current date if none provided)")
    parser.add_argument("--one", "--first", action="store_true", help="Stop immediately at first solution and print ASCII grid (default)")
    parser.add_argument("--all", action="store_true", help="Find all solutions")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of solutions to find")
    parser.add_argument("--instance", type=str, default="instance1", help="Instance directory name")
    parser.add_argument(
        "--color-adjacent", "--color",
        action="store_true",
        help="Require pieces of the same color to touch each other"
    )
    parser.add_argument(
        "--diagonal",
        action="store_true",
        help="Allow diagonal/corner touching for color adjacency (default: orthogonal edge-sharing)"
    )

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    instance_path = project_root / args.instance

    if not instance_path.exists():
        print(f"Error: Instance directory {instance_path} not found.")
        return

    solver = CalendarSolver(instance_path)

    if solver.date_mapper is None:
        print(f"Error: No DateMapper found for instance {args.instance}.")
        return

    # Determine target
    if args.date:
        dt = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        target_coords, (m_str, d_str, w_str) = solver.date_mapper.from_date(dt)
    elif args.month and args.day and args.weekday:
        m_str, d_str, w_str = args.month.upper(), str(args.day), args.weekday.upper()
        target_coords = solver.date_mapper.get_coordinates(m_str, d_str, w_str)
    else:
        # Default to today's date
        today = datetime.date.today()
        target_coords, (m_str, d_str, w_str) = solver.date_mapper.from_date(today)

    mode_info = " [Color-Adjacent]" if args.color_adjacent else ""
    print(f"Solving for Target: {m_str} {d_str}, {w_str} [{args.instance}]{mode_info}")
    print(f"Target coordinates: {target_coords}\n")

    max_sol = None if args.all else (args.limit if args.limit else 1)

    start_time = time.perf_counter()
    solutions = solver.solve(
        target_coords,
        max_solutions=max_sol,
        require_color_adjacency=args.color_adjacent,
        diagonal_adjacency=args.diagonal,
    )
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    if not solutions:
        print(f"No solution found for {m_str} {d_str}, {w_str} with requested constraints ({elapsed_ms:.2f} ms).")
        return

    print(f"Found {len(solutions)} solution(s) in {elapsed_ms:.2f} ms:\n")

    for idx, sol in enumerate(solutions, 1):
        if len(solutions) > 1:
            print(f"--- Solution #{idx} ---")
        print(solver.format_solution(sol, target_coords, show_colors=bool(solver.color_pairs)))
        print()


if __name__ == "__main__":
    main()
