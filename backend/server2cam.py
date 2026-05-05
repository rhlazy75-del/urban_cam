import os
import uuid
import shutil
from datetime import datetime
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

def get_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "Project_499"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "357004"),
    )

@app.get("/")
def root():
    return {
        "service": "urban_cam backend",
        "status": "ok",
        "routes": [
            "/ucs/api/upload",
            "/ucs/api/captures",
            "/ucs/api/image/{filename}",
            "/backend",
            "/health",
            "/ucs/api/docs",
            "/ucs/api/redoc",
        ],
    }

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
