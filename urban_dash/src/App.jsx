import { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import "./App.css";

// แก้ icon Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// const SERVER = import.meta.env.VITE_API_URL || "http://localhost:8000";
const SERVER = import.meta.env.VITE_API_URL || "http://localhost:6601";
const API_BASE = SERVER.replace(/\/ucs\/api\/?$/, "").replace(/\/$/, "") + "/ucs/api";
const CAPTURE_ENDPOINT = `${API_BASE}/capture`;
const CAPTURES_ENDPOINT = `${API_BASE}/captures`;
const IMAGE_ENDPOINT = `${API_BASE}/image`;
console.log("API URL:", API_BASE);
export default function App() {
  const [captures, setCaptures] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [captureStatus, setCaptureStatus] = useState("");

  useEffect(() => {
    fetchCaptures();
    const interval = setInterval(fetchCaptures, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchCaptures = async () => {
    try {
      const res = await fetch(CAPTURES_ENDPOINT);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setCaptures(data);
      if (!selected && data.length) {
        setSelected(data[0]);
      }
    } catch (err) {
      console.error("ดึงข้อมูลไม่ได้", err);
      setCaptureStatus("ไม่สามารถดึงข้อมูลได้");
    }
  };

  const startCapture = async () => {
    setLoading(true);
    setCaptureStatus("กำลังจับภาพ...");

    try {
      const res = await fetch(CAPTURE_ENDPOINT, { method: "POST" });
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      setCaptureStatus(`จับภาพสำเร็จ (${data.timestamp})`);
      await fetchCaptures();
    } catch (err) {
      console.error("จับภาพไม่สำเร็จ", err);
      setCaptureStatus("จับภาพไม่สำเร็จ ลองใหม่อีกครั้ง");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">

      {/* Header */}
      <div className="header">
        <span>📡</span>
        <span className="header-title">Urban Dashboard</span>
        <span className="header-status">
          ● LIVE — {captures.length} ภาพ
        </span>
      </div>

      {/* Capture control */}
      <div className="action-bar">
        <button className="capture-button" onClick={startCapture} disabled={loading}>
          {loading ? "กำลังจับภาพ..." : "Start Capture"}
        </button>
        <span className="capture-status">{captureStatus}</span>
      </div>

      {/* Map */}
      <div className="map-container">
        <MapContainer
          center={[18.7953, 98.9796]}
          zoom={15}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {captures
            .filter(c => c.latitude && c.longitude)
            .map(c => (
              <Marker key={c.id} position={[c.latitude, c.longitude]}>
                <Popup>
                  {c.device_id} | {c.side === "left" ? "ซ้าย" : "ขวา"}<br />
                  {c.captured_at?.slice(0, 19)}
                </Popup>
              </Marker>
            ))}
        </MapContainer>
      </div>

      {/* Bottom */}
      <div className="bottom">

        {/* Left */}
        <div className="left">
          {selected ? (
            <div className="image-box">
              <p className="image-text">
                {selected.device_id} | {selected.side === "left" ? "🟢 ซ้าย" : "🟡 ขวา"} | {selected.captured_at?.slice(0, 19)}
              </p>
              <img
                src={`${IMAGE_ENDPOINT}/${selected.filename}`}
                alt="capture"
                className="image"
              />
            </div>
          ) : (
            <div className="placeholder">
              <div style={{ fontSize: 40 }}>🖼️</div>
              <p>กดรายการทางขวาเพื่อดูรูปภาพ</p>
            </div>
          )}
        </div>

        {/* Right */}
        <div className="right">
          <h3 className="table-title">
            📋 ข้อมูลทั้งหมด ({captures.length})
          </h3>

          <div className="table-wrapper">
            <table className="table">
              <thead className="thead">
                <tr>
                  {["#", "กล้อง", "ฝั่ง", "เวลา"].map(h => (
                    <th key={h} className="th">{h}</th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {captures.map(c => (
                  <tr
                    key={c.id}
                    onClick={() => setSelected(c)}
                    className={`tr ${selected?.id === c.id ? "active" : ""}`}
                  >
                    <td className="td">{c.id}</td>
                    <td className="td">{c.device_id}</td>
                    <td className="td">
                      <span className={`badge ${c.side}`}>
                        {c.side === "left" ? "ซ้าย" : "ขวา"}
                      </span>
                    </td>
                    <td className="td">
                      {c.captured_at?.slice(11, 19)}
                    </td>
                  </tr>
                ))}
              </tbody>

            </table>
          </div>

          <div className="gallery-grid">
            {captures.map(c => (
              <div key={c.id} className="gallery-item" onClick={() => setSelected(c)}>
                <img src={`${IMAGE_ENDPOINT}/${c.filename}`} alt={c.filename} />
                <div className="gallery-caption">
                  {c.device_id} • {c.captured_at?.slice(11, 19)}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}