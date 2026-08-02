export function ripple(e) {
    const btn = e.currentTarget;
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    btn.style.setProperty("--x", `${x}px`);
    btn.style.setProperty("--y", `${y}px`);
    btn.classList.remove("rippling");
    void btn.offsetWidth; // force reflow เพื่อให้เล่นอนิเมชันซ้ำได้
    btn.classList.add("rippling");
    setTimeout(() => btn.classList.remove("rippling"), 650);
}