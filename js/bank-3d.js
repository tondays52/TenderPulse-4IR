/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D Holographic Institutional Banking & CreditConnect Mesh (bank-3d.js)
 * Grounding: Bangladesh Bank BRPD Circulars & CPTU PPR-2008 Rule 28 / Form e-PW2A-8
 * 
 * Renders an interactive 3D financial network topology showing:
 * - Central Bangladesh Bank (BB) Clearing Core & RTGS Hub
 * - 5 Tier-1 Scheduled Commercial Partner Banks in orbital constellation
 * - Dynamic 3D Liquidity Streams & Form e-PW2A-8 commitment token packets
 * - Real-time pre-approval pulse triggers and institutional safety rings
 */

class Bank3DVisualizer {
  constructor(canvasId = "bank3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.updateDimensions();
    this.rotation = 0.55;
    this.tilt = 0.32;
    this.zoom = 1.0;
    this.mouse = { isDown: false, lastX: 0, lastY: 0 };
    this.time = 0;
    this.pulseEnergy = 0;
    this.activeBankId = "prime-bank";
    this.isRunning = false;
    this.animFrameId = null;
    this.resizeObserver = null;

    // Define 3D Bank Node Topology
    this.banks = [
      { id: "prime-bank", name: "Prime Bank", code: "PRIME", maxCr: 25, color: "#10b981", x: -160, y: -40, z: -100, rating: "AAA" },
      { id: "brac-bank", name: "BRAC Bank", code: "BRAC", maxCr: 18, color: "#3b82f6", x: 170, y: -50, z: -90, rating: "AAA" },
      { id: "city-bank", name: "City Bank", code: "CITY", maxCr: 30, color: "#f59e0b", x: 200, y: 30, z: 120, rating: "AA+" },
      { id: "islami-bank", name: "Islami Bank", code: "IBBL", maxCr: 35, color: "#10b981", x: -190, y: 40, z: 110, rating: "AAA (Shariah)" },
      { id: "ebl", name: "Eastern Bank", code: "EBL", maxCr: 28, color: "#8b5cf6", x: 0, y: -90, z: 150, rating: "AAA" }
    ];

    // Flowing Liquidity Packets
    this.packets = [];
    for (let i = 0; i < 24; i++) {
      this.packets.push({
        bankIndex: i % this.banks.length,
        progress: Math.random(),
        speed: 0.008 + Math.random() * 0.012,
        size: 3 + Math.random() * 3
      });
    }

    this.initEvents();
    this.initResizeObserver();
    this.startLoop();
  }

