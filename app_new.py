from flask import Flask, render_template_string, jsonify, request, send_from_directory
import cv2 as cv
import os
import time
import requests
from datetime import datetime

app = Flask(__name__)

# =========================
# SERVER API
# =========================
# Update these URLs to match your server configuration
SERVER_BASE_URL     = os.environ.get("SERVER_BASE_URL", "http://geodev.fun")
SERVER_IMAGE_URL    = f"{SERVER_BASE_URL}/ucs/api/image/"
SERVER_CAPTURES_URL = f"{SERVER_BASE_URL}/ucs/api/captures"
SERVER_UPLOAD_URL   = f"{SERVER_BASE_URL}/ucs/api/upload"
SERVER_GPS_URL      = f"{SERVER_BASE_URL}/ucs/api/gps"

latest_capture = {}
latest_gps     = {"lat": None, "lng": None}

# =========================
# CREATE IMAGE FOLDER
# =========================
folder_name = "capture_images"
os.makedirs(folder_name, exist_ok=True)

# =========================
# OPEN CAMERAS
# =========================
cap1 = cv.VideoCapture(1, cv.CAP_DSHOW)
cap2 = cv.VideoCapture(2, cv.CAP_DSHOW)

cap1.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap1.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

cap2.set(cv.CAP_PROP_FRAME_WIDTH, 640)
cap2.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

print("Camera1:", cap1.isOpened())
print("Camera2:", cap2.isOpened())

# =========================
# CONTROL FLAGS
# =========================
capture_interval     = 5
last_capture_time    = time.time()
auto_capture_enabled = False
camera_running       = True

