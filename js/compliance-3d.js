/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D Holographic CPTU Compliance Matrix & Statutory Radar Manifold (compliance-3d.js)
 * Grounding: Public Procurement Act 2006 & Public Procurement Rules 2008 (PPR-2008)
 * 
 * Renders an interactive 3D 9-pillar compliance radar lattice, polyhedral statutory shield,
 * holographic clause orbital nodes, and real-time RFP laser shredding telemetry.
 */

class Compliance3DVisualizer {
  constructor(canvasId = "compliance3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width = this.canvas.offsetWidth || 800;
    this.height = this.canvas.height = this.canvas.offsetHeight || 300;
    this.rotation = 0.48;
    this.tilt = 0.28;
    this.zoom = 1.0;
    this.mouse = { isDown: false, lastX: 0, lastY: 0 };
    this.time = 0;
    this.scanSweep = 0;
    this.readinessScore = 94.2;

    // 9 Statutory Pillars
    this.pillars = [
      { name: "Turnover", code: "ITT 14.1", score: 0.95, color: "#10b981", angle: 0 },
      { name: "Liquid Assets", code: "ITT 15.1", score: 0.88, color: "#f59e0b", angle: (Math.PI * 2 / 9) * 1 },
      { name: "Specific Exp", code: "ITT 16.1b", score: 0.92, color: "#10b981", angle: (Math.PI * 2 / 9) * 2 },
      { name: "General Exp", code: "ITT 16.1a", score: 1.0, color: "#38bdf8", angle: (Math.PI * 2 / 9) * 3 },
      { name: "Key Staff", code: "ITT 24.1", score: 0.96, color: "#10b981", angle: (Math.PI * 2 / 9) * 4 },
      { name: "Equipment", code: "ITT 25.1", score: 0.90, color: "#38bdf8", angle: (Math.PI * 2 / 9) * 5 },
      { name: "Tender Security", code: "ITT 31.1", score: 1.0, color: "#10b981", angle: (Math.PI * 2 / 9) * 6 },
      { name: "Subcontract", code: "ITT 22.1", score: 1.0, color: "#38bdf8", angle: (Math.PI * 2 / 9) * 7 },
      { name: "Non-Debarment", code: "ITT 18.1", score: 1.0, color: "#10b981", angle: (Math.PI * 2 / 9) * 8 }
    ];

    this.initEvents();
    this.initResizeObserver();
    this.startLoop();
  }

  initResizeObserver() {
    if (typeof ResizeObserver !== 'undefined' && this.canvas) {
      const ro = new ResizeObserver(entries => {
        for (let entry of entries) {
          const cr = entry.contentRect;
          if (cr.width > 0 && cr.height > 0) {
            this.width = this.canvas.width = cr.width;
            this.height = this.canvas.height = cr.height;
          }
        }
      });
      ro.observe(this.canvas);
    }
  }

