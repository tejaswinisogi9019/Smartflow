"""
=====================================================================
 SmartFlow AI - SQLite Traffic Database Engine (Phase 7)
---------------------------------------------------------------------
 Automatically creates 'data/traffic.db' and logs:
   - Timestamp, City, Junction
   - North, South, East, West Vehicle Counts
   - Overall Traffic Density
   - Recommended Green Light Seconds for each Direction
=====================================================================
"""

import sqlite3
import os

# Database file stored in SmartFlow/data/traffic.db
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "traffic.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initializes the database table if it doesn't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            city TEXT NOT NULL,
            junction TEXT NOT NULL,
            north_count INTEGER DEFAULT 0,
            south_count INTEGER DEFAULT 0,
            east_count INTEGER DEFAULT 0,
            west_count INTEGER DEFAULT 0,
            total_count INTEGER DEFAULT 0,
            overall_density TEXT,
            rec_north_sec INTEGER,
            rec_south_sec INTEGER,
            rec_east_sec INTEGER,
            rec_west_sec INTEGER
        )
    """)
    conn.commit()
    conn.close()
    print("[Database] SQLite traffic database initialized successfully.")

def log_traffic_event(city, junction, counts, overall_density, signal_timings):
    """Saves a single traffic analysis snapshot to the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        total = sum(counts.values())
        
        cursor.execute("""
            INSERT INTO traffic_history 
            (city, junction, north_count, south_count, east_count, west_count, total_count,
             overall_density, rec_north_sec, rec_south_sec, rec_east_sec, rec_west_sec)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            city, junction,
            counts.get("North", 0), counts.get("South", 0),
            counts.get("East", 0), counts.get("West", 0),
            total,
            overall_density,
            signal_timings.get("North", 15), signal_timings.get("South", 15),
            signal_timings.get("East", 15), signal_timings.get("West", 15)
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database Error] Could not log event: {e}")

def get_recent_history(limit=10):
    """Retrieves the latest traffic history records."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, datetime(timestamp, 'localtime') as time_str,
                   city, junction, north_count, south_count, east_count, west_count,
                   total_count, overall_density, rec_north_sec, rec_south_sec, rec_east_sec, rec_west_sec
            FROM traffic_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[Database Error] Could not fetch history: {e}")
        return []