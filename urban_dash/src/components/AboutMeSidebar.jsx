import React from "react";
import { X } from "lucide-react";
import { ripple } from "../utils/ripple";

export default function AboutMeSidebar({ open, onClose }) {
    return (
        <>
            {open && <div className="backdrop" onClick={onClose} />}
            <aside className={`sidebar ${open ? "open" : ""}`}>
                <button className="close-btn ripple-target" onClick={(e) => { ripple(e); onClose(); }}>
                    <X size={16} />
                </button>
                <div className="avatar" />
                <h2>POOBED HANYURAPONG</h2>
                <span className="role">FRONT-END DEVELOPER</span>
                <ul className="info-list">
                    <li>hello</li>
                    <li>coco</li>
                    <li>everything any not be good</li>
                    <li>but there's something in every day</li>
                </ul>
                <hr />
                <div className="contact-list">
                    <span>EMAIL — name@example.com</span>
                    <span>INSTAGRAM — @name</span>
                </div>
            </aside>
        </>
    );
}