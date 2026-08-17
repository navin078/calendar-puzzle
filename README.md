# Calendar Puzzle Solver

A fast, flexible computational solver for the daily physical **Calendar Polyomino Puzzle**.

Given any combination of **Month**, **Day of the Month**, and **Day of the Week**, this program arranges the physical puzzle pieces to cover every playable cell on the board while leaving **only** the 3 target date cells exposed.

---

## 📅 Board Layout

The puzzle board consists of an $8 \times 7$ grid containing **50 playable cells**:

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

## 🧩 Physical Pieces

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

## 🚀 Quick Start

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
Solving for Target: AUG 17, MON
Target coordinates: [(1, 1), (4, 2), (6, 4)]

Found 1 solution(s) in 1.76 ms:

+---+---+---+---+---+---+---+
| I | I | I | I | B | N |   |
+---+---+---+---+---+---+---+
| L |AUG| P | P | B | N |   |
+---+---+---+---+---+---+---+
| L | P | P | P | B | N | N |
+---+---+---+---+---+---+---+
| L | L | S | S | B | B | N |
+---+---+---+---+---+---+---+
| U | U |17 | S | V | V | V |
+---+---+---+---+---+---+---+
| U | Z | Z | S | S | T | V |
+---+---+---+---+---+---+---+
| U | U | Z | Z |MON| T | V |
+---+---+---+---+---+---+---+
|   |   |   |   | T | T | T |
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
python3 -c "import test_solver; test_solver.test_date_mapper(); test_solver.test_solver_aug_17_mon(); print('All tests passed!')"
```

---

## 📁 Project Structure

```
calendar-puzzle/
├── README.md                  # Project documentation
├── .gitignore                 # Git ignore rules
├── solver.py                  # DateMapper, CalendarSolver, ASCII formatter & CLI
├── generate_orientations.py   # Computes 54 D4 rotations/reflections from base shapes
├── test_solver.py             # Validation and constraint tests
├── docs/
│   └── puzzle.txt             # Initial puzzle description & conjecture specification
└── instance1/                 # Data definitions for standard board
    ├── calendar.json          # 8x7 board binary matrix and label mappings
    ├── base_shapes.json       # 10 base piece 2D matrices
    └── orientations.json      # 54 precomputed static orientations
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
