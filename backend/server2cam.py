import os
import uuid
import shutil
from datetime import datetime, timezone, timedelta
from typing import Optional

import psycopg2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# เวลาไทย UTC+7
TZ_THAI = timezone(timedelta(hours=7))

app = FastAPI(
    title="Urban Cam Backend",
    version="2.0",
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

UPLOAD_FOLDER = os.environ.get(
    "UPLOAD_FOLDER", os.path.join(os.getcwd(), "upload_2cam")
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", 5432)),
    "dbname":   os.environ.get("DB_NAME") or os.environ.get("POSTGRES_DB", "Project_499"),
    "user":     os.environ.get("DB_USER") or os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD") or os.environ.get("POSTGRES_PASSWORD", "357004"),
}

latest_gps: dict = {"lat": None, "lng": None, "accuracy": None}


def get_db():
    return psycopg2.connect(**DB_CONFIG)


# =========================
# STARTUP — สร้าง/อัปเดตตารางอัตโนมัติ
# =========================
@app.on_event("startup")
def on_startup():
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS two_cams (
                id          SERIAL PRIMARY KEY,
                filename    TEXT NOT NULL,
                device_id   TEXT,
                image_path  TEXT,
                side        TEXT,
                label       TEXT,
                lat         DOUBLE PRECISION,
                lng         DOUBLE PRECISION,
                accuracy    DOUBLE PRECISION,
                captured_at TIMESTAMPTZ DEFAULT NOW(),
                received_at TIMESTAMPTZ
            )
        """)

        # เพิ่มคอลัมน์ถ้าตารางเก่าไม่มี
        for col in ["lat", "lng", "accuracy"]:
            cur.execute(f"""
                ALTER TABLE two_cams
                ADD COLUMN IF NOT EXISTS {col} DOUBLE PRECISION
            """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ DB พร้อมใช้งาน")
    except Exception as e:
        print(f"❌ DB startup error: {e}")


# =========================
# ROUTES
# =========================
@app.get("/")
def root():
    return {"service": "urban_cam", "version": "2.0", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# รับภาพ + GPS จาก app.py
# =========================
@app.post("/ucs/api/upload", status_code=201)
async def upload(
    image:     UploadFile = File(...),
    device_id: str        = Form("CAM_001"),
    lat:       Optional[float] = Form(None),
    lng:       Optional[float] = Form(None),
    accuracy:  Optional[float] = Form(None),
):
    # 1. บันทึกไฟล์
    filename  = str(uuid.uuid4())[:8] + ".jpg"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เขียนไฟล์ไม่ได้: {e}")
    finally:
        await image.close()

    # 2. ใช้ค่า GPS ล่าสุดจากโทรศัพท์
    lat_val   = lat
    lng_val   = lng
    acc_val   = accuracy
    side      = "left" if "LEFT" in device_id.upper() else "right"

    # เวลาไทย
    now_thai = datetime.now(TZ_THAI)

    print(f"📥 {device_id} | lat={lat_val} lng={lng_val} | {now_thai.strftime('%H:%M:%S')}")

    # 3. บันทึก DB
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO two_cams
                (filename, device_id, image_path, side, lat, lng, accuracy, captured_at)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (filename, device_id, file_path, side, lat_val, lng_val, acc_val, now_thai))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ บันทึก DB id={new_id}")
    except Exception as e:
        print(f"❌ DB error: {e}")
        return {"ok": True, "filename": filename, "db_error": str(e)}

    return {"ok": True, "id": new_id, "filename": filename}


# legacy path
@app.post("/upload", status_code=201)
async def upload_legacy(
    image:     UploadFile = File(...),
    device_id: str        = Form("CAM_001"),
):
    return await upload(image, device_id)


# =========================
# ดึงรายการภาพจาก DB
# =========================
@app.get("/ucs/api/captures")
def get_captures(request: Request):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, filename, device_id, side, label, captured_at, lat, lng
            FROM two_cams
            ORDER BY captured_at DESC
            LIMIT 100
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    result = []
    for r in rows:
        # แปลงเวลาเป็น UTC+7 ถ้ายังเป็น UTC อยู่
        cap_time = r[5]
        if cap_time and hasattr(cap_time, 'tzinfo') and cap_time.tzinfo is not None:
            cap_time = cap_time.astimezone(TZ_THAI)
            cap_time_str = cap_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            cap_time_str = str(cap_time)

        result.append({
            "id":          r[0],
            "filename":    r[1],
            "image_url":   str(request.url_for("get_image", filename=r[1])),
            "device_id":   r[2],
            "side":        r[3],
            "label":       r[4],
            "captured_at": cap_time_str,
            "lat":         r[6],
            "lng":         r[7],
        })
    return result


# =========================
# ดึงไฟล์ภาพ
# =========================
@app.get("/ucs/api/image/{filename}")
def get_image(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="ไม่พบไฟล์")
    return FileResponse(file_path)


# =========================
# ลบภาพและข้อมูลจาก DB
@app.delete("/ucs/api/captures/{filename}")
def delete_capture(filename: str):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT filename FROM two_cams WHERE filename = %s", (filename,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="ไม่พบรายการภาพ")

        filename = row[0]
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"ลบไฟล์ภาพไม่ได้: {e}")

        cur.execute("DELETE FROM two_cams WHERE filename = %s", (filename,))
        conn.commit()
        return {"ok": True, "filename": filename, "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


# =========================
# รับ GPS จาก app.py
# =========================
class GPSPayload(BaseModel):
    lat:      Optional[float] = None
    lng:      Optional[float] = None
    accuracy: Optional[float] = None
    device:   Optional[str]   = None


@app.post("/ucs/api/gps")
def receive_gps(payload: GPSPayload):
    global latest_gps
    latest_gps = {
        "lat": payload.lat,
        "lng": payload.lng,
        "accuracy": payload.accuracy
    }
    now_thai = datetime.now(TZ_THAI)
    print(f"📍 GPS อัปเดต: {payload.lat}, {payload.lng} ±{payload.accuracy}m | {now_thai.strftime('%H:%M:%S')}")
    return {"ok": True}


@app.get("/ucs/api/gps/latest")
def get_latest_gps():
    return latest_gps or {"message": "ยังไม่มีข้อมูล GPS"}