import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { ripple } from "../utils/ripple";

export default function AboutProModal({ open, onClose }) {
    const modalBodyRef = useRef(null);

    useEffect(() => {
        const root = modalBodyRef.current;
        if (!root) return;
        const targets = root.querySelectorAll("[data-reveal]");
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    const el = entry.target;
                    if (entry.isIntersecting) {
                        el.classList.add("is-visible");
                        el.classList.remove("is-past");
                    } else if (entry.boundingClientRect.top < 0) {
                        el.classList.remove("is-visible");
                        el.classList.add("is-past");
                    } else {
                        el.classList.remove("is-visible");
                        el.classList.remove("is-past");
                    }
                });
            },
            { root, threshold: 0.4, rootMargin: "-10% 0px -10% 0px" }
        );
        targets.forEach((t) => observer.observe(t));
        return () => observer.disconnect();
    }, []);

    return (
        <div className={`modal ${open ? "open" : ""}`}>
            <button className="close-btn ripple-target" onClick={(e) => { ripple(e); onClose(); }}>
                <X size={16} />
            </button>
            <div className="modal-vignette" />
            <div className="modal-body" ref={modalBodyRef}>
                <div className="modal-inner">
                    <div className="modal-image">
                        <div className="beam thin" />
                    </div>
                    <div className="modal-text">
                        <p data-reveal>เกี่ยวกับโปรเจกต์นี้</p>
                        <p data-reveal>บรรทัดรายละเอียดที่ 1 — อธิบายแนวคิดหรือที่มาของงาน ว่าทำไมถึงเริ่มโปรเจกต์นี้ขึ้นมา</p>
                        <p data-reveal>บรรทัดรายละเอียดที่ 2 — อธิบายกระบวนการทำงาน เครื่องมือ หรือขั้นตอนหลักที่ใช้</p>
                        <p data-reveal>บรรทัดรายละเอียดที่ 3 — อธิบายปัญหาที่เจอระหว่างทาง และวิธีที่แก้ไขมัน</p>
                        <p data-reveal>บรรทัดรายละเอียดที่ 4 — อธิบายผลลัพธ์หรือสิ่งที่ได้เรียนรู้จากโปรเจกต์นี้</p>
                        <p data-reveal>บรรทัดรายละเอียดที่ 5 — อธิบายประสบการณ์การทำ</p>
                        <p data-reveal>บรรทัดรายละเอียดที่ 6 — ปิดท้ายด้วยข้อความสรุป</p>
                    </div>
                    <div className="scroll-hint">— scroll —</div>
                </div>
            </div>
        </div>
    );
}