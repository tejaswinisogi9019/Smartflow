/* ================================================================
   SMARTFLOW AI – Master Frontend Controller (Full AI Connected)
   ================================================================ */

const API_BASE = "http://localhost:5000/api";
const VIDEO_STREAM_URL = "http://localhost:5000/video_feed";
const UPDATE_INTERVAL_MS = 2500; // Poll live AI metrics every 2.5s

const state = {
    connected: false,
    timer: null,
    city: "Bengaluru",
    junction: "Silk Board Junction"
};

const DIRECTIONS = ["North", "South", "East", "West"];
const $ = id => document.getElementById(id);

let distChart, signalChart, trendChart;
const trendData = { labels: [], values: [] };

// ================================================================
// INITIALIZATION
// ================================================================
document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    fetchCities();
    
    $("citySelect").addEventListener("change", (e) => fetchJunctions(e.target.value));
    $("connectBtn").addEventListener("click", connectCamera);
    $("stopBtn").addEventListener("click", stopCamera);

    showPlaceholderVideo("📷", "No camera connected.<br>Select City & Junction, then click ▶ Connect.");
});

// ================================================================
// CITIES & JUNCTIONS (Fetched from Flask Backend)
// ================================================================
async function fetchCities() {
    try {
        const res = await fetch(`${API_BASE}/cities`);
        const data = await res.json();
        const citySelect = $("citySelect");
        citySelect.innerHTML = "";
        
        data.cities.forEach(city => {
            const opt = document.createElement("option");
            opt.value = city;
            opt.textContent = city;
            citySelect.appendChild(opt);
        });

        if (data.cities.length > 0) {
            fetchJunctions(data.cities[0]);
        }
    } catch (err) {
        console.error("Could not fetch cities from backend", err);
    }
}

async function fetchJunctions(city) {
    try {
        const res = await fetch(`${API_BASE}/junctions?city=${city}`);
        const data = await res.json();
        const juncSelect = $("junctionSelect");
        juncSelect.innerHTML = "";

        data.junctions.forEach(j => {
            const opt = document.createElement("option");
            opt.value = j.name;
            opt.textContent = j.name + (j.camera_registered ? "" : " (no camera)");
            juncSelect.appendChild(opt);
        });
    } catch (err) {
        console.error("Could not fetch junctions", err);
    }
}

// ================================================================
// CONNECT / STOP CAMERA
// ================================================================
async function connectCamera() {
    const city = $("citySelect").value;
    const junction = $("junctionSelect").value;
    const sourceType = $("cameraSourceSelect").value;

    try {
        const res = await fetch(`${API_BASE}/camera/connect`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                city: city,
                junction: junction,
                source_type: sourceType
            })
        });

        const data = await res.json();

        // If camera is unavailable for this junction
        if (data.status === "unavailable") {
            showUnavailableVideo(data.message);
            setCameraStatus("unavailable");
            $("cameraNote").textContent = "Honest Mode: No registered camera for this location.";
            return;
        }

        if (data.status === "connected") {
            state.connected = true;
            state.city = city;
            state.junction = junction;

            setCameraStatus("connected");
            $("connectBtn").disabled = true;
            $("stopBtn").disabled = false;

            // Load live video stream into the panel
            $("videoPanel").innerHTML = `<img src="${VIDEO_STREAM_URL}?t=${new Date().getTime()}" alt="Live AI Camera Feed" style="width:100%; height:100%; object-fit:cover;">`;
            $("cameraNote").textContent = `Live Stream: ${junction}, ${city} [YOLO/OpenCV AI Active]`;

            // Hide the Demo Mode banner (Real AI is active!)
            $("demoBanner").style.display = "none";
            $("dataSourceBadge").textContent = "● REAL AI VISION";
            $("dataSourceBadge").className = "status-pill status-on";

            // Start live metric polling
            if (state.timer) clearInterval(state.timer);
            state.timer = setInterval(fetchLiveMetrics, UPDATE_INTERVAL_MS);
            fetchLiveMetrics();
        }
    } catch (err) {
        console.error("Error connecting to camera:", err);
        alert("Could not connect to Flask Backend. Is app.py running?");
    }
}

async function stopCamera() {
    try {
        await fetch(`${API_BASE}/camera/stop`, { method: "POST" });
        state.connected = false;
        clearInterval(state.timer);

        setCameraStatus("off");
        $("connectBtn").disabled = false;
        $("stopBtn").disabled = true;

        showPlaceholderVideo("📷", "Camera stopped.<br>Click ▶ Connect to start live stream.");
        $("cameraNote").textContent = "Camera is offline.";
    } catch (err) {
        console.error("Error stopping camera", err);
    }
}

