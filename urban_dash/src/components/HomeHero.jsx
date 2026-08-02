import React from "react";
import { ArrowRight, ArrowUpRight, ChevronDown } from "lucide-react";
import { ripple } from "../utils/ripple";
import cityWallpaper from "../assets/city_wallpaper.jpg";

const particles = Array.from({ length: 14 });

export default function HomeHero({ onOpenAboutMe, onOpenAboutPro, onGoResult }) {
    return (
        <section className="hero-cine">
            <div className="hero-bg">
                <div className="hero-photo" style={{ backgroundImage: `url(${cityWallpaper})` }} />
                {/* <div className="beam" />
                <div className="beam thin" />
                <div className="haze" /> */}
            </div>

            <div className="hero-overlay" />
            <div className="hero-overlay-bottom" />

            <header className="nav nav-abs">
                <span className="logo"> HENG </span>
                <button className="pill-btn ripple-target" onClick={(e) => { ripple(e); onOpenAboutMe(); }}>
                    about me
                </button>
            </header>

            <div className="hero-content">
                <span className="eyebrow">
                    <span className="dot" />
                    selected urban works
                </span>
                <h1 className="title">
                    Project - IoT & AI System for <span className="accent-word">Visual </span> Landscape <br />
                    Quality Assessment in Chiang Mai
                </h1>
                <p className="desc">
                    คำอธิบายคร่าวๆ หรือเป้าหมายของโปร...
                </p>
                <div className="btn-row">
                    <button className="btn-outline ripple-target" onClick={(e) => { ripple(e); onOpenAboutPro(); }}>
                        about project <ArrowRight size={15} />
                    </button>
                    <button className="btn-solid ripple-target" onClick={(e) => { ripple(e); onGoResult(); }}>
                        result project <ArrowUpRight size={15} />
                    </button>
                </div>
            </div>

            <div className="scroll-cue">
                <span>scroll</span>
                <ChevronDown size={14} />
            </div>
        </section>
    );
}