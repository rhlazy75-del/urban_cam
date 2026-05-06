import os
import uuid
import shutil
import threading
import requests
from datetime import datetime, timezone
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import psycopg2

app = FastAPI(
    title="Urban Cam Backend",
    version="1.0",
    description="Backend API for the Urban Cam dashboard with FastAPI auto-generated docs.",
    docs_url="/ucs/api/docs",
    redoc_url="/ucs/api/redoc",
    openapi_url="/ucs/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(os.getcwd(), "upload_2cam"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==================== ตั้งค่ากล้อง ====================
CAMERA_IPS = [
    {"id": 1, "ip": "http://10.132.250.222"},
    {"id": 2, "ip": "http://10.132.250.159"},
]

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "dbname": os.environ.get("DB_NAME") or os.environ.get("POSTGRES_DB", "Project_499"),
    "user": os.environ.get("DB_USER") or os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD") or os.environ.get("POSTGRES_PASSWORD", "357004"),
}

TIMEOUT = 10  # timeout ต่อ request (วินาที)

# ==================== ฟังก์ชัน Database ====================

def get_db():
    return psycopg2.connect(**DB_CONFIG)

# ==================== ฟังก์ชันสำหรับการจับภาพ ====================

def save_to_db(cam_id, filename, filepath, captured_at, received_at):
    """บันทึกข้อมูลลง PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO two_cams
                (Filename, device_id, image_path, side, captured_at, received_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (filename, f"CAM{cam_id}", filepath, "cam", captured_at, received_at)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"[cam{cam_id}] 🗄️  บันทึก DB แล้ว")
    except Exception as e:
        print(f"[cam{cam_id}] ❌ DB Error: {e}")


def capture_camera(cam: dict, timestamp: str):
    """ดึงภาพจากกล้องตัวเดียว บันทึกไฟล์ และบันทึก DB"""
    cam_id = cam["id"]
    url = f"{cam['ip']}/capture"

    captured_at = datetime.now(timezone.utc)

    try:
        response = requests.get(url, timeout=TIMEOUT)
        received_at = datetime.now(timezone.utc)

        if response.status_code == 200:
            filename = f"cam{cam_id}_{timestamp}.jpg"
            filepath = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))

            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"[cam{cam_id}] ✅ บันทึกไฟล์: {filepath}")

            save_to_db(cam_id, filename, filepath, captured_at, received_at)

        else:
            print(f"[cam{cam_id}] ❌ HTTP {response.status_code}")

    except requests.exceptions.ConnectionError:
        print(f"[cam{cam_id}] ❌ เชื่อมต่อไม่ได้ ({cam['ip']})")
    except requests.exceptions.Timeout:
        print(f"[cam{cam_id}] ❌ Timeout ({cam['ip']})")
    except Exception as e:
        print(f"[cam{cam_id}] ❌ Error: {e}")


def capture_all():
    """ดึงภาพจากทุกกล้องพร้อมกันด้วย threading"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n📸 ถ่ายภาพ [{timestamp}]")

    threads = []
    for cam in CAMERA_IPS:
        t = threading.Thread(target=capture_camera, args=(cam, timestamp))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return {"timestamp": timestamp, "status": "captured"}

@app.get("/")
def root():
    return {
        "service": "urban_cam backend",
        "status": "ok",
        "routes": [
            "/ucs/api/capture",
            "/ucs/api/upload",
            "/ucs/api/captures",
            "/ucs/api/image/{filename}",
            "/backend",
            "/health",
            "/ucs/api/docs",
            "/ucs/api/redoc",
        ],
    }

@app.post("/ucs/api/capture")
def capture():
    """ทำการถ่ายภาพจากทุกกล้อง"""
    result = capture_all()
    return {"ok": True, **result}

@app.get("/backend")
def backend_info():
    return {"message": "Urban Cam backend is running", "version": "1.0"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/ucs/api/upload", status_code=201)
async def upload(
    image: UploadFile = File(...),
    device_id: str = Form("CAM_001"),
):
    filename = str(uuid.uuid4())[:8] + ".jpg"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    finally:
        await image.close()

    side = "left" if "LEFT" in device_id else "right"

    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO two_cams (filename, device_id, side)
        VALUES (%s, %s, %s) RETURNING id
        """,
        (filename, device_id, side),
    )
    new_id = cur.fetchone()[0]
    db.commit()
    cur.close()
    db.close()

    print(f"[{datetime.now()}] รับภาพ #{new_id} | {device_id} | {side}")
    return {"ok": True, "id": new_id}


@app.post("/upload", status_code=201)
async def upload_legacy(
    image: UploadFile = File(...),
    device_id: str = Form("CAM_001"),
):
    """Legacy endpoint for backward compatibility"""
    return await upload(image, device_id)

@app.get("/ucs/api/captures")
def get_captures():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, filename, device_id, side, label, captured_at
        FROM two_cams
        ORDER BY captured_at DESC
        LIMIT 100
    """
    )
    rows = cur.fetchall()
    cur.close()
    db.close()

    return [
        {
            "id": r[0],
            "filename": r[1],
            "device_id": r[2],
            "side": r[3],
            "label": r[4],
            "captured_at": str(r[5]),
        }
        for r in rows
    ]

@app.get("/ucs/api/image/{filename}")
def get_image(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
