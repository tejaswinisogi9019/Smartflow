"""
=====================================================================
 SmartFlow AI - Master Backend Server (All Phases 1-7 Integrated)
=====================================================================
"""

import os
import time
from datetime import datetime

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from camera import global_camera
from detection import detector
from density import compute_traffic_density
from signal_calc import calculate_signal_timings
from database import init_db, log_traffic_event, get_recent_history

app = Flask(__name__)
CORS(app)

# Initialize SQLite Database on startup
init_db()

CITY_DATA = {
    "Bengaluru": [
        {"name": "Silk Board Junction", "camera_registered": True},
        {"name": "Hebbal Flyover",      "camera_registered": True},
        {"name": "Dairy Circle",        "camera_registered": False},
    ],
    "Shivamogga": [
        {"name": "Gopi Circle",         "camera_registered": True},
        {"name": "Bus Stand Circle",    "camera_registered": False},
    ],
    "Mysuru": [
        {"name": "KR Circle",           "camera_registered": True},
        {"name": "Hardinge Circle",     "camera_registered": True},
    ],
}

VALID_SOURCES = {
    "webcam": "Laptop Webcam",
    "ipcam":  "Mobile IP Camera",
    "video":  "Recorded Video File",
    "cctv":   "Registered CCTV/IP Stream",
}

camera_state = {
    "connected": False,
    "city": None,
    "junction": None,
    "source_type": None,
    "source_detail": None,
    "connected_at": None,
}

def find_junction(city, junction_name):
    for junction in CITY_DATA.get(city, []):
        if junction["name"] == junction_name:
            return junction
    return None

# ==================================================================
# API ROUTES
# ==================================================================

@app.route("/")
def home():
    return jsonify({
        "project": "SmartFlow AI Backend",
        "status": "fully_operational",
        "version": "1.0-Hackathon"
    })

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera_connected": camera_state["connected"],
    })

@app.route("/api/cities", methods=["GET"])
def get_cities():
    return jsonify({"status": "success", "cities": list(CITY_DATA.keys())})

@app.route("/api/junctions", methods=["GET"])
def get_junctions():
    city = request.args.get("city")
    if not city or city not in CITY_DATA:
        return jsonify({"status": "error", "message": f"City '{city}' not found."}), 404
    return jsonify({"status": "success", "city": city, "junctions": CITY_DATA[city]})

@app.route("/api/camera/connect", methods=["POST"])
def connect_camera():
    data = request.get_json(silent=True) or {}
    city = data.get("city")
    junction_name = data.get("junction")
    source_type = data.get("source_type", "webcam")
    custom_url = data.get("stream_url", None)

    if not city or not junction_name:
        return jsonify({"status": "error", "message": "City and junction are required."}), 400

    junction = find_junction(city, junction_name)
    if not junction:
        return jsonify({"status": "error", "message": "Junction not found."}), 404

    if not junction["camera_registered"]:
        return jsonify({
            "status": "unavailable",
            "message": f"No authorized camera registered for {junction_name}, {city}.",
        })

    actual_source = 0
    if source_type == "video":
        video_path = os.path.join(os.path.dirname(__file__), "..", "data", "traffic.mp4")
        if os.path.exists(video_path):
            actual_source = video_path
    elif source_type in ["ipcam", "cctv"] and custom_url:
        actual_source = custom_url

    success = global_camera.start(actual_source)
    if not success:
        return jsonify({"status": "error", "message": "Failed to open camera source."}), 500

    camera_state.update({
        "connected": True,
        "city": city,
        "junction": junction_name,
        "source_type": source_type,
        "source_detail": str(actual_source),
        "connected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    return jsonify({"status": "connected", "camera": camera_state})

@app.route("/api/camera/stop", methods=["POST"])
def stop_camera():
    global_camera.stop()
    camera_state.update({
        "connected": False,
        "city": None,
        "junction": None,
        "source_type": None,
        "source_detail": None,
        "connected_at": None,
    })
    return jsonify({"status": "stopped"})

@app.route("/video_feed")
def video_feed():
    def generate():
        while True:
            frame_bytes = global_camera.get_frame()
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
            time.sleep(0.04)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/traffic/live", methods=["GET"])
def traffic_live():
    if not camera_state["connected"]:
        return jsonify({
            "status": "no_camera",
            "data_source": "none",
            "message": "No camera connected.",
            "counts": None,
        })

    # 1. AI Vision counts
    counts = detector.get_directional_counts()

    # 2. Density classification
    density_analysis = compute_traffic_density(counts)

    # 3. Dynamic Signal Timing
    signal_analysis = calculate_signal_timings(counts)

    # 4. Save to SQLite Database history
    log_traffic_event(
        camera_state["city"],
        camera_state["junction"],
        counts,
        density_analysis["overall"],
        signal_analysis["timings"]
    )

    return jsonify({
        "status": "success",
        "data_source": "ai_computer_vision",
        "camera": camera_state,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "counts": counts,
        "density": density_analysis,
        "signals": signal_analysis,
    })

@app.route("/api/signal/recommend", methods=["GET"])
def signal_recommend():
    if not camera_state["connected"]:
        return jsonify({"status": "no_camera", "message": "No camera connected."})

    counts = detector.get_directional_counts()
    signal_analysis = calculate_signal_timings(counts)
    return jsonify({"status": "success", "signals": signal_analysis})

@app.route("/api/history", methods=["GET"])
def history():
    records = get_recent_history(10)
    return jsonify({"status": "success", "history": records})

if __name__ == "__main__":
    print("=" * 60)
    print(" SmartFlow AI Backend - Master Server Operational")
    print(" Backend API:  http://localhost:5000")
    print(" Video Stream: http://localhost:5000/video_feed")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)