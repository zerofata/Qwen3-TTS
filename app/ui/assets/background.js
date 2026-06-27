() => {
  // Arcane shape-grid background for Qwen 3 TTS.
  // Adapted from the "shapes" codepen: a sparse field of small gold runes/motes
  // that gently bloom near the pointer and ripple on click. It carves itself
  // OUT behind the app chrome (panels, status strip, tabs, hero, footer) so the
  // content stays clean. Self-disables under reduced-motion, never intercepts
  // pointer events, caps density, and pauses when the tab is hidden.
  try {
    if (document.getElementById("arcane-bg")) return; // guard against re-runs

    var canvas = document.createElement("canvas");
    canvas.id = "arcane-bg";
    document.body.appendChild(canvas);
    var ctx = canvas.getContext("2d");

    // --- tuning -----------------------------------------------------------
    var GAP = 52;               // grid spacing (larger = sparser)
    var RADIUS_VMIN = 26;       // pointer influence radius (% of min viewport)
    var SPEED_IN = 0.45;
    var SPEED_OUT = 0.7;
    var REST_SCALE = 0.0;       // invisible at rest -> only blooms near pointer/wave
    var MIN_HOVER = 0.8;
    var MAX_HOVER = 2.4;
    var WAVE_SPEED = 1100;
    var WAVE_WIDTH = 200;
    var MASK_SELECTOR =
      ".arcane-panel, #status-strip, #app-hero, #app-footer, [role='tablist'], .tab-nav";

    // Arcane palette: mostly gold, occasional verdigris/ember/bone flecks.
    var GOLD = "#d9a441", GOLD_HI = "#f0c463", TEAL = "#3f9d91",
        EMBER = "#b5532a", BONE = "#e8dcc0";
    var PALETTE = [
      GOLD, GOLD, GOLD, GOLD_HI, GOLD_HI, GOLD, BONE, TEAL, GOLD, EMBER,
    ];
    var SHAPE_TYPES = ["dot", "dot", "spark", "diamond"];

    var reduce = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var grid = null, pointer = null, activity = 0, waves = [];
    var maskRects = [], frameCount = 0, maskOverride = false, running = true;
    var rafId = null;

    function rnd(a, b) { return a + Math.random() * (b - a); }
    function pick(a) { return a[(Math.random() * a.length) | 0]; }
    function smoothstep(t) { var c = Math.max(0, Math.min(1, t)); return c * c * (3 - 2 * c); }
    function dur(s) { return s <= 0 ? 1 : 1 - Math.pow(0.05, 1 / (60 * s)); }

    function drawShape(shape) {
      var s = shape.size;
      ctx.beginPath();
      if (shape.type === "dot") {
        ctx.arc(0, 0, s * 0.6, 0, Math.PI * 2);
      } else if (shape.type === "diamond") {
        ctx.moveTo(0, -s); ctx.lineTo(s * 0.62, 0);
        ctx.lineTo(0, s); ctx.lineTo(-s * 0.62, 0); ctx.closePath();
      } else { // spark: 4-point star
        for (var i = 0; i < 8; i++) {
          var a = (i * Math.PI) / 4 - Math.PI / 2;
          var r = i % 2 === 0 ? s : s * 0.32;
          var x = Math.cos(a) * r, y = Math.sin(a) * r;
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();
      }
      ctx.fill();
    }

    function build() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var W = window.innerWidth, H = window.innerHeight;
      canvas.width = W * dpr; canvas.height = H * dpr;
      canvas.style.width = W + "px"; canvas.style.height = H + "px";
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);

      var cols = Math.floor(W / GAP), rows = Math.floor(H / GAP);
      var offX = (W - (cols - 1) * GAP) / 2, offY = (H - (rows - 1) * GAP) / 2;
      var shapes = [];
      for (var r = 0; r < rows; r++) {
        for (var c = 0; c < cols; c++) {
          var type = pick(SHAPE_TYPES);
          shapes.push({
            x: offX + c * GAP, y: offY + r * GAP, type: type,
            color: pick(PALETTE), angle: rnd(0, Math.PI * 2),
            size: GAP * 0.16, scale: REST_SCALE,
            maxScale: rnd(MIN_HOVER, MAX_HOVER), hovered: false,
          });
        }
      }
      grid = { shapes: shapes, width: W, height: H };
    }

    function renderStatic() {
      // reduced-motion: draw the faint resting field once, no animation
      if (!grid) build();
      ctx.clearRect(0, 0, grid.width, grid.height);
    }

    function tick() {
      if (!running) return;
      if (!grid) { rafId = requestAnimationFrame(tick); return; }
      var shapes = grid.shapes, W = grid.width, H = grid.height;
      var radius = Math.min(W, H) * (RADIUS_VMIN / 100);
      var now = performance.now();
      ctx.clearRect(0, 0, W, H);
      activity *= 0.93;

      if (++frameCount % 10 === 0) {
        maskRects = Array.prototype.slice
          .call(document.querySelectorAll(MASK_SELECTOR))
          .map(function (el) { return el.getBoundingClientRect(); })
          .filter(function (r) { return r.width > 0 && r.height > 0; });
      }

      var maxDist = Math.sqrt(W * W + H * H);
      waves = waves.filter(function (w) {
        return ((now - w.startTime) / 1000) * WAVE_SPEED < maxDist + WAVE_WIDTH;
      });

      for (var i = 0; i < shapes.length; i++) {
        var shape = shapes[i];
        var pad = GAP / 2;
        var masked = !maskOverride && maskRects.some(function (r) {
          return shape.x >= r.left - pad && shape.x <= r.right + pad &&
                 shape.y >= r.top - pad && shape.y <= r.bottom + pad;
        });
        if (masked) {
          shape.scale += (0 - shape.scale) * dur(SPEED_OUT);
          if (shape.scale < 0.005) shape.scale = 0;
          continue;
        }

        var pInf = 0;
        if (pointer && activity > 0.001) {
          var dx = shape.x - pointer.x, dy = shape.y - pointer.y;
          var dist = Math.sqrt(dx * dx + dy * dy);
          pInf = smoothstep(1 - dist / radius) * activity;
          if (pInf > 0.05 && !shape.hovered) {
            shape.hovered = true;
            shape.maxScale = rnd(MIN_HOVER, MAX_HOVER);
            shape.angle = rnd(0, Math.PI * 2);
          } else if (pInf <= 0.05) shape.hovered = false;
        } else shape.hovered = false;

        var wInf = 0;
        for (var j = 0; j < waves.length; j++) {
          var wave = waves[j];
          var wr = ((now - wave.startTime) / 1000) * WAVE_SPEED;
          var wdx = shape.x - wave.x, wdy = shape.y - wave.y;
          var wd = Math.sqrt(wdx * wdx + wdy * wdy);
          var t = 1 - Math.abs(wd - wr) / WAVE_WIDTH;
          if (t > 0) wInf = Math.max(wInf, Math.sin(Math.PI * t));
        }

        var target = Math.max(
          REST_SCALE + pInf * (shape.maxScale - REST_SCALE),
          REST_SCALE + wInf * (shape.maxScale - REST_SCALE)
        );
        var f = target > shape.scale ? dur(SPEED_IN) : dur(SPEED_OUT);
        shape.scale += (target - shape.scale) * f;
        if (shape.scale < 0.02) continue;

        ctx.save();
        ctx.translate(shape.x, shape.y);
        ctx.rotate(shape.angle);
        ctx.scale(shape.scale, shape.scale);
        ctx.globalAlpha = Math.min(1, shape.scale) * 0.85;
        ctx.fillStyle = shape.color;
        ctx.shadowColor = shape.color;
        ctx.shadowBlur = 8;
        drawShape(shape);
        ctx.restore();
      }
      ctx.globalAlpha = 1;
      rafId = requestAnimationFrame(tick);
    }

    function triggerWave(x, y) {
      x = x === undefined ? window.innerWidth / 2 : x;
      y = y === undefined ? window.innerHeight * 0.4 : y;
      waves.push({ x: x, y: y, startTime: performance.now() });
      maskOverride = true;
      var delay = Math.sqrt(
        window.innerWidth * window.innerWidth +
        window.innerHeight * window.innerHeight
      ) / WAVE_SPEED;
      setTimeout(function () { maskOverride = false; }, delay * 1000);
    }

    build();
    if (reduce) {
      renderStatic();
    } else {
      rafId = requestAnimationFrame(tick);
      triggerWave(); // gentle opening shimmer
      window.addEventListener("pointermove", function (e) {
        pointer = { x: e.clientX, y: e.clientY };
        activity = 1;
      });
      window.addEventListener("click", function (e) { triggerWave(e.clientX, e.clientY); });
      document.addEventListener("visibilitychange", function () {
        running = !document.hidden;
        if (running) rafId = requestAnimationFrame(tick);
      });
    }

    var rt;
    window.addEventListener("resize", function () {
      clearTimeout(rt);
      rt = setTimeout(function () { build(); if (reduce) renderStatic(); }, 200);
    });
  } catch (e) {
    if (window.console && console.warn) console.warn("arcane-bg disabled:", e);
  }
}
