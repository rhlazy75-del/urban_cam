import { useState, useEffect } from "react";
import axios from "axios";
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

const SERVER = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [captures, setCaptures] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetchCaptures();
    const interval = setInterval(fetchCaptures, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchCaptures = async () => {
    try {
      const res = await axios.get(`${SERVER}/ucs/api/captures`);
      setCaptures(res.data);
    } catch (err) {
      console.error("ดึงข้อมูลไม่ได้", err);
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
                src={`${SERVER}/ucs/api/image/${selected.filename}`}
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
        </div>

      </div>
    </div>
  );
}