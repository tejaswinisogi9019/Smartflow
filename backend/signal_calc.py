"""
=====================================================================
 SmartFlow AI - Intelligent Signal Timing Engine (Phase 6)
---------------------------------------------------------------------
 Implements Dynamic Green Light Allocation Algorithm:
   - Minimum Green: 15s (prevents starvation)
   - Maximum Green: 60s (prevents excessive queue delay)
   - Proportional allocation based on real-time directional demand
   - Includes 5s safety clearance interval per phase (Pedestrian/Yellow)
=====================================================================
"""

# Configurable Signal Parameters
MIN_GREEN = 15     # Minimum green time in seconds
MAX_GREEN = 60     # Maximum green time in seconds
CLEARANCE_SEC = 5  # Yellow + All-Red safety interval per phase

def calculate_signal_timings(directional_counts):
    """
    Calculates optimized green light timings for North, South, East, West.
    """
    total_vehicles = sum(directional_counts.values())
    allocated_timings = {}

    # If no vehicles detected anywhere, default to safe minimum
    if total_vehicles == 0:
        return {
            "timings": {d: MIN_GREEN for d in directional_counts.keys()},
            "total_cycle": (MIN_GREEN * 4) + (CLEARANCE_SEC * 4),
            "clearance_per_phase": CLEARANCE_SEC,
            "min_green": MIN_GREEN,
            "max_green": MAX_GREEN,
            "note": "Default baseline timing applied (no vehicles detected)."
        }

    # Proportional allocation formula:
    # Green_Time = MIN_GREEN + (Direction_Count / Total_Count) * (MAX_GREEN - MIN_GREEN)
    for direction, count in directional_counts.items():
        ratio = count / max(total_vehicles, 1)
        time_sec = MIN_GREEN + int(ratio * (MAX_GREEN - MIN_GREEN))
        
        # Clamp strictly between MIN_GREEN and MAX_GREEN
        clamped_time = max(MIN_GREEN, min(MAX_GREEN, time_sec))
        allocated_timings[direction] = clamped_time

    total_green = sum(allocated_timings.values())
    total_cycle = total_green + (CLEARANCE_SEC * 4)

    return {
        "timings": allocated_timings,
        "total_green_seconds": total_green,
        "clearance_per_phase": CLEARANCE_SEC,
        "total_cycle_seconds": total_cycle,
        "min_green": MIN_GREEN,
        "max_green": MAX_GREEN,
        "note": "Recommendation model only — includes pedestrian safety clearance."
    }