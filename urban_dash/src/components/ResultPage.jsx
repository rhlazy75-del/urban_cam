import React from "react";
import { ArrowLeft } from "lucide-react";
import { ripple } from "../utils/ripple";

export default function ResultPage({ onGoHome, onOpenAboutPro }) {
    return (
        <>
            <header className="nav">
                <span className="logo">HENG</span>
                <nav className="nav-links">
                    <button className="ripple-target" onClick={(e) => { ripple(e); onGoHome(); }}>
                        home
                    </button>
                    <button className="ripple-target" onClick={(e) => { ripple(e); onOpenAboutPro(); }}>
                        about project
                    </button>
                </nav>
            </header>

            <main className="result-main">
                <div className="result-head">
                    <h1>Results</h1>
                    <button className="back-link ripple-target" onClick={(e) => { ripple(e); onGoHome(); }}>
                        <ArrowLeft size={14} /> back to home
                    </button>
                </div>
                <div className="result-grid">
                    {Array.from({ length: 6 }).map((_, i) => (
                        <div className="result-card" key={i} />
                    ))}
                </div>
                <div className="bottom-badge-wrap">
                    <span className="eyebrow">
                        <span className="dot" />
                        Today's not this
                    </span>
                </div>
            </main>
        </>
    );
}