# =========================
# HTML PAGE (inline)
# =========================
HTML = '''
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dual Camera Flask</title>

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<style>
*{box-sizing:border-box;margin:0;padding:0}

body{
    font-family:Arial,sans-serif;
    background:#f2f2f2;
    padding-top:52px;
}

/* ── TOP STATUS BAR ── */
.topbar{
    position:fixed;top:0;left:0;right:0;height:52px;
    background:#1a1a2e;
    display:flex;align-items:center;
    justify-content:space-between;
    padding:0 16px;
    z-index:9999;
    box-shadow:0 2px 8px rgba(0,0,0,.4);
}

.topbar-title{
    color:#00e5ff;font-size:15px;
    font-weight:bold;letter-spacing:2px;
}

.cam-pills{display:flex;gap:10px;}

.cam-pill{
    display:flex;align-items:center;gap:6px;
    padding:5px 12px;border-radius:20px;
    font-size:12px;font-weight:bold;letter-spacing:1px;
    border:1px solid #444;color:#666;background:#111;
    transition:all .3s;
}

.cam-pill.on{
    border-color:#39ff6b;color:#39ff6b;
    background:rgba(57,255,107,.08);
}

.dot{
    width:8px;height:8px;border-radius:50%;
    background:currentColor;flex-shrink:0;
}

.dot.pulse{animation:blink 1.1s infinite;}

@keyframes blink{
    0%,100%{opacity:1;transform:scale(1)}
    50%{opacity:.3;transform:scale(.6)}
}

/* ── MAP ── */
#map{width:100%; height:300px; border-bottom:3px solid #00e5ff;}

.map-wrap{position:relative;}

.gps-box{
    position:absolute;bottom:10px;left:10px;z-index:500;
    background:rgba(0,0,0,.75);color:#00e5ff;
    font-size:11px;font-family:monospace;
    padding:5px 10px;border-radius:5px;
    border:1px solid #00e5ff;pointer-events:none;
}

/* ── CONTROLS ── */
.controls{
    background:#fff;
    padding:14px 20px;
    display:flex;align-items:center;
    gap:10px;flex-wrap:wrap;
    border-bottom:1px solid #ddd;
}

button{
    padding:12px 22px;font-size:15px;
    border:none;border-radius:6px;
    cursor:pointer;font-weight:bold;
    transition:opacity .2s,transform .1s;
}

button:active{transform:scale(.97);}
button:disabled{opacity:.35;cursor:not-allowed;}

.btn-once  {background:#2196F3;color:#fff;}
.btn-start {background:#4CAF50;color:#fff;}
.btn-stop  {background:#f44336;color:#fff;}
.btn-cam   {background:#555;   color:#fff;}

#status{
    margin-left:auto;font-size:13px;
    color:#555;font-style:italic;
}

/* ── SECTIONS ── */
.section{margin:20px;}

.section h2{
    font-size:13px;letter-spacing:2px;
    text-transform:uppercase;color:#888;
    margin-bottom:12px;
    border-bottom:1px solid #ddd;
    padding-bottom:6px;
}

.container{
    display:flex;justify-content:flex-start;
    gap:16px;flex-wrap:wrap;
}

.card{
    background:#fff;padding:10px;
    border-radius:10px;
    box-shadow:0 2px 10px rgba(0,0,0,.12);
    width:320px;
}

.card img{
    width:100%;border:2px solid #ddd;
    border-radius:4px;display:block;
    background:#eee;
}

.card-meta{
    margin-top:8px;font-size:11px;
    color:#666;font-family:monospace;
    line-height:1.8;
}

.gps-val{color:#e65100;font-weight:bold;}

.server-card{width:260px;}
.server-card img{height:160px;object-fit:cover;}
</style>
</head>
<body>

<!-- STATUS BAR -->
<div class="topbar">
    <div class="topbar-title"> URBAN_CAMS </div>
    <div class="cam-pills">
        <div class="cam-pill" id="pill1">
            <div class="dot" id="dot1"></div>CAM-LEFT
        </div>
        <div class="cam-pill" id="pill2">
            <div class="dot" id="dot2"></div>CAM-RIGHT
        </div>
    </div>
</div>

<!-- MAP -->
<div class="map-wrap">
    <div id="map"></div>
    <div class="gps-box" id="gps-box">📍 กำลังหาตำแหน่ง...</div>
</div>

<!-- CONTROLS -->
<div class="controls">
    <button class="btn-once"  onclick="manualCapture()">📷 ถ่ายครั้งเดียว</button>
    <button class="btn-start" id="btn-start" onclick="startAuto()">▶ เริ่มถ่าย</button>
    <button class="btn-stop"  id="btn-stop"  onclick="stopAuto()" disabled>⏹ หยุดถ่าย</button>
    <button class="btn-cam"   onclick="stopCamera()">🔴 ปิดกล้อง</button>
    <span id="status">พร้อมใช้งาน</span>
</div>

<!-- LOCAL IMAGES -->
<div class="section">
    <h2>ภาพจากกล้อง (ล่าสุด)</h2>
    <div class="container">

        <div class="card">
            <b>Camera 1 — LEFT</b>
            <img id="local1" src="" alt="ยังไม่มีภาพ">
            <div class="card-meta" id="meta1">—</div>
        </div>

        <div class="card">
            <b>Camera 2 — RIGHT</b>
            <img id="local2" src="" alt="ยังไม่มีภาพ">
            <div class="card-meta" id="meta2">—</div>
        </div>

    </div>
</div>

<!-- SERVER IMAGES -->
<div class="section">
    <h2>ภาพจาก Server</h2>
    <div class="container" id="serverImages">
        <p style="color:#aaa;font-size:13px;">กำลังโหลด...</p>
    </div>
</div>

<script>
// ─── GPS ──────────────────────────────────────
let currentLat = null;
let currentLng = null;
let map        = null;
let mapMarker  = null;

function initMap(lat, lng){
    if(map){ map.setView([lat,lng],16); return; }
    map = L.map('map',{zoomControl:true,attributionControl:false})
            .setView([lat,lng],16);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                {maxZoom:19}).addTo(map);
    const icon = L.divIcon({
        className:'',
        html:`<div style="width:14px;height:14px;background:#00e5ff;
              border-radius:50%;border:3px solid #fff;
              box-shadow:0 0 12px #00e5ff"></div>`,
        iconSize:[14,14], iconAnchor:[7,7]
    });
    mapMarker = L.marker([lat,lng],{icon}).addTo(map);
}

function onGPS(pos){
    const lat = pos.coords.latitude;
    const lng = pos.coords.longitude;
    currentLat = lat;
    currentLng = lng;
    document.getElementById('gps-box').textContent =
        '📍 ' + lat.toFixed(6) + ', ' + lng.toFixed(6);
    initMap(lat, lng);
    if(mapMarker) mapMarker.setLatLng([lat,lng]);
    fetch('/update_gps',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({lat, lng})
    }).catch(()=>{});
}

if(navigator.geolocation){
    navigator.geolocation.watchPosition(
        onGPS,
        ()=>{ document.getElementById('gps-box').textContent = '⚠ ไม่สามารถรับ GPS'; },
        {enableHighAccuracy:true, maximumAge:5000, timeout:10000}
    );
} else {
    document.getElementById('gps-box').textContent = '⚠ ไม่รองรับ GPS';
}

// ─── CAM STATUS ───────────────────────────────
function setCam(n, on){
    document.getElementById('pill'+n).classList.toggle('on', on);
    const d = document.getElementById('dot'+n);
    if(on) d.classList.add('pulse'); else d.classList.remove('pulse');
}

// ─── CAPTURE ──────────────────────────────────
let autoTimer = null;

async function manualCapture(){
    setStatus('กำลังถ่ายภาพ...');
    const res  = await fetch('/capture',{method:'POST'});
    const data = await res.json();
    updateLocal(data);
    loadServer();
}

async function startAuto(){
    const res  = await fetch('/start_auto',{method:'POST'});
    const data = await res.json();
    setStatus(data.message);
    document.getElementById('btn-start').disabled = true;
    document.getElementById('btn-stop').disabled  = false;
    setCam(1,true); setCam(2,true);
    if(!autoTimer){
        autoTimer = setInterval(async()=>{
            await loadLatest();
            await loadServer();
        }, 2500);
    }
}

async function stopAuto(){
    clearInterval(autoTimer); autoTimer = null;
    const res  = await fetch('/stop_auto',{method:'POST'});
    const data = await res.json();
    setStatus(data.message);
    document.getElementById('btn-start').disabled = false;
    document.getElementById('btn-stop').disabled  = true;
    setCam(1,false); setCam(2,false);
}

async function stopCamera(){
    const res  = await fetch('/stop_camera',{method:'POST'});
    const data = await res.json();
    setStatus(data.message);
    setCam(1,false); setCam(2,false);
}

async function loadLatest(){
    const res  = await fetch('/latest');
    const data = await res.json();
    if(data.cap1) updateLocal(data);
}

function updateLocal(data){
    if(data.error){ setStatus('⚠ ' + data.error); return; }
    setStatus('ถ่ายสำเร็จ: ' + data.timestamp);
    setCam(1,true); setCam(2,true);
    const t = '?t=' + Date.now();
    document.getElementById('local1').src = '/capture_images/' + data.cap1 + t;
    document.getElementById('local2').src = '/capture_images/' + data.cap2 + t;
    const gpsText = (data.lat && data.lng)
        ? `<span class="gps-val">📍 ${parseFloat(data.lat).toFixed(6)}, ${parseFloat(data.lng).toFixed(6)}</span>`
        : '📍 ไม่มีข้อมูล GPS';
    const meta = `เวลา: ${data.timestamp}<br>${gpsText}`;
    document.getElementById('meta1').innerHTML = meta;
    document.getElementById('meta2').innerHTML = meta;
}

async function loadServer(){
    const res  = await fetch('/server_captures');
    const list = await res.json();
    const box  = document.getElementById('serverImages');
    if(!list || list.error || !list.length){
        const errorMessage = list && list.error ? list.error : 'ยังไม่มีภาพจาก server';
        box.innerHTML = `<p style="color:#e53935;font-size:13px;">${errorMessage}</p>`;
        return;
    }
    box.innerHTML = list.slice(0,6).map(item=>{
        const gps = (item.lat !== null && item.lat !== undefined && item.lng !== null && item.lng !== undefined)
            ? `📍 ${parseFloat(item.lat).toFixed(5)}, ${parseFloat(item.lng).toFixed(5)}`
            : '—';
        return `
        <div class="card server-card">
            <b>${item.device_id}</b>
            <img src="${item.image_url}?t=${Date.now()}" loading="lazy">
            <div class="card-meta">
                ${item.captured_at}<br>
                <span class="gps-val">${gps}</span>
            </div>
        </div>`;
    }).join('');
}

function setStatus(msg){
    document.getElementById('status').textContent = msg;
}

loadServer();
</script>
</body>
</html>
'''

