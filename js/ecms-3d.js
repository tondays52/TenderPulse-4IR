/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D Isometric Infrastructure Digital Twin & e-CMS Execution Terrain (ecms-3d.js)
 * Renders an interactive 3D Bridge Digital Twin (Piles, Pier Columns, Pier Caps,
 * Pre-stressed Girders, Deck Slab, Water Surface Mesh) with real-time milestone progress.
 */

class Ecms3DDigitalTwin {
  constructor(canvasId = "ecms3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.updateDimensions();
    this.rotation = 0.25;
    this.tilt = 0.35;
    this.mouse = { x: this.width / 2, y: this.height / 2, targetX: this.width / 2, targetY: this.height / 2 };
    this.waterOffset = 0;
    this.hoveredSegment = null;
    this.time = 0;

    // Infrastructure Components for 142m Meghna Girder Bridge
    this.piers = [
      { id: "ABUT-1", name: "Abutment 1 (West Approach)", x: -220, z: -10, height: 50, status: "COMPLETED", progress: 100, color: "#10b981" },
      { id: "PIER-1", name: "Pier P1 & Pile Cap (4 Nos Bauer Piles)", x: -110, z: 0, height: 75, status: "COMPLETED", progress: 100, color: "#10b981" },
      { id: "PIER-2", name: "Pier P2 (Main Navigation Channel)", x: 0, z: 10, height: 85, status: "IN_PROGRESS", progress: 65, color: "#38bdf8" },
      { id: "PIER-3", name: "Pier P3 & Pier Cap", x: 110, z: 0, height: 75, status: "IN_PROGRESS", progress: 40, color: "#fbbf24" },
      { id: "ABUT-2", name: "Abutment 2 (East Approach)", x: 220, z: -10, height: 50, status: "PENDING", progress: 10, color: "#94a3b8" }
    ];

    this.spans = [
      { id: "SPAN-1", name: "Span 1 (Girder Launched)", x1: -220, x2: -110, status: "COMPLETED", progress: 100, color: "#10b981" },
      { id: "SPAN-2", name: "Span 2 (Main Channel Girder)", x1: -110, x2: 0, status: "IN_PROGRESS", progress: 65, color: "#38bdf8" },
      { id: "SPAN-3", name: "Span 3 (Precast Segments Casting)", x1: 0, x2: 110, status: "PENDING", progress: 20, color: "#f59e0b" },
      { id: "SPAN-4", name: "Span 4 (Approaches Staging)", x1: 110, x2: 220, status: "PENDING", progress: 0, color: "#64748b" }
    ];

    this.initEvents();
    this.startLoop();
  }

  updateDimensions() {
    if (!this.canvas) return;
    const w = this.canvas.offsetWidth || this.canvas.clientWidth || 800;
    const h = this.canvas.offsetHeight || this.canvas.clientHeight || 310;
    if (w > 0 && h > 0) {
      this.width = this.canvas.width = w;
      this.height = this.canvas.height = h;
    }
  }

