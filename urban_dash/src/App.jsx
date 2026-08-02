import React, { useState, useEffect } from "react";
import "./App.css";
import Loader from "./components/Loader";
import HomeHero from "./components/HomeHero";
import ResultPage from "./components/ResultPage";
import AboutMeSidebar from "./components/AboutMeSidebar";
import AboutProModal from "./components/AboutProModal";

export default function App() {
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState("home"); // 'home' | 'result'
  const [aboutMeOpen, setAboutMeOpen] = useState(false);
  const [aboutProOpen, setAboutProOpen] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 2400);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") {
        setAboutMeOpen(false);
        setAboutProOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const goResult = () => {
    setPage("result");
    setAboutProOpen(false);
    setAboutMeOpen(false);
  };
  const goHome = () => {
    setPage("home");
    setAboutMeOpen(false);
  };

  return (
    <div className="urban-root">
      <Loader loading={loading} />

      <div className="bg-grid" />
      <div className="ambient-glow a" />
      <div className="ambient-glow b" />

      {page === "home" && (
        <HomeHero
          onOpenAboutMe={() => setAboutMeOpen(true)}
          onOpenAboutPro={() => setAboutProOpen(true)}
          onGoResult={goResult}
        />
      )}

      {page === "result" && (
        <ResultPage onGoHome={goHome} onOpenAboutPro={() => setAboutProOpen(true)} />
      )}

      <AboutMeSidebar open={aboutMeOpen} onClose={() => setAboutMeOpen(false)} />
      <AboutProModal open={aboutProOpen} onClose={() => setAboutProOpen(false)} />
    </div>
  );
}