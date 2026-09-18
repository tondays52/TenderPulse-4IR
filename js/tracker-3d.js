/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D Isometric Bid Lifecycle Pipeline & Escalator Funnel (tracker-3d.js)
 * Renders an interactive 3D 5-stage escalator funnel with floating holographic bid tokens,
 * orbital energy particles, and real-time e-GP submission readiness telemetry.
 */

class Tracker3DEscalator {
  constructor(canvasId = "tracker3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.updateDimensions();
    this.rotation = 0.3;
    this.tilt = 0.42;
    this.mouse = { x: this.width / 2, y: this.height / 2, targetX: this.width / 2, targetY: this.height / 2 };

    this.currentActiveStage = 0;
    this.readinessScore = 96.4;
    this.activeBidCount = 7;
    this.activeTenderId = "984210";
    this.isRunning = false;
    this.animFrameId = null;

    // 5 Stages of Bangladesh e-GP Bid Lifecycle
    this.stages = [
      { id: "P1", name: "1. Discovery & TDS Audit", y: 45, radius: 140, color: "#38bdf8", bids: ["e-GP #984210", "LGED/2026/VR-42"] },
      { id: "P2", name: "2. SMT Formal Logic Proof", y: 20, radius: 115, color: "#60a5fa", bids: ["RHD/2026/W-104"] },
      { id: "P3", name: "3. BOQ Pricing & Nash Sweetspot", y: -5, radius: 90, color: "#fbbf24", bids: ["PWD/HOSP/2026-08"] },
      { id: "P4", name: "4. Bank Guarantee & Sec. Issued", y: -30, radius: 65, color: "#c084fc", bids: ["BWDB/RIVER/2026-99"] },
      { id: "P5", name: "5. e-GP Encrypted & Submitted", y: -55, radius: 40, color: "#34d399", bids: ["BREB/GRID/2026-11"] }
    ];

    this.particles = [];
    this.initEvents();
    this.startLoop();
  }

  updateDimensions() {
    if (!this.canvas) return;
    const w = this.canvas.offsetWidth || this.canvas.clientWidth || 800;
    const h = this.canvas.offsetHeight || this.canvas.clientHeight || 290;
    if (w > 0 && h > 0) {
      this.width = this.canvas.width = w;
      this.height = this.canvas.height = h;
    }
  }

  updateTenderStage(tenderId, phaseIndex, readinessPercent = 50, bidCount = 5) {
    this.activeTenderId = String(tenderId);
    this.currentActiveStage = Math.max(0, Math.min(4, phaseIndex));
    this.readinessScore = readinessPercent;
    this.activeBidCount = bidCount;

    // Reposition active tender token across the 5 platforms
    this.stages.forEach((stg, idx) => {
      stg.bids = stg.bids.filter(b => !b.includes(this.activeTenderId));
      if (idx === this.currentActiveStage) {
        stg.bids.unshift(`e-GP #${this.activeTenderId}`);
      }
    });
  }

