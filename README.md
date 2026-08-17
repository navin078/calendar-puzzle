# Calendar Puzzle Solver

A fast, flexible computational solver for the daily physical **Calendar Polyomino Puzzle**.

Given any combination of **Month**, **Day of the Month**, and **Day of the Week**, this program arranges the physical puzzle pieces to cover every playable cell on the board while leaving **only** the 3 target date cells exposed.

The architecture is **completely decoupled and instance-agnostic**: solver algorithms are generic, while board layouts, pieces, orientations, display representations, and date mappers live inside instance-specific directories (e.g. `instance1/`).

---

## 📅 Board Layout (Instance 1)

The standard puzzle board consists of an $8 \times 7$ grid containing **50 playable cells**:

```
+-----+-----+-----+-----+-----+-----+-----+
| JAN | FEB | MAR | APR | MAY | JUN |     |
+-----+-----+-----+-----+-----+-----+-----+
| JUL | AUG | SEP | OCT | NOV | DEC |     |
+-----+-----+-----+-----+-----+-----+-----+
|  1  |  2  |  3  |  4  |  5  |  6  |  7  |
+-----+-----+-----+-----+-----+-----+-----+
|  8  |  9  | 10  | 11  | 12  | 13  | 14  |
+-----+-----+-----+-----+-----+-----+-----+
| 15  | 16  | 17  | 18  | 19  | 20  | 21  |
+-----+-----+-----+-----+-----+-----+-----+
| 22  | 23  | 24  | 25  | 26  | 27  | 28  |
+-----+-----+-----+-----+-----+-----+-----+
| 29  | 30  | 31  | SUN | MON | TUE | WED |
+-----+-----+-----+-----+-----+-----+-----+
|     |     |     |     | THU | FRI | SAT |
+-----+-----+-----+-----+-----+-----+-----+
```

---

## 🧩 Physical Pieces (Instance 1)

The puzzle uses **10 polyomino pieces** totaling **47 cells** (exactly $50 - 3 = 47$ cells to cover):

| ID | Piece Name | Polyomino Type | Cells | Orientations (Rotations + Flips) |
|:---:|:---|:---|:---:|:---:|
| **L** | `L` | Tetromino | 4 | 8 |
| **B** | `Big L` | Pentomino | 5 | 8 |
| **I** | `I` | Tetromino | 4 | 2 |
| **U** | `U` | Pentomino | 5 | 4 |
| **P** | `P` | Pentomino | 5 | 8 |
| **T** | `T` | Pentomino | 5 | 4 |
| **Z** | `Z` | Tetromino | 4 | 4 |
| **N** | `Big Z` | Pentomino | 5 | 8 |
| **S** | `S` | Pentomino | 5 | 4 |
| **V** | `Flat L` (Corner) | Pentomino | 5 | 4 |
| **Total** | **10 Pieces** | | **47 Cells** | **54 Unique Orientations** |

---

## 🔄 Generating Shape Orientations (`generate_orientations.py`)

`generate_orientations.py` takes the base 2D shapes defined in an instance folder and automatically generates all unique orientations using the full dihedral symmetry group ($D_4$: 4 rotations $\times$ 2 reflections). It also manages single-character display IDs for visual board rendering and writes the result to `orientations.json`.

### Usage:
```bash
# Generate orientations for default instance (instance1)
python3 generate_orientations.py

# Generate orientations for a specific instance
python3 generate_orientations.py --instance instance1
```

### Adding a New Puzzle Variant / Instance:
1. Create a new folder (e.g. `instance2/`).
2. Add `calendar.json` (grid and labels) and `date_mapper.py`.
3. Add `base_shapes.json` containing 1 base 2D matrix per physical piece.
4. Run `python3 generate_orientations.py --instance instance2`.
5. Solve with `python3 solver.py --instance instance2`.

---

## 🚀 Quick Start (Solver)

### 1. Solve for Today's Date
By default, running without arguments solves for the current date:
```bash
python3 solver.py
```

### 2. Solve for a Specific Date
```bash
python3 solver.py --month AUG --day 17 --weekday MON
```

Or using an ISO date string:
```bash
python3 solver.py --date 2026-08-17
```

### 3. Stop at First Solution (Default / Fast)
```bash
python3 solver.py --month AUG --day 17 --weekday MON --one
```

Sample ASCII Output:
```
Solving for Target: AUG 17, MON [instance1]
Target coordinates: [(1, 1), (4, 2), (6, 4)]

Found 1 solution(s) in 1.21 ms:

+---+---+---+---+---+---+---+
| N | N | N | T | T | T |   |
+---+---+---+---+---+---+---+
| S |AUG| N | N | T | Z |   |
+---+---+---+---+---+---+---+
| S | S | S | L | T | Z | Z |
+---+---+---+---+---+---+---+
| B | B | S | L | L | L | Z |
+---+---+---+---+---+---+---+
| B | P |17 | I | I | I | I |
+---+---+---+---+---+---+---+
| B | P | P | U | U | U | V |
+---+---+---+---+---+---+---+
| B | P | P | U |MON| U | V |
+---+---+---+---+---+---+---+
|   |   |   |   | V | V | V |
+---+---+---+---+---+---+---+

Pieces Legend: L=L, B=Big L, I=I, U=U, P=P, T=T, Z=Z, N=Big Z, S=S, V=Flat L
```

### 4. Find Multiple or All Solutions
To see $N$ distinct solutions:
```bash
python3 solver.py --month AUG --day 17 --weekday MON --limit 3
```

To find and count **all** valid solutions:
```bash
python3 solver.py --month AUG --day 17 --weekday MON --all
```
*(e.g., Aug 17, Mon yields **866 distinct solutions** in ~1.2 seconds)*

---

## 🧪 Testing & Verification

Run the test suite:
```bash
python3 -c "import test_solver; test_solver.test_instance1_date_mapper(); test_solver.test_solver_aug_17_mon(); test_solver.test_solve_one_helper(); print('All tests passed!')"
```

---

## 📁 Project Structure

```
calendar-puzzle/
├── README.md                  # Project documentation & guides
├── .gitignore                 # Git ignore rules
├── solver.py                  # Generic, puzzle-agnostic backtracking solver & CLI
├── generate_orientations.py   # Computes D4 rotations/reflections and display IDs
├── test_solver.py             # Validation and constraint tests
├── docs/
│   └── puzzle.txt             # Initial puzzle description & conjecture specification
└── instance1/                 # Data and mapping definitions for Instance 1
    ├── calendar.json          # 8x7 board binary matrix and label mappings
    ├── base_shapes.json       # 10 base piece 2D matrices
    ├── orientations.json      # 54 precomputed static orientations & display IDs
    └── date_mapper.py         # Instance 1 specific date-to-coordinate mapping
```

---

## 💻 Python API

You can also use the solver as a library:

```python
from pathlib import Path
from solver import CalendarSolver

solver = CalendarSolver(Path("instance1"))
target_coords = solver.date_mapper.get_coordinates("AUG", 17, "MON")

# Find first solution
solution = solver.solve_one(target_coords)
print(solver.format_solution(solution, target_coords))

# Iterate over all solutions
for sol in solver.solve_generator(target_coords):
    # Process solution
    pass
```
