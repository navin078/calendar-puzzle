"""Calendar Puzzle Solver.

A generic polyomino tiling backtracking solver. Instance-specific date mapping,
board layout, and shape display representations are loaded directly from the instance folder.
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

    def solve(
        self, target_coords: List[Coordinate], max_solutions: Optional[int] = None
    ) -> List[Dict[str, List[Coordinate]]]:
        """Find solutions for the given target coordinates."""
        return list(self.solve_generator(target_coords, max_solutions=max_solutions))

    def solve_one(self, target_coords: List[Coordinate]) -> Optional[Dict[str, List[Coordinate]]]:
        """Find and return the very first solution immediately."""
        for sol in self.solve_generator(target_coords, max_solutions=1):
            return sol
        return None

    def solve_generator(
        self, target_coords: List[Coordinate], max_solutions: Optional[int] = None
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
        self, solution: Dict[str, List[Coordinate]], target_coords: List[Coordinate]
    ) -> str:
        """Format a solution into a readable ASCII grid using instance-defined display IDs."""
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

    print(f"Solving for Target: {m_str} {d_str}, {w_str} [{args.instance}]")
    print(f"Target coordinates: {target_coords}\n")

    max_sol = None if args.all else (args.limit if args.limit else 1)

    start_time = time.perf_counter()
    solutions = solver.solve(target_coords, max_solutions=max_sol)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    if not solutions:
        print(f"No solution found for {m_str} {d_str}, {w_str} ({elapsed_ms:.2f} ms).")
        return

    print(f"Found {len(solutions)} solution(s) in {elapsed_ms:.2f} ms:\n")

    for idx, sol in enumerate(solutions, 1):
        if len(solutions) > 1:
            print(f"--- Solution #{idx} ---")
        print(solver.format_solution(sol, target_coords))
        print()


if __name__ == "__main__":
    main()
