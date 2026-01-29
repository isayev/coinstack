"""
Normalize NGC/PCGS strike and surface to 1-5 or absent.

Accepts "4/5", "4", 4 and returns "4". Valid output: "1", "2", "3", "4", "5" or None.
"""

from typing import Optional, Union

_VALID = frozenset({"1", "2", "3", "4", "5"})


def normalize_strike_surface(value: Optional[Union[str, int]]) -> Optional[str]:
    """
    Normalize strike or surface to "1"-"5" or None.

    - "4/5", "4", 4 -> "4"
    - "5/5", "5", 5 -> "5"
    - "", None, invalid -> None
    - Values outside 1-5 -> None
    """
    if value is None:
        return None
    if isinstance(value, int):
        if 1 <= value <= 5:
            return str(value)
        return None
    s = str(value).strip()
    if not s:
        return None
    # "4/5" -> take first part
    if "/" in s:
        s = s.split("/")[0].strip()
    if s in _VALID:
        return s
    try:
        n = int(s)
        if 1 <= n <= 5:
            return str(n)
    except ValueError:
        pass
    return None
