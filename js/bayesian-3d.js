/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D Holographic Bayesian Nash Equilibrium & Pareto Surface (bayesian-3d.js)
 * Grounding: Milgrom-Weber Auction Theory & Truncated Empirical Bayes under Price Caps
 * 
 * Renders an interactive 3D Pareto Frontier Surface mapping Discount % vs Competitor Density vs Expected Margin.
 */

class Bayesian3DVisualizer {
  constructor(canvasId = "bayesian3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.updateDimensions();
    this.rotation = 0.45;
    this.tilt = 0.32;
    this.mouse = { x: this.width / 2, y: this.height / 2, isDown: false, lastX: 0, lastY: 0 };
    this.currentDiscount = -8.5;
    this.currentAgency = "RHD";
    this.time = 0;

    this.initEvents();
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
        this.tilt = Math.max(-0.7, Math.min(0.7, this.tilt + dy * 0.008));
        this.mouse.lastX = e.clientX;
        this.mouse.lastY = e.clientY;
      }
    });
  }

  setParams(discount, agency = "RHD") {
    this.currentDiscount = parseFloat(discount) || -8.5;
    this.currentAgency = agency;
  }

  project3D(x, y, z, cx, cy) {
    const cosR = Math.cos(this.rotation);
    const sinR = Math.sin(this.rotation);

    // Rotate around Y-axis
    const rotX = x * cosR - z * sinR;
    const rotZ = x * sinR + z * cosR;

    // Tilt around X-axis
    const cosT = Math.cos(this.tilt);
    const sinT = Math.sin(this.tilt);
    const rotY = y * cosT - rotZ * sinT;
    const finalZ = y * sinT + rotZ * cosT;

    const fov = 420;
    const scale = fov / (fov + finalZ + 250);

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
    ctx.clearRect(0, 0, this.width, this.height);

    const cx = this.width / 2;
    const cy = this.height / 2;

    // Background Gradient
    const bgGlow = ctx.createRadialGradient(cx, cy, 10, cx, cy, this.width * 0.6);
    bgGlow.addColorStop(0, "rgba(15, 23, 42, 0.95)");
    bgGlow.addColorStop(1, "rgba(2, 6, 23, 1)");
    ctx.fillStyle = bgGlow;
    ctx.fillRect(0, 0, this.width, this.height);

    // Grid Mesh Definition (Discount [-15% to 0%] x Bidders [2 to 16])
    const rows = 9;
    const cols = 9;
    const meshPoints = [];

    for (let r = 0; r <= rows; r++) {
      meshPoints[r] = [];
      const discountVal = -15 + (r / rows) * 15; // -15% to 0%
      for (let c = 0; c <= cols; c++) {
        const bidderCount = 2 + (c / cols) * 14; // 2 to 16 bidders
        
        // 3D Grid coordinates
        const gx = (r - rows / 2) * 28; // X: Discount axis
        const gz = (c - cols / 2) * 24; // Z: Competitor axis

        // Surface elevation (Y: Net Expected Utility)
        let height = 0;
        if (discountVal < -10.0) {
          // Rule 98 Cliff Drop
          height = -60;
        } else {
          // Pareto bell curve peaking near sweet spot (-8.9% to -9.85%)
          const sweetSpot = this.currentAgency === "LGED" ? -9.85 : -8.90;
          const distFromSweet = Math.abs(discountVal - sweetSpot);
          const basePeak = 70 - distFromSweet * 12;
          const cursePenalty = Math.pow(Math.abs(discountVal) / 10, 2) * (bidderCount / 4) * 8;
          height = basePeak - cursePenalty;
        }

        const gy = -height; // Inverted for canvas coordinates
        meshPoints[r][c] = {
          rawDiscount: discountVal,
          rawBidders: bidderCount,
          proj: this.project3D(gx, gy, gz, cx, cy)
        };
      }
    }

    // Draw Surface Wireframe Quads
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const p1 = meshPoints[r][c].proj;
        const p2 = meshPoints[r + 1][c].proj;
        const p3 = meshPoints[r + 1][c + 1].proj;
        const p4 = meshPoints[r][c + 1].proj;

        const disc = meshPoints[r][c].rawDiscount;
        const isDisqualified = disc < -10.0;
        const isOptimal = disc >= -9.9 && disc <= -8.5;

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.lineTo(p3.x, p3.y);
        ctx.lineTo(p4.x, p4.y);
        ctx.closePath();

        if (isDisqualified) {
          ctx.fillStyle = "rgba(239, 68, 68, 0.12)";
          ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
        } else if (isOptimal) {
          ctx.fillStyle = "rgba(16, 185, 129, 0.18)";
          ctx.strokeStyle = "rgba(52, 211, 153, 0.6)";
        } else {
          ctx.fillStyle = "rgba(56, 189, 248, 0.08)";
          ctx.strokeStyle = "rgba(56, 189, 248, 0.3)";
        }

        ctx.lineWidth = 1;
        ctx.fill();
        ctx.stroke();
      }
    }

    // Draw Rule 98 Boundary Red Hazard Line
    const rRule98 = Math.round(((-10 - (-15)) / 15) * rows);
    ctx.beginPath();
    for (let c = 0; c <= cols; c++) {
      const p = meshPoints[rRule98][c].proj;
      if (c === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Active User Bid Trajectory Cursor (Glowing Orb)
    const normDisc = Math.max(0, Math.min(1, (this.currentDiscount - (-15)) / 15));
    const curR = normDisc * rows;
    const curC = cols * 0.5; // Average 8 competitors
    const curX = (curR - rows / 2) * 28;
    const curZ = (curC - cols / 2) * 24;
    
    let curH = 0;
    if (this.currentDiscount < -10.0) {
      curH = -60;
    } else {
      const sweet = this.currentAgency === "LGED" ? -9.85 : -8.90;
      curH = 70 - Math.abs(this.currentDiscount - sweet) * 12 - 10;
    }

    const orbProj = this.project3D(curX, -curH - 10, curZ, cx, cy);

    // Orb Aura
    const isBad = this.currentDiscount < -10.0;
    ctx.beginPath();
    ctx.arc(orbProj.x, orbProj.y, 14 * orbProj.scale, 0, Math.PI * 2);
    ctx.fillStyle = isBad ? "rgba(239, 68, 68, 0.3)" : "rgba(16, 185, 129, 0.4)";
    ctx.fill();

    // Orb Core
    ctx.beginPath();
    ctx.arc(orbProj.x, orbProj.y, 6 * orbProj.scale, 0, Math.PI * 2);
    ctx.fillStyle = isBad ? "#ef4444" : "#10b981";
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Floating Target Label
    ctx.font = `bold ${Math.max(9, Math.round(11 * orbProj.scale))}px Inter, sans-serif`;
    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.fillText(`Your Bid: ${this.currentDiscount.toFixed(1)}%`, orbProj.x, orbProj.y - 12 * orbProj.scale);
  }
}

window.Bayesian3DVisualizer = Bayesian3DVisualizer;
window.initBayesian3D = function(canvasId = "bayesian3dCanvas") {
  if (!window.bayesian3dInstance) {
    window.bayesian3dInstance = new Bayesian3DVisualizer(canvasId);
  }
  return window.bayesian3dInstance;
};
