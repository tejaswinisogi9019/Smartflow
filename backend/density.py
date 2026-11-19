"""
=====================================================================
 SmartFlow AI - Directional Traffic Density Engine (Phase 5)
---------------------------------------------------------------------
 Computes traffic density per directional lane (North, South, East, West)
 and overall junction congestion based on:
   - Directional vehicle count
   - Configurable density thresholds (Low, Medium, High)
=====================================================================
"""

# Configurable thresholds for prototype junction
THRESHOLDS = {
    "LOW_MAX": 5,       # 0 - 5 vehicles = Low density
    "MEDIUM_MAX": 15,   # 6 - 15 vehicles = Medium density
                        # > 15 vehicles = High density
}

def classify_lane_density(count):
    """Classifies a single direction's count into Low, Medium, or High."""
    if count <= THRESHOLDS["LOW_MAX"]:
        return "Low"
    elif count <= THRESHOLDS["MEDIUM_MAX"]:
        return "Medium"
    else:
        return "High"

def compute_traffic_density(directional_counts):
    """
    Takes a dictionary like {'North': 8, 'South': 16, 'East': 2, 'West': 4}
    Returns complete density classification for each direction and overall.
    """
    lane_density = {}
    for direction, count in directional_counts.items():
        lane_density[direction] = classify_lane_density(count)

    total_vehicles = sum(directional_counts.values())

    # Overall junction density
    if total_vehicles <= 12:
        overall_density = "Low"
    elif total_vehicles <= 30:
        overall_density = "Medium"
    else:
        overall_density = "High"

    return {
        "overall": overall_density,
        "total_vehicles": total_vehicles,
        "lane_density": lane_density,
        "thresholds": THRESHOLDS
    }