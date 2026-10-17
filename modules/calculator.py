"""AQI calculator based on India's CPCB National Air Quality Index method.

AQI for each pollutant (sub-index) is found by linear interpolation inside the
breakpoint band the concentration falls in.  The overall AQI is the *maximum*
sub-index and the pollutant producing it is the 'dominant pollutant'.

CPCB rule: AQI is valid only if data for at least 3 pollutants is available and
at least one of them is PM2.5 or PM10.
"""
import math

# (conc_low, conc_high, aqi_low, aqi_high)  - bands are contiguous.
# Values above the last band are capped at AQI 500.
POLLUTANTS = {
    "PM2.5": {
        "name": "PM2.5", "unit": "µg/m³", "avg": "24-hr average",
        "bp": [(0, 30, 0, 50), (30, 60, 50, 100), (60, 90, 100, 200),
               (90, 120, 200, 300), (120, 250, 300, 400), (250, 380, 400, 500)],
    },
    "PM10": {
        "name": "PM10", "unit": "µg/m³", "avg": "24-hr average",
        "bp": [(0, 50, 0, 50), (50, 100, 50, 100), (100, 250, 100, 200),
               (250, 350, 200, 300), (350, 430, 300, 400), (430, 510, 400, 500)],
    },
    "NO2": {
        "name": "NO₂", "unit": "µg/m³", "avg": "24-hr average",
        "bp": [(0, 40, 0, 50), (40, 80, 50, 100), (80, 180, 100, 200),
               (180, 280, 200, 300), (280, 400, 300, 400), (400, 500, 400, 500)],
    },
    "SO2": {
        "name": "SO₂", "unit": "µg/m³", "avg": "24-hr average",
        "bp": [(0, 40, 0, 50), (40, 80, 50, 100), (80, 380, 100, 200),
               (380, 800, 200, 300), (800, 1600, 300, 400), (1600, 2000, 400, 500)],
    },
    "CO": {
        "name": "CO", "unit": "mg/m³", "avg": "8-hr average",
        "bp": [(0, 1.0, 0, 50), (1.0, 2.0, 50, 100), (2.0, 10, 100, 200),
               (10, 17, 200, 300), (17, 34, 300, 400), (34, 50, 400, 500)],
    },
    "O3": {
        "name": "O₃", "unit": "µg/m³", "avg": "8-hr average",
        "bp": [(0, 50, 0, 50), (50, 100, 50, 100), (100, 168, 100, 200),
               (168, 208, 200, 300), (208, 748, 300, 400), (748, 1000, 400, 500)],
    },
    "NH3": {
        "name": "NH₃", "unit": "µg/m³", "avg": "24-hr average",
        "bp": [(0, 200, 0, 50), (200, 400, 50, 100), (400, 800, 100, 200),
               (800, 1200, 200, 300), (1200, 1800, 300, 400), (1800, 2400, 400, 500)],
    },
}


def _valid(x):
    if x is None:
        return False
    try:
        return not math.isnan(float(x)) and float(x) >= 0
    except (TypeError, ValueError):
        return False


def sub_index(pollutant, conc):
    """Sub-index (0-500) of a single pollutant concentration."""
    for c_lo, c_hi, i_lo, i_hi in POLLUTANTS[pollutant]["bp"]:
        if conc <= c_hi:
            return i_lo + (conc - c_lo) * (i_hi - i_lo) / (c_hi - c_lo)
    return 500.0


def compute_aqi(concentrations):
    """Compute overall AQI.

    concentrations: dict like {"PM2.5": 80, "PM10": 150, "NO2": 40}
    Returns dict: aqi, dominant, sub_indices.
    Raises ValueError if the CPCB minimum-data rule is not met.
    """
    data = {p: float(v) for p, v in concentrations.items()
            if p in POLLUTANTS and _valid(v)}
    if len(data) < 3:
        raise ValueError("Enter at least 3 pollutants (CPCB rule) to calculate a valid AQI.")
    if "PM2.5" not in data and "PM10" not in data:
        raise ValueError("At least one of PM2.5 or PM10 is required (CPCB rule).")

    subs = {p: round(sub_index(p, v)) for p, v in data.items()}
    dominant = max(subs, key=subs.get)
    return {"aqi": subs[dominant], "dominant": dominant, "sub_indices": subs}
