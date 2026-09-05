"""Unit tests for Calendar Puzzle Solver."""

from pathlib import Path
from solver import CalendarSolver


def test_instance1_date_mapper():
    instance_dir = Path(__file__).parent / "instance1"
    solver = CalendarSolver(instance_dir)
    assert solver.date_mapper is not None, "DateMapper should be loaded for instance1"

    # Test Aug 17, Mon
    coords = solver.date_mapper.get_coordinates("AUG", 17, "MON")
    assert coords == [(1, 1), (4, 2), (6, 4)]

    # Test Dec 31, Sun
    coords = solver.date_mapper.get_coordinates("DEC", 31, "SUN")
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


def test_solve_one_helper():
    instance_dir = Path(__file__).parent / "instance1"
    solver = CalendarSolver(instance_dir)
    target_coords = [(1, 1), (4, 2), (6, 4)]
    sol = solver.solve_one(target_coords)
    assert sol is not None
    assert len(sol) == 10


def test_color_adjacent_solving():
    instance_dir = Path(__file__).parent / "instance1"
    solver = CalendarSolver(instance_dir)
    target_coords = [(1, 1), (4, 2), (6, 4)]

    # Test that color-adjacent solver finds valid solutions
    sol = solver.solve_one(target_coords, require_color_adjacency=True)
    assert sol is not None, "Should find a color-adjacent solution for Aug 17, Mon"
    assert solver.is_color_adjacent(sol, diagonal=False), "All color pairs must touch edge-to-edge"
