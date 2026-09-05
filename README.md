# Calendar Puzzle Solver

A fast, flexible computational solver for the daily physical **Calendar Polyomino Puzzle**.

Given any combination of **Month**, **Day of the Month**, and **Day of the Week**, this program arranges the physical puzzle pieces to cover every playable cell on the board while leaving **only** the 3 target date cells exposed.

The architecture is **completely decoupled and instance-agnostic**: solver algorithms are generic, while board layouts, pieces, orientations, color pairings, display representations, and date mappers live inside instance-specific directories (e.g. `instance1/`).

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

## 🎨 Physical Pieces & Color Pairings (Instance 1)

The puzzle uses **10 polyomino pieces** grouped into **5 colors** (2 pieces per color), totaling **47 cells** (exactly $50 - 3 = 47$ cells to cover):

| Color | Pieces | Shapes & IDs | Cells | Unique Orientations |
|:---|:---|:---:|:---:|:---:|
| ⚪ **White** | `L` (Tetromino) & `Flat L` (Pentomino) | `L` & `V` | 4 + 5 = 9 | 8 + 4 = 12 |
| 🟠 **Orange** | `Big L` (Pentomino) & `I` (Tetromino) | `B` & `I` | 5 + 4 = 9 | 8 + 2 = 10 |
| 🟡 **Yellow** | `S` (Pentomino) & `P` (Pentomino) | `S` & `P` | 5 + 5 = 10 | 4 + 8 = 12 |
| 🔴 **Red** | `T` (Pentomino) & `Big Z` (Pentomino) | `T` & `N` | 5 + 5 = 10 | 4 + 8 = 12 |
| 🟣 **Purple** | `U` (Pentomino) & `Z` (Tetromino) | `U` & `Z` | 5 + 4 = 9 | 4 + 4 = 8 |
| **Total** | **5 Color Pairs** | **10 Pieces** | **47 Cells** | **54 Orientations** |

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

---

## 🚀 Quick Start (Solver)

### 1. Solve for Today's Date
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

### 3. Solve with Color-Pair Adjacency Constraint (`--color-adjacent`)
Requires that both pieces of each color touch each other edge-to-edge on the board:
```bash
python3 solver.py --month AUG --day 17 --weekday MON --color-adjacent
```

Sample ASCII Output:
```
Solving for Target: AUG 17, MON [instance1] [Color-Adjacent]
Target coordinates: [(1, 1), (4, 2), (6, 4)]

Found 1 solution(s) in 153.55 ms:

+---+---+---+---+---+---+---+
| I | P | P | P | S | S |   |
+---+---+---+---+---+---+---+
| I |AUG| P | P | B | S |   |
+---+---+---+---+---+---+---+
| I | B | B | B | B | S | S |
+---+---+---+---+---+---+---+
| I | N | N | N | L | L | L |
+---+---+---+---+---+---+---+
| U | U |17 | N | N | T | L |
+---+---+---+---+---+---+---+
| U | Z | Z | T | T | T | V |
+---+---+---+---+---+---+---+
| U | U | Z | Z |MON| T | V |
+---+---+---+---+---+---+---+
|   |   |   |   | V | V | V |
+---+---+---+---+---+---+---+

Pieces Legend: L=L, B=Big L, I=I, U=U, P=P, T=T, Z=Z, N=Big Z, S=S, V=Flat L

Color Pairs Status:
  - White   (L=L & V=Flat L): ✓ Touching (Edge)
  - Orange  (B=Big L & I=I): ✓ Touching (Edge)
  - Yellow  (S=S & P=P): ✓ Touching (Edge)
  - Red     (T=T & N=Big Z): ✓ Touching (Edge)
  - Purple  (U=U & Z=Z): ✓ Touching (Edge)
```

### 4. Find Multiple or All Solutions
To see $N$ distinct solutions:
```bash
python3 solver.py --month AUG --day 17 --weekday MON --limit 3
```

To count all solutions under standard or color-adjacent mode:
```bash
# All standard solutions (e.g. 866 solutions for Aug 17, Mon)
python3 solver.py --month AUG --day 17 --weekday MON --all

# All color-adjacent solutions (e.g. 6 solutions for Aug 17, Mon)
python3 solver.py --month AUG --day 17 --weekday MON --color-adjacent --all
```

---

## 🧪 Testing & Verification

Run the test suite:
```bash
python3 -c "import test_solver; test_solver.test_instance1_date_mapper(); test_solver.test_solver_aug_17_mon(); test_solver.test_solve_one_helper(); test_solver.test_color_adjacent_solving(); print('All tests passed!')"
```

---

## 📁 Project Structure

```
calendar-puzzle/
├── README.md                  # Project documentation & guides
├── .gitignore                 # Git ignore rules
├── solver.py                  # Generic backtracking solver & CLI (with color pruning)
├── generate_orientations.py   # Computes D4 rotations/reflections and display IDs
├── test_solver.py             # Validation, constraint, and color-adjacency tests
├── docs/
│   └── puzzle.txt             # Initial puzzle description & conjecture specification
└── instance1/                 # Data and mapping definitions for Instance 1
    ├── calendar.json          # 8x7 board binary matrix and label mappings
    ├── base_shapes.json       # 10 base piece 2D matrices
    ├── colors.json            # 5 color pair definitions
    ├── orientations.json      # 54 precomputed static orientations & display IDs
    └── date_mapper.py         # Instance 1 specific date-to-coordinate mapping
```
