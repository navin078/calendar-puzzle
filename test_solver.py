"""Unit tests for Calendar Puzzle Solver."""

from pathlib import Path
from solver import CalendarSolver, DateMapper


def test_date_mapper():
    instance_dir = Path(__file__).parent / "instance1"
    solver = CalendarSolver(instance_dir)
    mapper = solver.date_mapper

    # Test Aug 17, Mon
    coords = mapper.get_coordinates("AUG", 17, "MON")
    assert coords == [(1, 1), (4, 2), (6, 4)]

    # Test Dec 31, Sun
    coords = mapper.get_coordinates("DEC", 31, "SUN")
    assert coords == [(1, 5), (6, 2), (6, 3)]


def test_solver_aug_17_mon():
    instance_dir = Path(__file__).parent / "instance1"
    solver = CalendarSolver(instance_dir)

    target_coords = [(1, 1), (4, 2), (6, 4)]
    solutions = solver.solve(target_coords, max_solutions=5)

    assert len(solutions) > 0, "Should find at least one solution for Aug 17, Mon"

    # Verify properties of the first solution
    sol = solutions[0]
    # Check that all 10 shapes are placed
    assert len(sol) == 10

    # Check that no shape overlaps and targets are uncovered
    covered_cells = set()
    for shape_name, coords in sol.items():
        for r, c in coords:
            assert (r, c) not in covered_cells, f"Overlap detected at ({r}, {c})"
            assert (r, c) not in target_coords, f"Target cell covered at ({r}, {c})"
            covered_cells.add((r, c))

    # Total playable cells = 50, targets = 3, covered = 47
    assert len(covered_cells) == 47


def test_find_all_solutions_count():
    instance_dir = Path(__file__).parent / "instance1"
    solver = CalendarSolver(instance_dir)

    target_coords = [(1, 1), (4, 2), (6, 4)]
    all_solutions = solver.solve(target_coords, max_solutions=None)

    assert len(all_solutions) > 1, f"Expected multiple solutions, got {len(all_solutions)}"
    print(f"Total solutions for Aug 17, Mon: {len(all_solutions)}")