  initEvents() {
    // Window resize
    window.addEventListener('resize', () => {
      this.updateDimensions();
    });

    // ResizeObserver for zero-crash layout switching
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

    // Rotate around Y-axis
    const rotX = x * cosR - z * sinR;
    const rotZ = x * sinR + z * cosR;

    // Tilt around X-axis
    const tilt = this.tilt + (this.mouse.y - cy) * 0.0008;
    const cosT = Math.cos(tilt);
    const sinT = Math.sin(tilt);
    const rotY = y * cosT - rotZ * sinT;
    const finalZ = y * sinT + rotZ * cosT;

    const fov = 450;
    const scale = fov / (fov + finalZ + 250);

    return {
      x: cx + rotX * scale,
      y: cy + rotY * scale,
      scale: Math.max(0.1, scale),
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
    const ctx = this.ctx;
    if (!ctx) return;

    // Ensure valid dimensions
    if (this.width <= 10 || this.height <= 10) {
      this.updateDimensions();
    }

    ctx.clearRect(0, 0, this.width, this.height);

    const cx = this.width / 2;
    const cy = this.height / 2 + 20;

    // Smooth mouse interpolation
    this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
    this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

    // Subtle automatic oscillation
    this.rotation = 0.22 + Math.sin(Date.now() * 0.0006) * 0.08 + (this.mouse.x - cx) * 0.0006;
    this.waterOffset += 0.03;

    // Background Cyber Dark Gradient
    const bgGlow = ctx.createRadialGradient(cx, cy, 20, cx, cy, this.width * 0.7);
    bgGlow.addColorStop(0, "rgba(15, 23, 42, 0.95)");
    bgGlow.addColorStop(1, "rgba(2, 6, 23, 1)");
    ctx.fillStyle = bgGlow;
    ctx.fillRect(0, 0, this.width, this.height);

    // 1. Draw 3D Water Surface Mesh (Meghna River Bathymetry)
    ctx.save();
    ctx.strokeStyle = "rgba(56, 189, 248, 0.12)";
    ctx.lineWidth = 1;
    const riverY = 45;

    for (let rz = -80; rz <= 80; rz += 20) {
      ctx.beginPath();
      for (let rx = -280; rx <= 280; rx += 20) {
        const wave = Math.sin(rx * 0.04 + this.waterOffset + rz * 0.03) * 3;
        const p = this.project3D(rx, riverY + wave, rz, cx, cy);
        if (rx === -280) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
    }
    ctx.restore();

    // 2. Draw Bridge Deck / Girder Spans
    this.spans.forEach(span => {
      const p1Top = this.project3D(span.x1, -25, 0, cx, cy);
      const p2Top = this.project3D(span.x2, -25, 0, cx, cy);
      const p1Bottom = this.project3D(span.x1, -12, 0, cx, cy);
      const p2Bottom = this.project3D(span.x2, -12, 0, cx, cy);

      // Deck Girder Box
      ctx.beginPath();
      ctx.moveTo(p1Top.x, p1Top.y);
      ctx.lineTo(p2Top.x, p2Top.y);
      ctx.lineTo(p2Bottom.x, p2Bottom.y);
      ctx.lineTo(p1Bottom.x, p1Bottom.y);
      ctx.closePath();

      if (span.status === "COMPLETED") {
        ctx.fillStyle = "rgba(16, 185, 129, 0.28)";
        ctx.strokeStyle = "#10b981";
        ctx.lineWidth = 2;
      } else if (span.status === "IN_PROGRESS") {
        ctx.fillStyle = "rgba(56, 189, 248, 0.24)";
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 2;
      } else {
        ctx.fillStyle = "rgba(148, 163, 184, 0.06)";
        ctx.strokeStyle = "rgba(148, 163, 184, 0.3)";
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
      }

      ctx.fill();
      ctx.stroke();
      ctx.setLineDash([]);

      // Draw Top Roadway Surface
      const p1Back = this.project3D(span.x1, -25, -20, cx, cy);
      const p2Back = this.project3D(span.x2, -25, -20, cx, cy);

      ctx.beginPath();
      ctx.moveTo(p1Top.x, p1Top.y);
      ctx.lineTo(p2Top.x, p2Top.y);
      ctx.lineTo(p2Back.x, p2Back.y);
      ctx.lineTo(p1Back.x, p1Back.y);
      ctx.closePath();
      ctx.fillStyle = span.status === "COMPLETED" ? "rgba(16, 185, 129, 0.4)" : "rgba(30, 41, 59, 0.5)";
      ctx.fill();
      ctx.stroke();
    });

    // 3. Draw Piers, Pile Caps & Substructure
    this.piers.forEach(pier => {
      const baseP = this.project3D(pier.x, 40, pier.z, cx, cy);
      const topP = this.project3D(pier.x, -12, pier.z, cx, cy);
      const capWidth = 24 * topP.scale;
      const colWidth = 14 * baseP.scale;

      // Pier Column Shaft
      ctx.beginPath();
      ctx.moveTo(baseP.x - colWidth / 2, baseP.y);
      ctx.lineTo(topP.x - colWidth / 2, topP.y);
      ctx.lineTo(topP.x + colWidth / 2, topP.y);
      ctx.lineTo(baseP.x + colWidth / 2, baseP.y);
      ctx.closePath();

      const grad = ctx.createLinearGradient(baseP.x - colWidth, 0, baseP.x + colWidth, 0);
      if (pier.status === "COMPLETED") {
        grad.addColorStop(0, "rgba(16, 185, 129, 0.6)");
        grad.addColorStop(1, "rgba(5, 150, 105, 0.8)");
        ctx.strokeStyle = "#34d399";
      } else if (pier.status === "IN_PROGRESS") {
        grad.addColorStop(0, "rgba(56, 189, 248, 0.5)");
        grad.addColorStop(1, "rgba(2, 132, 199, 0.7)");
        ctx.strokeStyle = "#38bdf8";
      } else {
        grad.addColorStop(0, "rgba(51, 65, 85, 0.4)");
        grad.addColorStop(1, "rgba(30, 41, 59, 0.6)");
        ctx.strokeStyle = "#64748b";
      }

      ctx.fillStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.fill();
      ctx.stroke();

      // Pier Cap Block (Top)
      ctx.beginPath();
      ctx.rect(topP.x - capWidth / 2, topP.y - 6 * topP.scale, capWidth, 6 * topP.scale);
      ctx.fillStyle = pier.color;
      ctx.fill();
      ctx.stroke();

      // Underwater Pile Foundation Wireframe
      const pileTipP = this.project3D(pier.x, 75, pier.z, cx, cy);
      ctx.beginPath();
      ctx.moveTo(baseP.x, baseP.y);
      ctx.lineTo(pileTipP.x, pileTipP.y);
      ctx.strokeStyle = "rgba(148, 163, 184, 0.25)";
      ctx.setLineDash([2, 3]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Node Label
      ctx.font = `700 ${Math.max(8, Math.round(9.5 * topP.scale))}px "JetBrains Mono", monospace`;
      ctx.fillStyle = pier.color;
      ctx.fillText(pier.id, topP.x - 14, topP.y - 12);

      // Percentage Pill
      ctx.font = `600 ${Math.max(8, Math.round(8.5 * topP.scale))}px "Plus Jakarta Sans", sans-serif`;
      ctx.fillStyle = "#cbd5e1";
      ctx.fillText(`${pier.progress}%`, topP.x - 10, topP.y + 14);
    });

    // 4. Progress InSAR Coherence Ray (Sentinel-1 SAR Satellite Sweep)
    const scanX = cx + Math.sin(Date.now() * 0.0015) * (this.width * 0.35);
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(scanX, 10);
    ctx.lineTo(scanX - 45, cy + 60);
    ctx.lineTo(scanX + 45, cy + 60);
    ctx.closePath();
    ctx.fillStyle = "rgba(56, 189, 248, 0.08)";
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(scanX, 10);
    ctx.lineTo(scanX, cy + 60);
    ctx.strokeStyle = "rgba(56, 189, 248, 0.6)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([3, 3]);
    ctx.stroke();
    ctx.restore();

    // Satellite Icon Indicator on Beam
    ctx.beginPath();
    ctx.arc(scanX, 12, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#38bdf8";
    ctx.fill();

    // 5. HUD Telemetry Overlay
    ctx.font = '700 10px "JetBrains Mono", monospace';
    ctx.fillStyle = "#38bdf8";
    ctx.fillText("🛰️ SENTINEL-1A C-SAR ORBITAL COHERENCE — 142m MEGHNA BRIDGE", 14, 22);

    ctx.font = '500 9px "JetBrains Mono", monospace';
    ctx.fillStyle = "#94a3b8";
    ctx.fillText("RADAR REFLECTION: +14.2 dB | GROUND TRUTH: 46.2% | MB CLAIMED: 44.5% (SAT)", 14, 38);
  }
}

// Global Singleton Initializers & Aliases
window.Ecms3DDigitalTwin = Ecms3DDigitalTwin;
window.initEcms3DDigitalTwin = function(canvasId = "ecms3dCanvas") {
  if (!window.ecmsTwinInstance && document.getElementById(canvasId)) {
    window.ecmsTwinInstance = new Ecms3DDigitalTwin(canvasId);
  }
  return window.ecmsTwinInstance;
};
window.initEcms3D = window.initEcms3DDigitalTwin;
