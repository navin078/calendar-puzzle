"""Instance 1 DateMapper.

Handles mapping of Month, Day of month, and Day of week for Instance 1 calendar grid.
"""

import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

Coordinate = Tuple[int, int]


class DateMapper:
    """Maps month, day of month, and day of week to Instance 1 board coordinates."""

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
