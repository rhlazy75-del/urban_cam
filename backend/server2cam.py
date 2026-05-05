import os, uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(os.getcwd(), "upload_2cam"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "Project_499"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "357004")
    )

@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"error": "no image"}), 400

    img   = request.files["image"]
    fname = str(uuid.uuid4())[:8] + ".jpg"
    img.save(os.path.join(UPLOAD_FOLDER, fname))

    device_id = request.form.get("device_id", "CAM_001")
    side      = "left" if "LEFT" in device_id else "right"

    db  = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO two_cams (filename, device_id, side)
        VALUES (%s, %s, %s) RETURNING id
    """, (fname, device_id, side))
    new_id = cur.fetchone()[0]
    db.commit()
    cur.close()
    db.close()

    print(f"[{datetime.now()}] รับภาพ #{new_id} | {device_id} | {side}")
    return jsonify({"ok": True, "id": new_id}), 201

@app.route("/api/captures")
def get_captures():
    db  = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT id, filename, device_id, side, label, captured_at
        FROM two_cams
        ORDER BY captured_at DESC
        LIMIT 100
    """)
    rows = cur.fetchall()
    cur.close()
    db.close()

    result = []
    for r in rows:
        result.append({
            "id":          r[0],
            "filename":    r[1],
            "device_id":   r[2],
            "side":        r[3],
            "label":       r[4],
            "captured_at": str(r[5])
        })
    return jsonify(result)

@app.route("/image/<filename>")
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    print("Server running at http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)