# =========================
# UPLOAD FUNCTION
# =========================

def upload_image(filepath, device_id):
    """Upload image to FastAPI server (GPS จะใช้ค่าล่าสุดจากโทรศัพท์)"""
    try:
        with open(filepath, 'rb') as img:
            files = {'image': img}
            data = {
                'device_id': device_id,
            }

            response = requests.post(
                SERVER_UPLOAD_URL,
                files=files,
                data=data,
                timeout=10
            )
            if response.status_code != 201:
                print(f"❌ UPLOAD FAILED {device_id}: {response.status_code} {response.text}")
                return False
            print(f"✅ UPLOAD {device_id} → {response.status_code}")
            return True
    except Exception as e:
        print(f"❌ UPLOAD ERROR {device_id}: {e}")
        return False

# =========================
# SAVE IMAGES
# =========================

def save_images():
    """Capture from both cameras and upload to server"""
    global last_capture_time

    if not camera_running:
        return {"error": "Camera stopped"}

    # Flush camera buffers
    for _ in range(3):
        cap1.read()
        cap2.read()

    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()

    if not ret1:
        return {"error": "Camera 1 failed"}
    if not ret2:
        return {"error": "Camera 2 failed"}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img1  = f"cap1_{timestamp}.jpg"
    img2  = f"cap2_{timestamp}.jpg"
    path1 = os.path.join(folder_name, img1)
    path2 = os.path.join(folder_name, img2)

    cv.imwrite(path1, frame1)
    cv.imwrite(path2, frame2)

    print(f"📸 Captured: {path1}")
    print(f"📸 Captured: {path2}")

    lat = latest_gps["lat"]
    lng = latest_gps["lng"]

    # Upload both images (GPS จะใช้ค่าล่าสุดจากโทรศัพท์)
    ok1 = upload_image(path1, "CAM_LEFT")
    ok2 = upload_image(path2, "CAM_RIGHT")
    if not ok1 or not ok2:
        print("UPLOAD ERROR: one or more uploads failed")

    last_capture_time = time.time()

    global latest_capture
    latest_capture = {
        "cap1":      img1,
        "cap2":      img2,
        "timestamp": timestamp,
        "lat":       lat,
        "lng":       lng,
    }
    return latest_capture

