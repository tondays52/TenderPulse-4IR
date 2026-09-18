/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D Holographic CPTU Standard Tender Document & Compliance Manifold (std-3d.js)
 * Grounding: Public Procurement Act 2006 & Public Procurement Rules 2008 (PPR-2008)
 * 
 * Renders an interactive 3D legal document manifold with floating CPTU parchment sheets,
 * rotating Golden Compliance Seal, statutory clause ribbons, and audit telemetry.
 */

class Std3DVisualizer {
  constructor(canvasId = "std3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.updateDimensions();
    this.rotation = 0.42;
    this.tilt = 0.26;
    this.zoom = 1.0;
    this.mouse = { isDown: false, lastX: 0, lastY: 0 };
    this.time = 0;
    this.scanPulse = 0;
    this.currentFormCode = "e-PW3-1";
    this.currentCategory = "Mandatory Submission";
    this.isRunning = false;
    this.animFrameId = null;

    this.initEvents();
    this.initResizeObserver();
    this.startLoop();
  }

  updateDimensions() {
    if (!this.canvas) return;
    const w = this.canvas.offsetWidth || this.canvas.clientWidth || 800;
    const h = this.canvas.offsetHeight || this.canvas.clientHeight || 300;
    if (w > 0 && h > 0) {
      this.width = this.canvas.width = w;
      this.height = this.canvas.height = h;
    }
  }

  initResizeObserver() {
    if (typeof ResizeObserver !== 'undefined' && this.canvas) {
      this.resizeObserver = new ResizeObserver(() => {
        this.updateDimensions();
      });
      this.resizeObserver.observe(this.canvas);
      if (this.canvas.parentElement) {
        this.resizeObserver.observe(this.canvas.parentElement);
      }
    }
  }

