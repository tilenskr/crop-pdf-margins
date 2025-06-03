from dataclasses import dataclass
from enum import Enum, auto


class BorderUnit(Enum):
    POINT = auto()
    RATIO = auto()


@dataclass(frozen=True)
class BorderSpec:
    value: float
    unit: BorderUnit


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