// ================================================================
// LIVE AI POLLING & DASHBOARD UPDATE
// ================================================================
async function fetchLiveMetrics() {
    if (!state.connected) return;

    try {
        const res = await fetch(`${API_BASE}/traffic/live`);
        const data = await res.json();

        if (data.status === "success") {
            const counts = data.counts;
            const density = data.density;
            const signals = data.signals;

            // Stat Cards
            $("statTotal").textContent = density.total_vehicles;
            $("statDensity").textContent = density.overall;
            $("statCycle").textContent = `${signals.total_cycle_seconds}s`;
            $("statCamera").textContent = "Live AI";

            // Direction Cards
            DIRECTIONS.forEach(dir => {
                const count = counts[dir] || 0;
                const laneDensity = density.lane_density[dir] || "Low";

                $("count" + dir).textContent = count;
                $("bar" + dir).style.width = Math.min(100, (count / 20) * 100) + "%";
                
                const badge = $("density" + dir);
                badge.textContent = laneDensity;
                badge.className = "badge " + laneDensity.toLowerCase();
            });

            // Signal Recommendation Table
            const tbody = $("signalTableBody");
            tbody.innerHTML = "";
            DIRECTIONS.forEach(dir => {
                const count = counts[dir] || 0;
                const laneDensity = density.lane_density[dir] || "Low";
                const greenSec = signals.timings[dir] || 15;

                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${dir}</strong></td>
                    <td>${count}</td>
                    <td><span class="badge ${laneDensity.toLowerCase()}">${laneDensity}</span></td>
                    <td><strong style="color:var(--accent-green); font-size:1.1rem;">${greenSec}s</strong></td>
                `;
                tbody.appendChild(tr);
            });

            $("cycleInfo").textContent =
                `Total Cycle: ${signals.total_cycle_seconds}s (Greens: ${signals.total_green_seconds}s + 4 × 5s Pedestrian Safety Clearance). Recommendation only.`;

            // Charts
            updateCharts(counts, signals.timings, density.total_vehicles);

            // Update Database History Table
            fetchHistoryTable();
        }
    } catch (err) {
        console.error("Error fetching live metrics", err);
    }
}

async function fetchHistoryTable() {
    try {
        const res = await fetch(`${API_BASE}/history`);
        const data = await res.json();

        if (data.status === "success" && data.history.length > 0) {
            const tbody = $("historyTableBody");
            tbody.innerHTML = "";

            data.history.forEach(row => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${row.time_str || "Just now"}</td>
                    <td>${row.junction}</td>
                    <td>${row.north_count}</td>
                    <td>${row.south_count}</td>
                    <td>${row.east_count}</td>
                    <td>${row.west_count}</td>
                    <td><strong>${row.total_count}</strong></td>
                    <td><span class="badge ${row.overall_density.toLowerCase()}">${row.overall_density}</span></td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error("Error fetching history", err);
    }
}

// ================================================================
// UI HELPERS
// ================================================================
function showPlaceholderVideo(icon, message) {
    $("videoPanel").innerHTML = `
        <div class="video-placeholder">
            <span class="big">${icon}</span>
            <p>${message}</p>
        </div>`;
}

function showUnavailableVideo(message) {
    $("videoPanel").innerHTML = `
        <div class="video-unavailable">
            <span class="big">🚫</span>
            <strong>Camera Feed Unavailable</strong><br><br>
            <p>${message}</p>
        </div>`;
}

function setCameraStatus(status) {
    const badge = $("cameraStatusBadge");
    if (status === "connected") {
        badge.textContent = "● Live Stream Active";
        badge.className = "status-pill status-on";
    } else if (status === "unavailable") {
        badge.textContent = "● Unavailable";
        badge.className = "status-pill status-warn";
    } else {
        badge.textContent = "● Not Connected";
        badge.className = "status-pill status-off";
    }
}

// ================================================================
// CHART.JS INTEGRATION
// ================================================================
function initCharts() {
    try {
        const colors = ["#3b82f6", "#22c55e", "#eab308", "#ef4444"];
        const opts = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: "#f1f5f9" } } },
            scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "#1e3a6e" } },
                y: { ticks: { color: "#94a3b8" }, grid: { color: "#1e3a6e" } }
            }
        };

        distChart = new Chart($("chartDistribution"), {
            type: "doughnut",
            data: { labels: DIRECTIONS, datasets: [{ data: [0, 0, 0, 0], backgroundColor: colors }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#f1f5f9" } } } }
        });

        signalChart = new Chart($("chartSignals"), {
            type: "bar",
            data: { labels: DIRECTIONS, datasets: [{ label: "Green Seconds", data: [15, 15, 15, 15], backgroundColor: "#3b82f6" }] },
            options: opts
        });

        trendChart = new Chart($("chartTrend"), {
            type: "line",
            data: { labels: [], datasets: [{ label: "Total Vehicles Detected", data: [], borderColor: "#38bdf8", backgroundColor: "rgba(56,189,248,0.15)", fill: true, tension: 0.3 }] },
            options: opts
        });
    } catch (e) {
        console.warn("Chart.js warning:", e);
    }
}

function updateCharts(counts, timings, total) {
    if (distChart) {
        distChart.data.datasets[0].data = DIRECTIONS.map(d => counts[d] || 0);
        distChart.update();
    }

    if (signalChart) {
        signalChart.data.datasets[0].data = DIRECTIONS.map(d => timings[d] || 15);
        signalChart.update();
    }

    if (trendChart) {
        trendData.labels.push(new Date().toLocaleTimeString());
        trendData.values.push(total);
        if (trendData.labels.length > 10) {
            trendData.labels.shift();
            trendData.values.shift();
        }
        trendChart.data.labels = trendData.labels;
        trendChart.data.datasets[0].data = trendData.values;
        trendChart.update();
    }
}