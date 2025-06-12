from dataclasses import dataclass
from enum import Enum, auto
from typing import NamedTuple


class BorderUnit(Enum):
    POINT = auto()
    RATIO = auto()


@dataclass(frozen=True)
class BorderSpec:
    value: float
    unit: BorderUnit

class FourBorders(NamedTuple):
    top: BorderSpec
    right: BorderSpec
    bottom: BorderSpec
    left: BorderSpec

def parse_border(data: str) -> BorderSpec:
    """
    Parse a border specifier of the form:
      - '<number>'    → absolute points (pixels)
      - '<number>%'   → percentage of page width or height
    """
    if data.endswith("%"):
        percentage = float(data[:-1])
        if percentage < 0:
            raise ValueError("Percentage must be non-negative.")
        if percentage > 100:
            raise ValueError("Percentage must not exceed 100.")
        return BorderSpec(percentage / 100.0, BorderUnit.RATIO)
    else:
        pixels = float(data)
        if pixels < 0:
            raise ValueError("Border in pixels must be non-negative.")
        return BorderSpec(pixels, BorderUnit.POINT)


def expand_css_border(borders: list[BorderSpec]) -> FourBorders:
    border_num = len(borders)
    if border_num == 1:
        return FourBorders(borders[0], borders[0], borders[0], borders[0])
    if border_num == 4:
        return FourBorders(borders[0], borders[1], borders[2], borders[3])
    raise ValueError(f"Borders expects 1 or 4 values, got {border_num}.")
