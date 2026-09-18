/**
 * Di-Tender 4IR — 3D Holographic AI Copilot Neural Core & Knowledge Manifold (copilot-3d.js)
 * Grounding: Public Procurement Act 2006 & Public Procurement Rules 2008 (PPR-2008)
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

class Copilot3DVisualizer {
  constructor(canvasId = "copilot3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.width = 800;
    this.height = 300;
    this.rotation = 0.52;
    this.tilt = 0.24;
    this.zoom = 1.0;
    this.mouse = { isDown: false, lastX: 0, lastY: 0 };
    this.time = 0;
    this.pulseEnergy = 0;

    // 4 Knowledge Orbital Satellites
    this.satellites = [
      { name: "PPR-2008 Rules", code: "RULE-96", color: "#10b981", radius: 140, speed: 0.015, angle: 0 },
      { name: "Section 2 TDS", code: "ITT-25.1", color: "#38bdf8", radius: 110, speed: -0.02, angle: Math.PI / 2 },
      { name: "Section 4 PCC", code: "GCC-47", color: "#f59e0b", radius: 160, speed: 0.012, angle: Math.PI },
      { name: "BOQ Unit Rates", code: "SEC-6", color: "#a855f7", radius: 125, speed: -0.018, angle: (3 * Math.PI) / 2 }
    ];

    // Neural Synapse Particles
    this.synapses = [];
    for (let i = 0; i < 30; i++) {
      this.synapses.push({
        x: (Math.random() - 0.5) * 260,
        y: (Math.random() - 0.5) * 120,
        z: (Math.random() - 0.5) * 260,
        speed: 0.01 + Math.random() * 0.02,
        size: 2 + Math.random() * 2.5
      });
    }

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

  triggerPromptPulse() {
    this.pulseEnergy = 1.0;
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
    if (this.pulseEnergy > 0) {
      this.pulseEnergy = Math.max(0, this.pulseEnergy - 0.02);
    }

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

    // 2. Draw 3D Orbital Rings
    this.drawOrbitalRings(ctx, cx, cy);

    // 3. Draw Synapse Connections & Floating Neural Particles
    this.drawSynapses(ctx, cx, cy);

    // 4. Draw Knowledge Satellites
    this.drawSatellites(ctx, cx, cy);

    // 5. Draw Central AI Neural Core
    this.drawCentralCore(ctx, cx, cy);

    // 6. Draw HUD Telemetry
    this.drawHUD(ctx);
  }

  drawOrbitalRings(ctx, cx, cy) {
    ctx.save();
    ctx.lineWidth = 1;

    [110, 140, 160].forEach((r, idx) => {
      ctx.beginPath();
      for (let theta = 0; theta <= Math.PI * 2; theta += 0.15) {
        const x = Math.cos(theta) * r;
        const z = Math.sin(theta) * r;
        const pt = this.project3D(x, 0, z, cx, cy);
        if (theta === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }
      ctx.closePath();
      ctx.strokeStyle = idx === 1 ? 'rgba(56, 189, 248, 0.25)' : 'rgba(255, 255, 255, 0.08)';
      ctx.stroke();
    });
    ctx.restore();
  }

  drawSynapses(ctx, cx, cy) {
    const center = this.project3D(0, 0, 0, cx, cy);
    ctx.save();

    this.synapses.forEach(s => {
      const pt = this.project3D(s.x, s.y + Math.sin(this.time * 2 + s.speed) * 15, s.z, cx, cy);

      // Faint connection line to center
      if (Math.random() > 0.4) {
        ctx.beginPath();
        ctx.moveTo(center.x, center.y);
        ctx.lineTo(pt.x, pt.y);
        ctx.strokeStyle = `rgba(59, 130, 246, ${0.1 + this.pulseEnergy * 0.3})`;
        ctx.lineWidth = 0.8 * pt.scale;
        ctx.stroke();
      }

      // Synapse particle
      ctx.fillStyle = this.pulseEnergy > 0 ? '#fbbf24' : '#38bdf8';
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, s.size * pt.scale, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.restore();
  }

  drawSatellites(ctx, cx, cy) {
    ctx.save();
    this.satellites.forEach(sat => {
      sat.angle += sat.speed;
      const x = Math.cos(sat.angle) * sat.radius;
      const z = Math.sin(sat.angle) * sat.radius;
      const y = Math.sin(sat.angle * 2 + this.time) * 20;

      const pt = this.project3D(x, y, z, cx, cy);
      const nodeR = 14 * pt.scale;

      // Satellite Sphere
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, nodeR, 0, Math.PI * 2);
      ctx.fillStyle = '#09152b';
      ctx.strokeStyle = sat.color;
      ctx.lineWidth = 2 * pt.scale;
      ctx.fill();
      ctx.stroke();

      // Inner icon label
      ctx.fillStyle = '#ffffff';
      ctx.font = `bold ${Math.max(7, Math.floor(8 * pt.scale))}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(sat.code, pt.x, pt.y);

      // Name Label Tag
      ctx.fillStyle = '#94a3b8';
      ctx.font = `${Math.max(7, Math.floor(8 * pt.scale))}px monospace`;
      ctx.fillText(sat.name, pt.x, pt.y + nodeR + 10);
    });
    ctx.restore();
  }

  drawCentralCore(ctx, cx, cy) {
    const center = this.project3D(0, 0, 0, cx, cy);
    const radius = 28 * center.scale;

    ctx.save();
    // Glowing Core Halo
    const grad = ctx.createRadialGradient(center.x, center.y, 2, center.x, center.y, radius * 2.2);
    grad.addColorStop(0, '#38bdf8');
    grad.addColorStop(0.5, 'rgba(59, 130, 246, 0.6)');
    grad.addColorStop(1, 'rgba(14, 165, 233, 0)');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius * (2.2 + this.pulseEnergy * 0.8), 0, Math.PI * 2);
    ctx.fill();

    // Central Core Orb
    ctx.fillStyle = '#0f172a';
    ctx.strokeStyle = this.pulseEnergy > 0 ? '#fbbf24' : '#38bdf8';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // AI Core Label
    ctx.fillStyle = '#ffffff';
    ctx.font = `bold ${Math.max(9, Math.floor(10 * center.scale))}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText("COPILOT", center.x, center.y - 4);

    ctx.fillStyle = '#34d399';
    ctx.font = `${Math.max(7, Math.floor(7.5 * center.scale))}px monospace`;
    ctx.fillText("4IR AI CORE", center.x, center.y + 7);
    ctx.restore();
  }

  drawHUD(ctx) {
    ctx.save();
    // Top Left Status Pill
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.4)';
    ctx.lineWidth = 1;
    safeRoundRect(ctx, 14, 14, 250, 48, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 10px monospace';
    ctx.fillText("CPTU AI REASONING CORE", 24, 30);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px Inter, sans-serif';
    ctx.fillText("Context: Section 2, 4 & 6 BOQ Embedded", 24, 46);

    // Top Right Telemetry
    if (this.width > 300) {
      ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
      safeRoundRect(ctx, this.width - 210, 14, 196, 48, 8);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#34d399';
      ctx.font = 'bold 10px monospace';
      ctx.fillText("INFERENCE: REAL-TIME (<42ms)", this.width - 200, 30);

      ctx.fillStyle = '#e2e8f0';
      ctx.font = '9px monospace';
      ctx.fillText("PPR-2008 Citations: SYNCHRONIZED", this.width - 200, 46);
    }

    ctx.restore();
  }
}

// Global Export
window.Copilot3DVisualizer = Copilot3DVisualizer;
window.initCopilot3D = function(canvasId = "copilot3dCanvas") {
  if (window.copilot3dInstance && window.copilot3dInstance.canvas) {
    window.copilot3dInstance.updateDimensions();
    return window.copilot3dInstance;
  }
  const canvas = document.getElementById(canvasId);
  if (canvas) {
    window.copilot3dInstance = new Copilot3DVisualizer(canvasId);
    if (window.tenderCopilot) {
      window.tenderCopilot.visualizer = window.copilot3dInstance;
    }
    return window.copilot3dInstance;
  }
  return null;
};
