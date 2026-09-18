/**
 * Di-Tender 4IR — 3D Holographic Bid Go/No-Go Decision Gyroscope & TEC Matrix (decision-3d.js)
 * Grounding: CPTU PPR-2008 & Government Tender Evaluation Committee (TEC) Guidelines
 */

function safeRoundRect(ctx, x, y, w, h, r = 8) {
  if (w <= 0 || h <= 0) return;
  r = Math.min(r, w / 2, h / 2);
  if (typeof ctx.roundRect === 'function') {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
    return;
  }
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

class Decision3DVisualizer {
  constructor(canvasId = "decision3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.width = 800;
    this.height = 300;
    this.rotation = 0.44;
    this.tilt = 0.28;
    this.zoom = 1.0;
    this.mouse = { isDown: false, lastX: 0, lastY: 0 };
    this.time = 0;
    this.score = 88.0;
    this.verdict = "GO";

    this.updateDimensions();
    this.initEvents();
    this.initResizeObserver();
    this.startLoop();
  }

  updateDimensions() {
    if (!this.canvas) return;
    const parent = this.canvas.parentElement;
    const w = this.canvas.offsetWidth || (parent ? parent.clientWidth : 0) || 800;
    const h = this.canvas.offsetHeight || (parent ? parent.clientHeight : 0) || 300;
    if (w > 0 && h > 0 && (this.canvas.width !== w || this.canvas.height !== h)) {
      this.width = this.canvas.width = w;
      this.height = this.canvas.height = h;
    }
  }

  initResizeObserver() {
    if (typeof ResizeObserver !== 'undefined' && this.canvas) {
      const ro = new ResizeObserver(() => {
        this.updateDimensions();
      });
      ro.observe(this.canvas);
      if (this.canvas.parentElement) {
        ro.observe(this.canvas.parentElement);
      }
    }
  }

  initEvents() {
    if (typeof window !== 'undefined' && typeof window.addEventListener === 'function') {
      window.addEventListener('resize', () => {
        this.updateDimensions();
      });
      window.addEventListener('mouseup', () => {
        this.mouse.isDown = false;
      });
    }

    if (this.canvas && typeof this.canvas.addEventListener === 'function') {
      this.canvas.addEventListener('mousedown', (e) => {
        this.mouse.isDown = true;
        this.mouse.lastX = e.clientX;
        this.mouse.lastY = e.clientY;
      });

      this.canvas.addEventListener('mousemove', (e) => {
        if (this.mouse.isDown) {
          const dx = e.clientX - this.mouse.lastX;
          const dy = e.clientY - this.mouse.lastY;
          this.rotation += dx * 0.008;
          this.tilt = Math.max(-0.6, Math.min(0.6, this.tilt + dy * 0.008));
          this.mouse.lastX = e.clientX;
          this.mouse.lastY = e.clientY;
        }
      });

      this.canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        this.zoom = Math.max(0.6, Math.min(1.8, this.zoom - e.deltaY * 0.001));
      }, { passive: false });
    }
  }

  setVerdict(score, verdict = "GO") {
    this.score = score;
    this.verdict = verdict;
  }

  project3D(x, y, z, cx, cy) {
    const cosR = Math.cos(this.rotation);
    const sinR = Math.sin(this.rotation);

    // Rotate around Y-axis
    const rotX = (x * cosR - z * sinR) * this.zoom;
    const rotZ = (x * sinR + z * cosR) * this.zoom;

    // Tilt around X-axis
    const cosT = Math.cos(this.tilt);
    const sinT = Math.sin(this.tilt);
    const rotY = (y * cosT - rotZ * sinT) * this.zoom;
    const finalZ = (y * sinT + rotZ * cosT) * this.zoom;

    const fov = 440;
    const scale = fov / (fov + finalZ + 290);

    return {
      x: cx + rotX * scale,
      y: cy + rotY * scale,
      scale: Math.max(0.2, scale),
      z: finalZ
    };
  }

  startLoop() {
    const animate = () => {
      this.render();
      requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }

  render() {
    this.updateDimensions();
    const ctx = this.ctx;
    if (!ctx) return;

    this.time += 0.02;

    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Dark Cybernetic Background
    const bgGrad = ctx.createRadialGradient(
      this.width / 2, this.height / 2, 20,
      this.width / 2, this.height / 2, Math.max(this.width, this.height) * 0.8
    );
    bgGrad.addColorStop(0, '#040d1a');
    bgGrad.addColorStop(0.5, '#020617');
    bgGrad.addColorStop(1, '#000000');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, this.width, this.height);

    const cx = this.width / 2;
    const cy = this.height / 2 + 10;

    // 2. Draw Gyroscope Concentric Gimbal Rings
    this.drawGimbalRings(ctx, cx, cy);

    // 3. Draw 5-Point Spider Web / Radar Pentagon
    this.drawDecisionPentagon(ctx, cx, cy);

    // 4. Draw Central Holographic Decision Orb
    this.drawDecisionOrb(ctx, cx, cy);

    // 5. Draw Top HUD Telemetry
    this.drawHUD(ctx);
  }

  drawGimbalRings(ctx, cx, cy) {
    ctx.save();
    const isGo = (this.verdict || "").includes("GO");
    const ringColor = isGo ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)';

    // Outer Ring (Financial Capacity)
    ctx.beginPath();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = ringColor;
    for (let theta = 0; theta <= Math.PI * 2; theta += 0.1) {
      const r = 150;
      const x = Math.cos(theta + this.time * 0.5) * r;
      const z = Math.sin(theta + this.time * 0.5) * r;
      const pt = this.project3D(x, 0, z, cx, cy);
      if (theta === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    }
    ctx.closePath();
    ctx.stroke();

    // Middle Ring (Solvency & Technical)
    ctx.beginPath();
    ctx.lineWidth = 1.2;
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.25)';
    for (let theta = 0; theta <= Math.PI * 2; theta += 0.1) {
      const r = 115;
      const y = Math.cos(theta - this.time * 0.6) * r;
      const z = Math.sin(theta - this.time * 0.6) * r;
      const pt = this.project3D(0, y, z, cx, cy);
      if (theta === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    }
    ctx.closePath();
    ctx.stroke();

    ctx.restore();
  }

  drawDecisionPentagon(ctx, cx, cy) {
    ctx.save();
    const axes = [
      { label: "Turnover Capacity (25p)", weight: 0.95, color: "#10b981" },
      { label: "Solvency Credit (25p)", weight: 0.90, color: "#38bdf8" },
      { label: "Past Track Record (20p)", weight: 0.85, color: "#a855f7" },
      { label: "Personnel & Plant (15p)", weight: 0.90, color: "#f59e0b" },
      { label: "Clean Cartel Check (15p)", weight: 1.00, color: "#34d399" }
    ];

    const count = axes.length;
    const maxR = 90;

    // Draw baseline pentagon grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1;
    [0.33, 0.66, 1.0].forEach(ratio => {
      ctx.beginPath();
      for (let i = 0; i < count; i++) {
        const angle = (i * 2 * Math.PI) / count - Math.PI / 2;
        const r = maxR * ratio;
        const x = Math.cos(angle) * r;
        const y = Math.sin(angle) * r;
        const pt = this.project3D(x, y, 0, cx, cy);
        if (i === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.closePath();
      ctx.stroke();
    });

    // Draw active score polygon
    ctx.beginPath();
    const isGo = (this.verdict || "").includes("GO");
    ctx.fillStyle = isGo ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)';
    ctx.strokeStyle = isGo ? '#10b981' : '#f59e0b';
    ctx.lineWidth = 2;

    const points = [];
    axes.forEach((axis, i) => {
      const angle = (i * 2 * Math.PI) / count - Math.PI / 2;
      const r = maxR * axis.weight;
      const x = Math.cos(angle) * r;
      const y = Math.sin(angle) * r;
      const pt = this.project3D(x, y, 0, cx, cy);
      points.push(pt);
      if (i === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    });
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Draw node vertices and labels
    points.forEach((pt, i) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4 * pt.scale, 0, Math.PI * 2);
      ctx.fillStyle = axes[i].color;
      ctx.fill();

      // Axis labels
      ctx.fillStyle = '#cbd5e1';
      ctx.font = `${Math.max(7.5, Math.floor(9 * pt.scale))}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      const angle = (i * 2 * Math.PI) / count - Math.PI / 2;
      const labelX = pt.x + Math.cos(angle) * 14;
      const labelY = pt.y + Math.sin(angle) * 12;
      ctx.fillText(axes[i].label, labelX, labelY);
    });

    ctx.restore();
  }

  drawDecisionOrb(ctx, cx, cy) {
    const center = this.project3D(0, 0, 0, cx, cy);
    const isGo = (this.verdict || "").includes("GO");
    const radius = 22 * center.scale;

    ctx.save();
    // Center glow
    const grad = ctx.createRadialGradient(center.x, center.y, 2, center.x, center.y, radius * 2);
    grad.addColorStop(0, isGo ? '#10b981' : '#f59e0b');
    grad.addColorStop(0.6, isGo ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)');
    grad.addColorStop(1, 'rgba(0,0,0,0)');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius * 2, 0, Math.PI * 2);
    ctx.fill();

    // Solid core badge
    ctx.fillStyle = '#09152b';
    ctx.strokeStyle = isGo ? '#34d399' : '#fbbf24';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Text Verdict
    ctx.fillStyle = '#ffffff';
    ctx.font = `bold ${Math.max(9, Math.floor(11 * center.scale))}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(this.verdict || "GO", center.x, center.y);
    ctx.restore();
  }

  drawHUD(ctx) {
    ctx.save();
    // Top Left Status Pill
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.4)';
    ctx.lineWidth = 1;
    safeRoundRect(ctx, 14, 14, 260, 48, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 10px monospace';
    ctx.fillText("FEASIBILITY & TEC GYROSCOPE", 24, 30);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px Inter, sans-serif';
    ctx.fillText("5 Evaluation Axes • Altura Decision Matrix", 24, 46);

    // Top Right Telemetry
    if (this.width > 300) {
      ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
      safeRoundRect(ctx, this.width - 210, 14, 196, 48, 8);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#34d399';
      ctx.font = 'bold 10px monospace';
      ctx.fillText(`SIMULATED TEC SCORE: ${this.score}/100`, this.width - 200, 30);

      ctx.fillStyle = '#e2e8f0';
      ctx.font = '9px monospace';
      ctx.fillText("VERDICT: RESPONSIVE TENDERER", this.width - 200, 46);
    }

    ctx.restore();
  }
}

// Global Export
window.Decision3DVisualizer = Decision3DVisualizer;
window.initDecision3D = function(canvasId = "decision3dCanvas") {
  if (window.decision3dInstance && window.decision3dInstance.canvas) {
    window.decision3dInstance.updateDimensions();
    return window.decision3dInstance;
  }
  const canvas = document.getElementById(canvasId);
  if (canvas) {
    window.decision3dInstance = new Decision3DVisualizer(canvasId);
    if (window.bidDecision) {
      window.bidDecision.visualizer = window.decision3dInstance;
    }
    return window.decision3dInstance;
  }
  return null;
};
