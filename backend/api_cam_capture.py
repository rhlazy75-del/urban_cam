import requests
import threading
import time
import os
import psycopg2
from datetime import datetime, timezone

# ==================== ตั้งค่ากล้อง ====================
CAMERA_IPS = [
    {"id": 1, "ip": "http://10.132.250.222"},
    {"id": 2, "ip": "http://10.132.250.159"},
]

# ==================== ตั้งค่า PostgreSQL ====================
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "Project_499",
    "user":     "postgres",
    "password": "357004",
}

# ==================== ตั้งค่าทั่วไป ====================
SAVE_DIR         = "upload_2cam"
INTERVAL_SECONDS = 10
TIMEOUT          = 10
# =======================================================

os.makedirs(SAVE_DIR, exist_ok=True)


def save_to_db(cam_id, filename, filepath, captured_at, received_at):
    """บันทึกข้อมูลลง PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur  = conn.cursor()
        cur.execute(
            """
            INSERT INTO api_cam
                (filename, device_id, image_path, captured_at, received_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (filename, f"CAM{cam_id}", filepath, captured_at, received_at)
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
    url    = f"{cam['ip']}/capture"

    captured_at = datetime.now(timezone.utc)

    try:
        response    = requests.get(url, timeout=TIMEOUT)
        received_at = datetime.now(timezone.utc)

        if response.status_code == 200:
            filename = f"cam{cam_id}_{timestamp}.jpg"
            filepath = os.path.abspath(f"{SAVE_DIR}/{filename}")

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


def main():
    print("=" * 45)
    print("  Dual ESP32-CAM Capture + PostgreSQL")
    print(f"  บันทึกที่: ./{SAVE_DIR}/")
    print(f"  ถ่ายทุก {INTERVAL_SECONDS} วินาที")
    print("  กด Ctrl+C เพื่อหยุด")
    print("=" * 45)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print("🗄️  เชื่อมต่อ PostgreSQL สำเร็จ ✅\n")
    except Exception as e:
        print(f"❌ เชื่อมต่อ PostgreSQL ไม่ได้: {e}")
        return

    try:
        while True:
            capture_all()
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n\n🛑 หยุดการทำงาน")


if __name__ == "__main__":
    main()