  initEvents() {
    window.addEventListener('resize', () => {
      this.updateDimensions();
    });

    if (typeof ResizeObserver !== 'undefined' && this.canvas) {
      this.resizeObserver = new ResizeObserver(() => {
        this.updateDimensions();
      });
      this.resizeObserver.observe(this.canvas);
      if (this.canvas.parentElement) {
        this.resizeObserver.observe(this.canvas.parentElement);
      }
    }

    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.targetX = e.clientX - rect.left;
      this.mouse.targetY = e.clientY - rect.top;
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.mouse.targetX = this.width / 2;
      this.mouse.targetY = this.height / 2;
    });
  }

  project3D(x, y, z, cx, cy) {
    const cosR = Math.cos(this.rotation);
    const sinR = Math.sin(this.rotation);

    const rotX = x * cosR - z * sinR;
    const rotZ = x * sinR + z * cosR;

    const tilt = this.tilt + (this.mouse.y - cy) * 0.0008;
    const cosT = Math.cos(tilt);
    const sinT = Math.sin(tilt);
    const rotY = y * cosT - rotZ * sinT;
    const finalZ = y * sinT + rotZ * cosT;

    const fov = 420;
    const scale = fov / (fov + finalZ + 240);

    return {
      x: cx + rotX * scale,
      y: cy + rotY * scale,
      scale: scale,
      z: finalZ
    };
  }

  startLoop() {
    this.isRunning = true;
    const animate = () => {
      if (!this.isRunning) return;
      this.render();
      this.animFrameId = requestAnimationFrame(animate);
    };
    this.animFrameId = requestAnimationFrame(animate);
  }

  stop() {
    this.isRunning = false;
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    }
  }

  render() {
    const ctx = this.ctx;
    if (!ctx) return;

    if (this.width <= 10 || this.height <= 10) {
      this.updateDimensions();
    }

    ctx.clearRect(0, 0, this.width, this.height);

    const cx = this.width / 2;
    const cy = this.height / 2 + 10;

    // Smooth mouse interpolation
    this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
    this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

    // Continuous rotation
    this.rotation += 0.007;

    // Cyber Dark Background
    const bgGlow = ctx.createRadialGradient(cx, cy, 10, cx, cy, this.width * 0.65);
    bgGlow.addColorStop(0, "rgba(15, 23, 42, 0.95)");
    bgGlow.addColorStop(1, "rgba(2, 6, 23, 1)");
    ctx.fillStyle = bgGlow;
    ctx.fillRect(0, 0, this.width, this.height);

    // 1. Draw 3D Holographic Floor Wireframe Grid
    ctx.save();
    ctx.strokeStyle = "rgba(148, 163, 184, 0.08)";
    ctx.lineWidth = 1;
    for (let gz = -100; gz <= 100; gz += 25) {
      const p1 = this.project3D(-200, 60, gz, cx, cy);
      const p2 = this.project3D(200, 60, gz, cx, cy);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }
    ctx.restore();

    // 2. Draw 5 Escalating Funnel Rings
    this.stages.forEach((stg, idx) => {
      const isCurrentActive = idx === this.currentActiveStage;

      // Connect to next stage with vertical guide vectors
      if (idx < this.stages.length - 1) {
        const nextStg = this.stages[idx + 1];
        const numPillars = 4;
        for (let i = 0; i < numPillars; i++) {
          const ang = (Math.PI * 2 / numPillars) * i + this.rotation;
          const x1 = Math.cos(ang) * stg.radius;
          const z1 = Math.sin(ang) * stg.radius * 0.7;
          const x2 = Math.cos(ang) * nextStg.radius;
          const z2 = Math.sin(ang) * nextStg.radius * 0.7;

          const p1 = this.project3D(x1, stg.y, z1, cx, cy);
          const p2 = this.project3D(x2, nextStg.y, z2, cx, cy);

          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = isCurrentActive ? "rgba(56, 189, 248, 0.4)" : "rgba(148, 163, 184, 0.15)";
          ctx.setLineDash([2, 4]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }

      // Draw Orbit Ellipse
      const segments = 32;
      ctx.beginPath();
      for (let i = 0; i <= segments; i++) {
        const ang = (Math.PI * 2 / segments) * i;
        const x = Math.cos(ang) * stg.radius;
        const z = Math.sin(ang) * stg.radius * 0.7;
        const p = this.project3D(x, stg.y, z, cx, cy);
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.closePath();
      ctx.strokeStyle = isCurrentActive ? "#38bdf8" : stg.color;
      ctx.lineWidth = isCurrentActive ? 3.5 : (idx === 4 ? 3 : 1.5);
      ctx.stroke();

      // Platform Glow
      ctx.fillStyle = stg.color;
      ctx.globalAlpha = isCurrentActive ? 0.14 : 0.05;
      ctx.fill();
      ctx.globalAlpha = 1.0;

      // Draw Stage Label on the leading edge
      const labelP = this.project3D(stg.radius + 15, stg.y, 0, cx, cy);
      ctx.font = `${isCurrentActive ? '700' : '600'} ${Math.max(8, Math.round(9.5 * labelP.scale))}px "JetBrains Mono", monospace`;
      ctx.fillStyle = isCurrentActive ? "#ffffff" : stg.color;
      ctx.fillText(stg.name + (isCurrentActive ? " (ACTIVE)" : ""), labelP.x + 8, labelP.y + 3);

      // Draw Floating Bid Tokens on this Platform
      stg.bids.forEach((bidName, bidIdx) => {
        const bidAngle = this.rotation * 1.5 + (bidIdx * Math.PI * 2 / Math.max(1, stg.bids.length));
        const bx = Math.cos(bidAngle) * stg.radius;
        const bz = Math.sin(bidAngle) * stg.radius * 0.7;
        const bp = this.project3D(bx, stg.y - 8, bz, cx, cy);

        // Glowing Token
        ctx.fillStyle = isCurrentActive ? "#38bdf8" : stg.color;
        ctx.shadowColor = isCurrentActive ? "#38bdf8" : stg.color;
        ctx.shadowBlur = isCurrentActive ? 15 : 10;
        ctx.beginPath();
        ctx.arc(bp.x, bp.y, (isCurrentActive ? 6 : 4.5) * bp.scale, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Bright Center
        ctx.fillStyle = "#ffffff";
        ctx.beginPath();
        ctx.arc(bp.x, bp.y, 2 * bp.scale, 0, Math.PI * 2);
        ctx.fill();

        // Token Badge
        ctx.font = `600 ${Math.max(7, Math.round(8 * bp.scale))}px "Plus Jakarta Sans", sans-serif`;
        ctx.fillStyle = isCurrentActive ? "#38bdf8" : "#e2e8f0";
        ctx.fillText(bidName, bp.x + 6, bp.y - 4);
      });
    });

    // 3. Dynamic Escalator Particles (moving upwards from P1 to P5)
    if (Math.random() < 0.28) {
      this.particles.push({
        stageIdx: 0,
        angle: Math.random() * Math.PI * 2,
        y: this.stages[0].y,
        speedY: 0.8 + Math.random() * 0.5,
        life: 1.0,
        color: "#38bdf8"
      });
    }

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.y -= p.speedY;
      p.life -= 0.015;

      const totalYRange = this.stages[0].y - this.stages[4].y;
      const progress = Math.max(0, Math.min(1, (this.stages[0].y - p.y) / totalYRange));
      const currentRadius = this.stages[0].radius + (this.stages[4].radius - this.stages[0].radius) * progress;

      p.angle += 0.02;
      const px = Math.cos(p.angle) * currentRadius;
      const pz = Math.sin(p.angle) * currentRadius * 0.7;

      const proj = this.project3D(px, p.y, pz, cx, cy);
      ctx.fillStyle = progress > 0.8 ? "#34d399" : (progress > 0.4 ? "#fbbf24" : "#38bdf8");
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.beginPath();
      ctx.arc(proj.x, proj.y, 2.5 * proj.scale, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1.0;

      if (p.life <= 0 || p.y <= this.stages[4].y - 15) {
        this.particles.splice(i, 1);
      }
    }

    // 4. Top Telemetry HUD Overlay
    ctx.font = '700 10px "JetBrains Mono", monospace';
    ctx.fillStyle = "#34d399";
    ctx.fillText("● 4IR LIVE BID PIPELINE — 5 STAGES SYNCHRONIZED", 14, 22);

    ctx.font = '500 9px "JetBrains Mono", monospace';
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(`ACTIVE FLIGHT: 0${this.activeBidCount} BIDS | READINESS: ${this.readinessScore}% | TENDER #${this.activeTenderId} IN STAGE P${this.currentActiveStage + 1}`, 14, 38);
  }
}

// Global Singleton Initializer
window.Tracker3DEscalator = Tracker3DEscalator;
window.initTracker3DEscalator = function(canvasId = "tracker3dCanvas") {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  if (window.tracker3dInstance) {
    if (window.tracker3dInstance.canvas !== canvas) {
      if (typeof window.tracker3dInstance.stop === 'function') {
        window.tracker3dInstance.stop();
      }
      window.tracker3dInstance = new Tracker3DEscalator(canvasId);
    } else {
      window.tracker3dInstance.updateDimensions();
    }
  } else {
    window.tracker3dInstance = new Tracker3DEscalator(canvasId);
  }
  return window.tracker3dInstance;
};