# =========================
# ROUTES
# =========================

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/capture', methods=['POST'])
def capture():
    return jsonify(save_images())

@app.route('/latest')
def latest():
    return jsonify(latest_capture)

@app.route('/start_auto', methods=['POST'])
def start_auto():
    global auto_capture_enabled
    auto_capture_enabled = True
    return jsonify({"message": "เริ่มถ่ายภาพอัตโนมัติแล้ว"})

@app.route('/stop_auto', methods=['POST'])
def stop_auto():
    global auto_capture_enabled
    auto_capture_enabled = False
    return jsonify({"message": "หยุดถ่ายภาพแล้ว"})

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    global camera_running
    camera_running = False
    cap1.release()
    cap2.release()
    return jsonify({"message": "ปิดกล้องแล้ว"})

# =========================
# GPS — รับพิกัดจาก browser
# =========================

@app.route('/update_gps', methods=['POST'])
def update_gps():
    """Receive GPS coordinates from browser"""
    global latest_gps
    body = request.get_json(force=True, silent=True) or {}
    lat  = body.get('lat')
    lng  = body.get('lng')
    if lat is not None and lng is not None:
        latest_gps = {"lat": lat, "lng": lng}
        print(f"📍 GPS UPDATE: {lat:.6f}, {lng:.6f}")
        try:
            requests.post(
                SERVER_GPS_URL,
                json={"lat": lat, "lng": lng, "device": "WEB"},
                timeout=5,
            )
        except Exception as e:
            print(f"GPS FORWARD ERROR: {e}")
    return jsonify({"ok": True})

@app.route('/server_captures')
def server_captures():
    """Fetch latest captures from FastAPI server"""
    try:
        response = requests.get(SERVER_CAPTURES_URL, timeout=10)
        captures = response.json()
        results  = []

        if isinstance(captures, list):
            for item in captures:
                results.append({
                    "id":         item.get("id"),
                    "device_id":  item.get("device_id"),
                    "captured_at": item.get("captured_at"),
                    "image_url":  item.get("image_url") or SERVER_IMAGE_URL + item.get("filename", ""),
                    "lat":        item.get("lat"),
                    "lng":        item.get("lng"),
                })

        return jsonify(results)
    except Exception as e:
        print(f"❌ SERVER CAPTURES ERROR: {e}")
        return jsonify({"error": str(e)})

# =========================
# SERVE LOCAL IMAGES
# =========================

@app.route('/capture_images/<filename>')
def images(filename):
    return send_from_directory(folder_name, filename)

# =========================
# AUTO CAPTURE LOOP
# =========================

def auto_capture():
    """Background thread for automatic captures"""
    global last_capture_time
    while True:
        try:
            if auto_capture_enabled and camera_running:
                if time.time() - last_capture_time >= capture_interval:
                    print("🔄 AUTO CAPTURE RUNNING")
                    result = save_images()
                    if "error" in result:
                        print(f"   ⚠️  {result['error']}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ AUTO LOOP ERROR: {e}")
            time.sleep(1)

# =========================
# RUN
# =========================

if __name__ == '__main__':
    import threading

    print(f"\n🚀 Starting Flask App")
    print(f"📡 Server: {SERVER_BASE_URL}")
    print(f"🌐 Web UI: http://localhost:5000\n")

    t = threading.Thread(target=auto_capture)
    t.daemon = True
    t.start()

    app.run(host='0.0.0.0', debug=False, port=5000)