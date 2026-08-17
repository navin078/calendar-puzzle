"""Calendar Puzzle Solver.

Supports finding a single solution or all solutions for a given date.
"""

import argparse
import datetime
import json
import time
from pathlib import Path
from typing import Dict, Generator, List, Optional, Set, Tuple

Coordinate = Tuple[int, int]
Board = List[List[int]]


class DateMapper:
    """Maps month, day of month, and day of week to board coordinates."""

    MONTHS = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
        "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
        "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12,
    }

    MONTH_NAMES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                   "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

    WEEKDAYS = {
        "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
        "SUNDAY": 0, "MONDAY": 1, "TUESDAY": 2, "WEDNESDAY": 3,
        "THURSDAY": 4, "FRIDAY": 5, "SATURDAY": 6,
    }

    WEEKDAY_NAMES = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]

    def __init__(self, labels: List[List[Optional[str]]]):
        self.labels = labels
        self.label_to_coord: Dict[str, Coordinate] = {}

        for r, row in enumerate(labels):
            for c, label in enumerate(row):
                if label is not None:
                    self.label_to_coord[str(label).upper()] = (r, c)

    def get_coordinates(self, month: str | int, day: str | int, weekday: str) -> List[Coordinate]:
        """Convert month, day, weekday to [(r, c), (r, c), (r, c)]."""
        # Normalize month
        if isinstance(month, int) or str(month).isdigit():
            m_idx = int(month) - 1
            if 0 <= m_idx < 12:
                m_str = self.MONTH_NAMES[m_idx]
            else:
                raise ValueError(f"Invalid month number: {month}")
        else:
            m_str = str(month).strip().upper()
            if m_str not in self.MONTH_NAMES:
                raise ValueError(f"Invalid month name: {month}")

        # Normalize day
        d_str = str(day).strip()
        if not (d_str.isdigit() and 1 <= int(d_str) <= 31):
            raise ValueError(f"Invalid day: {day}. Must be 1-31.")

        # Normalize weekday
        w_raw = str(weekday).strip().upper()
        if w_raw in self.WEEKDAYS:
            w_str = self.WEEKDAY_NAMES[self.WEEKDAYS[w_raw]]
        else:
            raise ValueError(f"Invalid weekday: {weekday}")

        coords = [
            self.label_to_coord[m_str],
            self.label_to_coord[d_str],
            self.label_to_coord[w_str],
        ]
        return coords

    def from_date(self, dt: datetime.date) -> Tuple[List[Coordinate], Tuple[str, str, str]]:
        """Get coordinates directly from a datetime.date object."""
        m_str = self.MONTH_NAMES[dt.month - 1]
        d_str = str(dt.day)
        # Python weekday: Monday=0 ... Sunday=6
        w_map = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        w_str = w_map[dt.weekday()]
        coords = self.get_coordinates(m_str, d_str, w_str)
        return coords, (m_str, d_str, w_str)


class CalendarSolver:
    """Backtracking solver for the calendar puzzle."""

    # Short display IDs for shapes
    SHAPE_DISPLAY_ID = {
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

    def __init__(self, instance_dir: Path):
        self.instance_dir = instance_dir
        with open(instance_dir / "calendar.json", "r") as f:
            calendar_data = json.load(f)
            self.grid_template: List[List[int]] = calendar_data["grid"]
            self.labels: List[List[Optional[str]]] = calendar_data["labels"]

        with open(instance_dir / "orientations.json", "r") as f:
            self.raw_orientations: Dict[str, List[List[List[int]]]] = json.load(f)

        self.rows = len(self.grid_template)
        self.cols = len(self.grid_template[0])
        self.date_mapper = DateMapper(self.labels)

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

    def solve_generator(
        self, target_coords: List[Coordinate], max_solutions: Optional[int] = None
    ) -> Generator[Dict[str, List[Coordinate]], None, None]:
        """Generator that yields solutions one by one."""
        # Initialize board: 1 = empty playable cell, 0 = blocked / covered / out-of-bounds
        board = [row[:] for row in self.grid_template]

        # Target cells must remain uncovered (set to 0 so shapes cannot cover them)
        for r, c in target_coords:
            board[r][c] = 0

        # Track placed shapes: shape_name -> list of board coordinates
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
                    # Check if all offsets fit on the board and cover empty cells
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
        """Format a solution into a readable ASCII grid."""
        display_grid = [["." if self.grid_template[r][c] == 1 else " " for c in range(self.cols)]
                        for r in range(self.rows)]

        # Place shape identifiers
        for shape_name, coords in solution.items():
            char = self.SHAPE_DISPLAY_ID.get(shape_name, shape_name[0])
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
        legend_items = [f"{self.SHAPE_DISPLAY_ID.get(name, name[0])}={name}" for name in self.shape_names]
        lines.append("\nPieces Legend: " + ", ".join(legend_items))
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Calendar Puzzle Solver")
    parser.add_argument("--month", type=str, help="Target month (e.g. AUG or 8)")
    parser.add_argument("--day", type=int, help="Target day of month (1-31)")
    parser.add_argument("--weekday", type=str, help="Target day of week (e.g. MON)")
    parser.add_argument("--date", type=str, help="Target date in YYYY-MM-DD format (uses current date if none provided)")
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

    print(f"Solving for Target: {m_str} {d_str}, {w_str}")
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
        print(f"--- Solution #{idx} ---")
        print(solver.format_solution(sol, target_coords))
        print()


if __name__ == "__main__":
    main()
