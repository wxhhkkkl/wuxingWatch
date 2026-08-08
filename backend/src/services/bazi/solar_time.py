"""True solar time adjustment.

真太阳时 = 平太阳时 + 经度修正(4min × (经度 − 标准经线)) + 均时差
China uses UTC+8 whose standard meridian is 120°E.
"""

import math
from datetime import datetime, timedelta

STD_MERIDIAN = 120.0  # degrees E (UTC+8)

_TWO_PI = 2 * math.pi


def equation_of_time_minutes(day_of_year: int) -> float:
    """Equation of time (minutes) via the Spencer approximation."""
    b = _TWO_PI * (day_of_year - 81) / 364
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def true_solar_time(local_dt: datetime, longitude: float) -> datetime:
    """Convert a local clock time to true solar time for a given longitude."""
    lon_correction = 4.0 * (longitude - STD_MERIDIAN)
    eot = equation_of_time_minutes(local_dt.timetuple().tm_yday)
    return local_dt + timedelta(minutes=lon_correction + eot)