  initEvents() {
    window.addEventListener('resize', () => {
      if (!this.canvas) return;
      this.width = this.canvas.width = this.canvas.offsetWidth || 800;
      this.height = this.canvas.height = this.canvas.offsetHeight || 300;
    });

    this.canvas.addEventListener('mousedown', (e) => {
      this.mouse.isDown = true;
      this.mouse.lastX = e.clientX;
      this.mouse.lastY = e.clientY;
    });

    window.addEventListener('mouseup', () => {
      this.mouse.isDown = false;
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

  triggerShredScan() {
    this.scanSweep = 1.0;
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
    const ctx = this.ctx;
    if (!ctx) return;

    this.time += 0.02;
    if (this.scanSweep > 0) {
      this.scanSweep = Math.max(0, this.scanSweep - 0.025);
    }

    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Cybernetic Deep Space Background
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

    // 2. Draw 3D 9-Pillar Radar Spider Grid
    this.drawRadarGrid(ctx, cx, cy);

    // 3. Draw 3D Polyhedral Compliance Shield
    this.drawComplianceShield(ctx, cx, cy);

    // 4. Draw 3D Pillar Nodes & Legal Tokens
    this.drawPillarNodes(ctx, cx, cy);

    // 5. Draw Central Proof Seal Core
    this.drawCentralProofCore(ctx, cx, cy);

    // 6. Draw Animated RFP Laser Shredding Beam
    if (this.scanSweep > 0) {
      this.drawLaserShredBeam(ctx, cx, cy);
    }

    // 7. Telemetry HUD Overlay
    this.drawHUD(ctx);
  }

  drawRadarGrid(ctx, cx, cy) {
    ctx.save();
    const maxR = 150;

    // Concentric threshold rings
    for (let pct = 0.25; pct <= 1.0; pct += 0.25) {
      ctx.beginPath();
      const r = maxR * pct;
      this.pillars.forEach((p, idx) => {
        const x = Math.cos(p.angle) * r;
        const z = Math.sin(p.angle) * r;
        const pt = this.project3D(x, 20, z, cx, cy);
        if (idx === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      });
      ctx.closePath();
      ctx.strokeStyle = pct === 1.0 ? 'rgba(56, 189, 248, 0.35)' : 'rgba(59, 130, 246, 0.12)';
      ctx.lineWidth = pct === 1.0 ? 1.5 : 1;
      ctx.stroke();
    }

    // Spokes from center
    this.pillars.forEach(p => {
      const x = Math.cos(p.angle) * maxR;
      const z = Math.sin(p.angle) * maxR;
      const pt = this.project3D(x, 20, z, cx, cy);
      const c = this.project3D(0, 20, 0, cx, cy);

      ctx.beginPath();
      ctx.moveTo(c.x, c.y);
      ctx.lineTo(pt.x, pt.y);
      ctx.strokeStyle = 'rgba(59, 130, 246, 0.18)';
      ctx.lineWidth = 1;
      ctx.stroke();
    });

    ctx.restore();
  }

  drawComplianceShield(ctx, cx, cy) {
    ctx.save();
    const maxR = 150;

    // Build 3D polyhedral polygon
    const points = this.pillars.map(p => {
      const r = maxR * p.score;
      const x = Math.cos(p.angle) * r;
      const z = Math.sin(p.angle) * r;
      return this.project3D(x, 0, z, cx, cy);
    });

    ctx.beginPath();
    points.forEach((pt, idx) => {
      if (idx === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    });
    ctx.closePath();

    // Translucent gradient fill
    const center = this.project3D(0, 0, 0, cx, cy);
    const grad = ctx.createRadialGradient(center.x, center.y, 10, center.x, center.y, 140);
    grad.addColorStop(0, 'rgba(16, 185, 129, 0.45)');
    grad.addColorStop(0.6, 'rgba(56, 189, 248, 0.3)');
    grad.addColorStop(1, 'rgba(14, 165, 233, 0.1)');
    ctx.fillStyle = grad;
    ctx.fill();

    // Glowing border outline
    ctx.strokeStyle = '#34d399';
    ctx.lineWidth = 2;
    ctx.shadowColor = '#10b981';
    ctx.shadowBlur = 10;
    ctx.stroke();

    ctx.restore();
  }

  drawPillarNodes(ctx, cx, cy) {
    ctx.save();
    const maxR = 150;

    this.pillars.forEach(p => {
      const r = maxR * p.score;
      const x = Math.cos(p.angle) * r;
      const z = Math.sin(p.angle) * r;
      const pt = this.project3D(x, 0, z, cx, cy);
      const nodeR = 12 * pt.scale;

      // Glowing node
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, nodeR, 0, Math.PI * 2);
      ctx.fillStyle = '#091f18';
      ctx.strokeStyle = p.color;
      ctx.lineWidth = 2 * pt.scale;
      ctx.fill();
      ctx.stroke();

      // Inner dot
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4 * pt.scale, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();

      // Outer label tag
      const labelPt = this.project3D(Math.cos(p.angle) * (maxR + 24), 0, Math.sin(p.angle) * (maxR + 24), cx, cy);
      ctx.fillStyle = '#ffffff';
      ctx.font = `bold ${Math.max(8, Math.floor(9 * labelPt.scale))}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(p.name, labelPt.x, labelPt.y - 4);

      ctx.fillStyle = '#94a3b8';
      ctx.font = `${Math.max(7, Math.floor(7.5 * labelPt.scale))}px monospace`;
      ctx.fillText(p.code, labelPt.x, labelPt.y + 6);
    });

    ctx.restore();
  }

  drawCentralProofCore(ctx, cx, cy) {
    const center = this.project3D(0, 0, 0, cx, cy);
    const radius = 24 * center.scale;

    ctx.save();
    // Central Emblem
    ctx.fillStyle = '#0f172a';
    ctx.strokeStyle = '#fbbf24';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#fbbf24';
    ctx.font = `bold ${Math.max(8, Math.floor(9 * center.scale))}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText("PPR-2008", center.x, center.y - 3);

    ctx.fillStyle = '#34d399';
    ctx.font = `${Math.max(7, Math.floor(7.5 * center.scale))}px monospace`;
    ctx.fillText("SAT 94%", center.x, center.y + 7);
    ctx.restore();
  }

  drawLaserShredBeam(ctx, cx, cy) {
    ctx.save();
    const beamY = -80 + (1 - this.scanSweep) * 160;
    const pLeft = this.project3D(-200, beamY, 0, cx, cy);
    const pRight = this.project3D(200, beamY, 0, cx, cy);

    ctx.beginPath();
    ctx.moveTo(pLeft.x, pLeft.y);
    ctx.lineTo(pRight.x, pRight.y);
    ctx.strokeStyle = `rgba(56, 189, 248, ${this.scanSweep})`;
    ctx.lineWidth = 3;
    ctx.shadowColor = '#38bdf8';
    ctx.shadowBlur = 15;
    ctx.stroke();

    ctx.restore();
  }

  drawHUD(ctx) {
    ctx.save();
    // Top Left Status Pill
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.4)';
    ctx.lineWidth = 1;
    ctx.roundRect(14, 14, 260, 48, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 10px monospace';
    ctx.fillText("CPTU COMPLIANCE RADAR MATRIX", 24, 30);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px Inter, sans-serif';
    ctx.fillText("9 Statutory Pillars • Prequalification Grade A+", 24, 46);

    // Top Right Telemetry
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
    ctx.roundRect(this.width - 210, 14, 196, 48, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#34d399';
    ctx.font = 'bold 10px monospace';
    ctx.fillText("STATUTORY READINESS: 94.2%", this.width - 200, 30);

    ctx.fillStyle = '#e2e8f0';
    ctx.font = '9px monospace';
    ctx.fillText("Rule 96-127 Compliance: SAT", this.width - 200, 46);

    ctx.restore();
  }

  updateDimensions() {
    if (!this.canvas) return;
    const w = this.canvas.offsetWidth || 800;
    const h = this.canvas.offsetHeight || 300;
    if (w > 0 && h > 0) {
      this.width = this.canvas.width = w;
      this.height = this.canvas.height = h;
    }
  }
}

// Global Export
window.Compliance3DVisualizer = Compliance3DVisualizer;
window.initCompliance3D = function(canvasId = "compliance3dCanvas") {
  if (window.compliance3dInstance && window.compliance3dInstance.canvas) {
    window.compliance3dInstance.updateDimensions();
    return window.compliance3dInstance;
  }
  const canvas = document.getElementById(canvasId);
  if (canvas) {
    window.compliance3dInstance = new Compliance3DVisualizer(canvasId);
    if (window.complianceMatrix) {
      window.complianceMatrix.visualizer = window.compliance3dInstance;
    }
    return window.compliance3dInstance;
  }
  return null;
};
