() => {
  // Ambient "arcane embers" background for Qwen 3 TTS.
  // Subtle drifting motes behind the UI. Self-disables under reduced-motion,
  // never intercepts pointer events, caps density, and pauses when hidden.
  try {
    if (document.getElementById("arcane-bg")) return;            // guard re-runs
    const reduce = window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;

    const canvas = document.createElement("canvas");
    canvas.id = "arcane-bg";
    document.body.appendChild(canvas);
    const ctx = canvas.getContext("2d");

    let w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
    let motes = [];

    const AMBER = [232, 184, 92];
    const VIOLET = [177, 139, 255];

    function rand(a, b) { return a + Math.random() * (b - a); }

    function build() {
      w = canvas.width = Math.floor(innerWidth * dpr);
      h = canvas.height = Math.floor(innerHeight * dpr);
      canvas.style.width = innerWidth + "px";
      canvas.style.height = innerHeight + "px";
      // Density scales with area but stays low; hard cap for performance.
      const count = Math.min(70, Math.floor((innerWidth * innerHeight) / 26000));
      motes = [];
      for (let i = 0; i < count; i++) {
        const col = Math.random() < 0.6 ? AMBER : VIOLET;
        motes.push({
          x: Math.random() * w,
          y: Math.random() * h,
          r: rand(0.6, 2.2) * dpr,
          vy: -rand(0.06, 0.30) * dpr,        // drift upward like embers
          vx: rand(-0.10, 0.10) * dpr,
          a: rand(0.10, 0.55),
          tw: rand(0.004, 0.014),             // twinkle speed
          ph: Math.random() * Math.PI * 2,
          col: col,
        });
      }
    }

    let running = true;
    function frame() {
      if (!running) return;
      ctx.clearRect(0, 0, w, h);
      for (const m of motes) {
        m.x += m.vx;
        m.y += m.vy;
        m.ph += m.tw;
        if (m.y < -10) { m.y = h + 10; m.x = Math.random() * w; }
        if (m.x < -10) m.x = w + 10;
        if (m.x > w + 10) m.x = -10;
        const alpha = m.a * (0.6 + 0.4 * Math.sin(m.ph));
        const g = ctx.createRadialGradient(m.x, m.y, 0, m.x, m.y, m.r * 6);
        g.addColorStop(0, `rgba(${m.col[0]},${m.col[1]},${m.col[2]},${alpha})`);
        g.addColorStop(1, `rgba(${m.col[0]},${m.col[1]},${m.col[2]},0)`);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(m.x, m.y, m.r * 6, 0, Math.PI * 2);
        ctx.fill();
      }
      requestAnimationFrame(frame);
    }

    build();
    requestAnimationFrame(frame);

    let rt;
    window.addEventListener("resize", () => {
      clearTimeout(rt);
      rt = setTimeout(build, 200);
    });
    document.addEventListener("visibilitychange", () => {
      running = !document.hidden;
      if (running) requestAnimationFrame(frame);
    });
  } catch (e) {
    // Never let the ambient effect break the app.
    console && console.warn && console.warn("arcane-bg disabled:", e);
  }
}