  updateDimensions() {
    if (!this.canvas) return;
    const w = this.canvas.offsetWidth || this.canvas.clientWidth || 800;
    const h = this.canvas.offsetHeight || this.canvas.clientHeight || 320;
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

    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const clickX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
      const clickY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
      const cx = this.width / 2;
      const cy = this.height / 2 + 10;

      // Check click on bank nodes
      for (const bank of this.banks) {
        const p = this.project3D(bank.x, bank.y, bank.z, cx, cy);
        const nodeR = 26 * p.scale;
        const dist = Math.hypot(clickX - p.x, clickY - p.y);
        if (dist <= nodeR + 8) {
          this.selectBank(bank.id);
          return;
        }
      }

      // Check click on central core
      const center = this.project3D(0, 0, 0, cx, cy);
      if (Math.hypot(clickX - center.x, clickY - center.y) <= 32 * center.scale) {
        this.triggerCentralPulse();
      }
    });
  }

  selectBank(bankId = "prime-bank") {
    this.activeBankId = bankId;
    this.pulseEnergy = 1.0;
    
    // Highlight bank card in UI if present
    document.querySelectorAll(".bank-card").forEach(card => {
      const btn = card.querySelector(".btn-apply-bank");
      if (btn && btn.getAttribute("data-bank") === bankId) {
        card.classList.add("active-bank");
        card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else {
        card.classList.remove("active-bank");
      }
    });

    if (typeof showToast === 'function') {
      const bank = this.banks.find(b => b.id === bankId);
      if (bank) {
        showToast(`🏛️ Focused 3D Topology on ${bank.name} (Max LOC: BDT ${bank.maxCr} Cr)`, "info");
      }
    }
  }

  triggerPreApprovalPulse(bankId = "prime-bank") {
    this.selectBank(bankId);
  }

  triggerCentralPulse() {
    this.pulseEnergy = 1.2;
    if (typeof showToast === 'function') {
      showToast("⚡ Bangladesh Bank RTGS Real-Time Liquidity Pulse Broadcasted", "success");
    }
  }

  resetCamera() {
    this.rotation = 0.55;
    this.tilt = 0.32;
    this.zoom = 1.0;
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
    const scale = fov / (fov + finalZ + 300);

    return {
      x: cx + rotX * scale,
      y: cy + rotY * scale,
      scale: Math.max(0.2, scale),
      z: finalZ
    };
  }

  startLoop() {
    if (this.isRunning) return;
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
    if (this.pulseEnergy > 0) {
      this.pulseEnergy = Math.max(0, this.pulseEnergy - 0.02);
    }

    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Dark Cybernetic Mesh Background
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

    // 2. Draw 3D Radial Institutional Grid Floor
    this.drawRadialGrid(ctx, cx, cy);

    // 3. Central Bangladesh Bank & e-GP Clearing Core
    this.drawCentralClearingCore(ctx, cx, cy);

    // 4. Draw Institutional Conduits & Flowing Packets
    this.drawConduitsAndLiquidity(ctx, cx, cy);

    // 5. Draw 3D Bank Nodes
    this.drawBankNodes(ctx, cx, cy);

    // 6. Draw 3D Floating e-PW2A-8 Certificate Token
    this.drawCertificateToken(ctx, cx, cy);

    // 7. Telemetry HUD Overlay
    this.drawHUD(ctx);
  }

  drawRadialGrid(ctx, cx, cy) {
    ctx.save();
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.12)';
    ctx.lineWidth = 1;

    // Orbital rings
    for (let r = 80; r <= 280; r += 60) {
      ctx.beginPath();
      for (let theta = 0; theta <= Math.PI * 2; theta += 0.15) {
        const x = Math.cos(theta) * r;
        const z = Math.sin(theta) * r;
        const p = this.project3D(x, 40, z, cx, cy);
        if (theta === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.closePath();
      ctx.stroke();
    }
    ctx.restore();
  }

  drawCentralClearingCore(ctx, cx, cy) {
    const center = this.project3D(0, 0, 0, cx, cy);
    const radius = 28 * center.scale;

    // Glowing core gradient
    const grad = ctx.createRadialGradient(center.x, center.y, 2, center.x, center.y, radius * 1.6);
    grad.addColorStop(0, '#38bdf8');
    grad.addColorStop(0.5, 'rgba(59, 130, 246, 0.7)');
    grad.addColorStop(1, 'rgba(14, 165, 233, 0)');

    ctx.save();
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius * 1.6, 0, Math.PI * 2);
    ctx.fill();

    // Central Icon Pill
    ctx.fillStyle = '#0f172a';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Core Label
    ctx.fillStyle = '#ffffff';
    ctx.font = `bold ${Math.max(9, Math.floor(10 * center.scale))}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText("BB / e-GP", center.x, center.y - 4);
    ctx.font = `${Math.max(7, Math.floor(8 * center.scale))}px monospace`;
    ctx.fillStyle = '#38bdf8';
    ctx.fillText("RTGS CORE", center.x, center.y + 7);
    ctx.restore();
  }

  drawConduitsAndLiquidity(ctx, cx, cy) {
    const center = this.project3D(0, 0, 0, cx, cy);

    ctx.save();
    this.banks.forEach((bank, idx) => {
      const p = this.project3D(bank.x, bank.y, bank.z, cx, cy);
      const isSelected = bank.id === this.activeBankId;

      // Conduit line
      ctx.beginPath();
      ctx.moveTo(center.x, center.y);
      ctx.lineTo(p.x, p.y);
      ctx.strokeStyle = isSelected 
        ? `rgba(56, 189, 248, ${0.6 + this.pulseEnergy * 0.4})` 
        : 'rgba(59, 130, 246, 0.25)';
      ctx.lineWidth = (isSelected ? 2.5 : 1.2) * p.scale;
      ctx.stroke();
    });

    // Flowing Liquidity Packets
    this.packets.forEach(pkt => {
      pkt.progress = (pkt.progress + pkt.speed) % 1.0;
      const bank = this.banks[pkt.bankIndex];
      const bx = bank.x * pkt.progress;
      const by = bank.y * pkt.progress;
      const bz = bank.z * pkt.progress;

      const pos = this.project3D(bx, by, bz, cx, cy);
      const isSelected = bank.id === this.activeBankId;

      ctx.fillStyle = isSelected ? '#fbbf24' : bank.color;
      ctx.shadowColor = ctx.fillStyle;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, pkt.size * pos.scale, 0, Math.PI * 2);
      ctx.fill();
    });

    ctx.restore();
  }

  drawBankNodes(ctx, cx, cy) {
    ctx.save();
    this.banks.forEach(bank => {
      const p = this.project3D(bank.x, bank.y, bank.z, cx, cy);
      const isSelected = bank.id === this.activeBankId;
      const nodeR = (isSelected ? 24 : 18) * p.scale;

      // Pulse ring for active bank
      if (isSelected && this.pulseEnergy > 0) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, (nodeR + 15 * (1 - this.pulseEnergy)), 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(251, 191, 36, ${this.pulseEnergy})`;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Bank Node Circle
      ctx.beginPath();
      ctx.arc(p.x, p.y, nodeR, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? '#093627' : '#09152b';
      ctx.strokeStyle = isSelected ? '#10b981' : bank.color;
      ctx.lineWidth = isSelected ? 2.5 : 1.5;
      ctx.fill();
      ctx.stroke();

      // Bank Code
      ctx.fillStyle = '#ffffff';
      ctx.font = `bold ${Math.max(8, Math.floor(9 * p.scale))}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(bank.code, p.x, p.y - 3);

      // Max Sanction Cr Badge
      ctx.fillStyle = isSelected ? '#34d399' : '#94a3b8';
      ctx.font = `${Math.max(7, Math.floor(7.5 * p.scale))}px monospace`;
      ctx.fillText(`BDT ${bank.maxCr} Cr`, p.x, p.y + 7);

      // Bank Full Name Tag Below
      ctx.fillStyle = '#e2e8f0';
      ctx.font = `${Math.max(8, Math.floor(8.5 * p.scale))}px Inter, sans-serif`;
      ctx.fillText(bank.name, p.x, p.y + nodeR + 10);
    });
    ctx.restore();
  }

  drawCertificateToken(ctx, cx, cy) {
    // Floating 3D token on top right
    const floatY = -80 + Math.sin(this.time * 2.5) * 8;
    const token = this.project3D(110, floatY, -50, cx, cy);

    ctx.save();
    ctx.translate(token.x, token.y);
    ctx.scale(token.scale, token.scale);

    // Outer glow
    ctx.fillStyle = 'rgba(245, 158, 11, 0.15)';
    ctx.beginPath();
    ctx.arc(0, 0, 32, 0, Math.PI * 2);
    ctx.fill();

    // Golden Certificate Badge
    ctx.fillStyle = '#1e1b4b';
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, 0, 22, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Inner Emblem
    ctx.fillStyle = '#fbbf24';
    ctx.font = 'bold 9px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText("e-PW2A-8", 0, -3);
    ctx.font = '7px monospace';
    ctx.fillStyle = '#38bdf8';
    ctx.fillText("LOC SEAL", 0, 6);

    ctx.restore();
  }

  drawHUD(ctx) {
    ctx.save();
    // Top Left Status Pill
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.4)';
    ctx.lineWidth = 1;
    ctx.roundRect(14, 14, 250, 48, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 10px monospace';
    ctx.fillText("INSTITUTIONAL LIQUIDITY MESH", 24, 30);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px Inter, sans-serif';
    ctx.fillText("5 Scheduled Partner Banks • BDT 136 Cr Max Sanction", 24, 46);

    // Top Right Telemetry
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
    ctx.roundRect(this.width - 210, 14, 196, 48, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#34d399';
    ctx.font = 'bold 10px monospace';
    ctx.fillText("CLEARING LATENCY: 24h FAST-TRACK", this.width - 200, 30);

    ctx.fillStyle = '#e2e8f0';
    ctx.font = '9px monospace';
    ctx.fillText("Form e-PW2A-8 Commitments: ACTIVE", this.width - 200, 46);

    ctx.restore();
  }
}

// Global Export
window.Bank3DVisualizer = Bank3DVisualizer;
window.initBank3D = function(canvasId = "bank3dCanvas") {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  if (window.bank3dInstance) {
    if (window.bank3dInstance.canvas !== canvas) {
      if (typeof window.bank3dInstance.stop === 'function') {
        window.bank3dInstance.stop();
      }
      window.bank3dInstance = new Bank3DVisualizer(canvasId);
    } else {
      window.bank3dInstance.updateDimensions();
    }
  } else {
    window.bank3dInstance = new Bank3DVisualizer(canvasId);
  }

  if (window.bankHub) {
    window.bankHub.visualizer = window.bank3dInstance;
  }
  return window.bank3dInstance;
};
