# -------------------------------------------------------------------------------------------------------------

from math import radians, sin, cos, sqrt, atan2

# -------------------------------------------------------------------------------------------------------------

def extract_numeric_value(value_str):
    """
    Extracts the numeric value from a string containing numeric value followed by units.
    Example: "20km/h" -> 20
    """
    numeric_part = ""
    for char in value_str:
        if char.isdigit() or char == ".":
            numeric_part += char
        else:
            break
    return float(numeric_part) if numeric_part else None

# -------------------------------------------------------------------------------------------------------------

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on the Earth's surface
    using the Haversine formula.

    Parameters:
    lat1 (float): Latitude of the first point in degrees.
    lon1 (float): Longitude of the first point in degrees.
    lat2 (float): Latitude of the second point in degrees.
    lon2 (float): Longitude of the second point in degrees.

    Returns:
    float: Distance between the two points in kilometers.
    """
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    radius_earth = 6371
    distance = radius_earth * c
    return distance

# -------------------------------------------------------------------------------------------------------------

region_distances = {
    "aldoar": {
        "aldoar": 0.0,
        "ramalde": 3.477,
        "lordelo": 3.723,
        "paranhos": 7.486,
        "centro": 5.718,
        "bonfim": 7.633,
        "campanha": 9.483
    },
    "ramalde": {
        "aldoar": 3.477,
        "ramalde": 0.0,
        "lordelo": 1.781,
        "paranhos": 4.010,
        "centro": 2.742,
        "bonfim": 4.471,
        "campanha": 6.150
    },
    "lordelo": {
        "aldoar": 3.723,
        "ramalde": 1.781,
        "lordelo": 0.0,
        "paranhos": 4.623,
        "centro": 2.096,
        "bonfim": 4.019,
        "campanha": 5.970
    },
    "paranhos": {
        "aldoar": 7.486,
        "ramalde": 4.010,
        "lordelo": 4.623,
        "paranhos": 0.0,
        "centro": 3.012,
        "bonfim": 2.563,
        "campanha": 2.896
    },
    "centro": {
        "aldoar": 5.718,
        "ramalde": 2.742,
        "lordelo": 2.096,
        "paranhos": 3.012,
        "centro": 0.0,
        "bonfim": 1.929,
        "campanha": 3.877
    },
    "bonfim": {
        "aldoar": 7.633,
        "ramalde": 4.471,
        "lordelo": 4.019,
        "paranhos": 2.563,
        "centro": 1.929,
        "bonfim": 0.0,
        "campanha": 2.004
    },
    "campanha": {
        "aldoar": 9.483,
        "ramalde": 6.150,
        "lordelo": 5.970,
        "paranhos": 2.896,
        "centro": 3.877,
        "bonfim": 2.004,
        "campanha": 0.0
    }
}

# -------------------------------------------------------------------------------------------------------------

def calculate_angle(pos1, pos2):
    """
    Calculate the angle between two points.
    """
    lat1, lon1 = pos1
    lat2, lon2 = pos2
    return atan2(lat2 - lat1, lon2 - lon1)

# -------------------------------------------------------------------------------------------------------------

def stepsToTime(step, steps_per_day):
    """
    Convert the number of steps to a time string in the format HH:MM.
    """
    hours = step // (steps_per_day // 24)
    minutes = (step % (steps_per_day // 24)) * 60 // (steps_per_day // 24)
    return f"{hours:02d} : {minutes:02d} h"

# -------------------------------------------------------------------------------------------------------------