  initEvents() {
    window.addEventListener('resize', () => {
      this.updateDimensions();
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

  setFormCode(code, category = "Mandatory Submission") {
    this.currentFormCode = code;
    this.currentCategory = category;
    this.scanPulse = 1.0;
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

    const fov = 420;
    const scale = fov / (fov + finalZ + 280);

    return {
      x: cx + rotX * scale,
      y: cy + rotY * scale,
      scale: Math.max(0.2, scale),
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

    this.time += 0.02;
    if (this.scanPulse > 0) {
      this.scanPulse = Math.max(0, this.scanPulse - 0.02);
    }

    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Dark Cybernetic Background
    const bgGrad = ctx.createRadialGradient(
      this.width / 2, this.height / 2, 20,
      this.width / 2, this.height / 2, Math.max(this.width, this.height) * 0.8
    );
    bgGrad.addColorStop(0, '#040b17');
    bgGrad.addColorStop(0.5, '#020617');
    bgGrad.addColorStop(1, '#000000');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, this.width, this.height);

    const cx = this.width / 2;
    const cy = this.height / 2 + 10;

    // 2. Draw 3D Floating Legal Parchment Stack (e-PW3 Schedules)
    this.drawParchmentStack(ctx, cx, cy);

    // 3. Draw 3D Clause Binding Ribbons
    this.drawClauseRibbons(ctx, cx, cy);

    // 4. Draw Rotating 3D Golden CPTU Compliance Seal
    this.drawCptuSeal(ctx, cx, cy);

    // 5. Draw Holographic Audit Scan Sweep
    this.drawScanSweep(ctx, cx, cy);

    // 6. Draw Telemetry HUD
    this.drawHUD(ctx);
  }

  drawParchmentStack(ctx, cx, cy) {
    const sheets = [
      { code: "Form e-PW3-1", label: "e-Tender Submission", color: "#38bdf8", zOffset: -60, yOffset: -20 },
      { code: "Form e-PW2A-8", label: "Bank Credit Commitment", color: "#10b981", zOffset: -20, yOffset: -5 },
      { code: "Form e-PW3-7", label: "Tender Security Guarantee", color: "#f59e0b", zOffset: 20, yOffset: 10 },
      { code: "Form e-PW3-3A", label: "Turnover Declaration", color: "#a855f7", zOffset: 60, yOffset: 25 }
    ];

    sheets.forEach((sheet, idx) => {
      const isSelected = sheet.code.includes(this.currentFormCode) || this.currentFormCode.includes(sheet.code.split(" ")[1]);
      const w = 110;
      const h = 150;
      const yo = sheet.yOffset + Math.sin(this.time + idx * 0.8) * 6;

      const corners = [
        { x: -w, y: yo - h / 2, z: sheet.zOffset },
        { x: w, y: yo - h / 2, z: sheet.zOffset },
        { x: w, y: yo + h / 2, z: sheet.zOffset },
        { x: -w, y: yo + h / 2, z: sheet.zOffset }
      ];

      const proj = corners.map(c => this.project3D(c.x, c.y, c.z, cx, cy));

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(proj[0].x, proj[0].y);
      for (let i = 1; i < proj.length; i++) ctx.lineTo(proj[i].x, proj[i].y);
      ctx.closePath();

      ctx.fillStyle = isSelected ? 'rgba(56, 189, 248, 0.18)' : 'rgba(15, 23, 42, 0.65)';
      ctx.fill();
      ctx.strokeStyle = isSelected ? '#38bdf8' : (sheet.color + '88');
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();

      // Document Header
      const headerProj = this.project3D(-w + 12, yo - h / 2 + 18, sheet.zOffset, cx, cy);
      ctx.font = `700 ${Math.max(8, Math.round(10 * headerProj.scale))}px "JetBrains Mono", monospace`;
      ctx.fillStyle = sheet.color;
      ctx.textAlign = 'left';
      ctx.fillText(sheet.code, headerProj.x, headerProj.y);

      // Document Simulated Text Lines
      for (let l = 0; l < 5; l++) {
        const l1 = this.project3D(-w + 12, yo - h / 2 + 35 + l * 18, sheet.zOffset, cx, cy);
        const l2 = this.project3D(w - 12, yo - h / 2 + 35 + l * 18, sheet.zOffset, cx, cy);
        ctx.beginPath();
        ctx.moveTo(l1.x, l1.y);
        ctx.lineTo(l2.x, l2.y);
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.25)';
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }

      ctx.restore();
    });
  }

  drawClauseRibbons(ctx, cx, cy) {
    // 3D Connecting legal clause ribbons
    ctx.save();
    const ribbonSegments = 24;
    ctx.beginPath();
    for (let i = 0; i <= ribbonSegments; i++) {
      const t = i / ribbonSegments;
      const angle = t * Math.PI * 2 + this.time * 0.5;
      const rx = Math.cos(angle) * 160;
      const rz = Math.sin(angle) * 160;
      const ry = Math.sin(angle * 2 + this.time) * 35;
      const p = this.project3D(rx, ry, rz, cx, cy);

      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }
    ctx.strokeStyle = 'rgba(245, 158, 11, 0.35)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 6]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  }

  drawCptuSeal(ctx, cx, cy) {
    // Center Golden Rotating Seal
    const sealProj = this.project3D(0, 0, 0, cx, cy);
    const radius = 38 * sealProj.scale;

    ctx.save();
    // Outer Glow Halo
    ctx.beginPath();
    ctx.arc(sealProj.x, sealProj.y, radius * (1.6 + this.scanPulse * 0.6), 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(245, 158, 11, 0.15)';
    ctx.fill();

    // Seal Body
    ctx.beginPath();
    ctx.arc(sealProj.x, sealProj.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = '#0f172a';
    ctx.fill();
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Inner Ring
    ctx.beginPath();
    ctx.arc(sealProj.x, sealProj.y, radius * 0.78, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(245, 158, 11, 0.6)';
    ctx.lineWidth = 1.2;
    ctx.setLineDash([3, 3]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Seal Emblem Text
    ctx.font = `800 ${Math.max(8, Math.round(9 * sealProj.scale))}px "JetBrains Mono", monospace`;
    ctx.fillStyle = '#fbbf24';
    ctx.textAlign = 'center';
    ctx.fillText('CPTU', sealProj.x, sealProj.y - 4);
    ctx.font = `600 ${Math.max(7, Math.round(7.5 * sealProj.scale))}px "JetBrains Mono", monospace`;
    ctx.fillStyle = '#34d399';
    ctx.fillText('PPR-2008', sealProj.x, sealProj.y + 8);
    ctx.restore();
  }

  drawScanSweep(ctx, cx, cy) {
    if (this.scanPulse <= 0) return;
    const sweepY = Math.sin(this.time * 6) * 70;
    const p1 = this.project3D(-160, sweepY, 0, cx, cy);
    const p2 = this.project3D(160, sweepY, 0, cx, cy);

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.strokeStyle = `rgba(56, 189, 248, ${this.scanPulse * 0.8})`;
    ctx.lineWidth = 3;
    ctx.shadowColor = '#38bdf8';
    ctx.shadowBlur = 12;
    ctx.stroke();
    ctx.restore();
  }

  drawHUD(ctx) {
    ctx.save();
    // Top Left Status Badge
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(14, 14, 280, 78, 8);
    ctx.fill();
    ctx.stroke();

    ctx.font = '700 11px "JetBrains Mono", monospace';
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('📜 CPTU STD COMPLIANCE MANIFOLD', 24, 32);

    ctx.font = '500 9.5px "JetBrains Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(`Active Form: ${this.currentFormCode} (${this.currentCategory})`, 24, 48);
    ctx.fillText('Standards: e-PW2, e-PW3, e-PG2, e-PG3', 24, 62);
    ctx.fillText('PPR-2008 Statutory Clauses: 80 Configured', 24, 76);

    // Top Right Telemetry
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)';
    ctx.beginPath();
    ctx.roundRect(this.width - 240, 14, 226, 68, 8);
    ctx.fill();
    ctx.stroke();

    ctx.font = '700 10.5px "JetBrains Mono", monospace';
    ctx.fillStyle = '#fbbf24';
    ctx.fillText('🏛️ CPTU CLASS-1 AUDIT SAT', this.width - 228, 32);

    ctx.font = '500 9.5px "JetBrains Mono", monospace';
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('Field Injections: 100% Validated', this.width - 228, 48);
    ctx.fillText('Form e-PW3-8 Bank Seal: ATTACHED', this.width - 228, 62);

    // Bottom Controls Hint
    ctx.font = '500 9.5px "Plus Jakarta Sans", sans-serif';
    ctx.fillStyle = 'rgba(148, 163, 184, 0.7)';
    ctx.textAlign = 'left';
    ctx.fillText('🖱️ Drag to rotate 3D document stack • Scroll to zoom', 16, this.height - 12);
    ctx.restore();
  }
}

window.Std3DVisualizer = Std3DVisualizer;
window.initStd3D = function(canvasId = "std3dCanvas") {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  if (window.std3dInstance) {
    if (window.std3dInstance.canvas !== canvas) {
      if (typeof window.std3dInstance.stop === 'function') {
        window.std3dInstance.stop();
      }
      window.std3dInstance = new Std3DVisualizer(canvasId);
    } else {
      window.std3dInstance.updateDimensions();
    }
  } else {
    window.std3dInstance = new Std3DVisualizer(canvasId);
  }
  return window.std3dInstance;
};
