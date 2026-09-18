/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D Isometric Capacity Math Balance Scale & SMT Feasibility Polytope (capacity-3d.js)
 * Renders an interactive 3D dynamic equilibrium balance scale comparing
 * Gross Potential (A * N * alpha), Commitments (B), and Target Tender Cost (T).
 */

class Capacity3DVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width = this.canvas.offsetWidth || 800;
    this.height = this.canvas.height = this.canvas.offsetHeight || 300;
    this.rotation = 0.35;
    this.tilt = 0.4;
    this.mouse = { x: this.width / 2, y: this.height / 2, targetX: this.width / 2, targetY: this.height / 2 };

    // Dynamic Mathematical State
    this.state = {
      grossPotential: 56.25, // Crore
      commitmentB: 12.0,     // Crore
      netCapacity: 44.25,    // Crore
      tenderCost: 32.0,      // Crore
      liquidAssets: 4.5,     // Crore
      liquidReq: 6.5,        // Crore
      alpha: 1.5,
      isEligible: true
    };

    this.particles = [];
    this.initEvents();
    this.startLoop();
  }

  initEvents() {
    window.addEventListener('resize', () => {
      if (!this.canvas) return;
      this.width = this.canvas.width = this.canvas.offsetWidth;
      this.height = this.canvas.height = this.canvas.offsetHeight || 300;
    });

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

  updateMathState(params = {}) {
    if (params.grossPotential !== undefined) this.state.grossPotential = params.grossPotential / 10000000;
    if (params.commitmentB !== undefined) this.state.commitmentB = params.commitmentB / 10000000;
    if (params.netCapacity !== undefined) this.state.netCapacity = params.netCapacity / 10000000;
    if (params.tenderCost !== undefined) this.state.tenderCost = params.tenderCost / 10000000;
    if (params.liquidAssets !== undefined) this.state.liquidAssets = params.liquidAssets / 10000000;
    if (params.liquidReq !== undefined) this.state.liquidReq = params.liquidReq / 10000000;
    if (params.alpha !== undefined) this.state.alpha = params.alpha;
    this.state.isEligible = this.state.netCapacity >= this.state.tenderCost;
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
    const animate = () => {
      this.render();
      requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }

  render() {
    const ctx = this.ctx;
    if (!ctx) return;

    ctx.clearRect(0, 0, this.width, this.height);

    const cx = this.width / 2;
    const cy = this.height / 2 + 15;

    // Smooth mouse interpolation
    this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
    this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

    // Subtle gentle oscillation
    this.rotation = 0.32 + Math.sin(Date.now() * 0.0008) * 0.06 + (this.mouse.x - cx) * 0.0006;

    // 1. Draw 3D Ground Grid & Coordinate Plane
    ctx.save();
    ctx.strokeStyle = "rgba(56, 189, 248, 0.06)";
    ctx.lineWidth = 1;
    for (let gz = -120; gz <= 120; gz += 30) {
      const p1 = this.project3D(-240, 50, gz, cx, cy);
      const p2 = this.project3D(240, 50, gz, cx, cy);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }
    for (let gx = -240; gx <= 240; gx += 40) {
      const p1 = this.project3D(gx, 50, -120, cx, cy);
      const p2 = this.project3D(gx, 50, 120, cx, cy);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }
    ctx.restore();

    // 2. Draw Center Fulcrum & Balance Scale Base
    const fulcrumBase = this.project3D(0, 50, 0, cx, cy);
    const fulcrumApex = this.project3D(0, 5, 0, cx, cy);

    ctx.beginPath();
    ctx.moveTo(fulcrumBase.x - 25 * fulcrumBase.scale, fulcrumBase.y);
    ctx.lineTo(fulcrumApex.x, fulcrumApex.y);
    ctx.lineTo(fulcrumBase.x + 25 * fulcrumBase.scale, fulcrumBase.y);
    ctx.closePath();
    ctx.fillStyle = "rgba(30, 41, 59, 0.85)";
    ctx.strokeStyle = "rgba(56, 189, 248, 0.4)";
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();

    // 3. Dynamic Tilt Angle calculation based on Net Capacity Margin
    const netSurplus = this.state.netCapacity - this.state.tenderCost;
    const targetTiltAngle = Math.max(-0.25, Math.min(0.25, netSurplus * 0.015));
    const armLength = 150;

    const leftArmX = -Math.cos(targetTiltAngle) * armLength;
    const leftArmY = 5 - Math.sin(targetTiltAngle) * armLength * 0.4;
    const rightArmX = Math.cos(targetTiltAngle) * armLength;
    const rightArmY = 5 + Math.sin(targetTiltAngle) * armLength * 0.4;

    const leftTip = this.project3D(leftArmX, leftArmY, 0, cx, cy);
    const rightTip = this.project3D(rightArmX, rightArmY, 0, cx, cy);

    // Balance Beam
    ctx.beginPath();
    ctx.moveTo(leftTip.x, leftTip.y);
    ctx.lineTo(rightTip.x, rightTip.y);
    ctx.strokeStyle = this.state.isEligible ? "#10b981" : "#f43f5e";
    ctx.lineWidth = 4;
    ctx.stroke();

    // 4. Draw Left Pillar / Cylinder: Gross Capacity (A * N * alpha)
    const grossHeight = Math.min(100, Math.max(25, this.state.grossPotential * 1.3));
    const grossP = this.project3D(leftArmX, leftArmY, 0, cx, cy);
    const grossTopP = this.project3D(leftArmX, leftArmY - grossHeight, 0, cx, cy);
    const colWidth = 26 * grossP.scale;

    ctx.beginPath();
    ctx.rect(grossP.x - colWidth / 2, grossTopP.y, colWidth, grossP.y - grossTopP.y);
    const gradGross = ctx.createLinearGradient(grossP.x - colWidth, 0, grossP.x + colWidth, 0);
    gradGross.addColorStop(0, "rgba(16, 185, 129, 0.7)");
    gradGross.addColorStop(1, "rgba(5, 150, 105, 0.9)");
    ctx.fillStyle = gradGross;
    ctx.strokeStyle = "#34d399";
    ctx.lineWidth = 1.5;
    ctx.fill();
    ctx.stroke();

    // Gross Pillar Top Label
    ctx.font = '700 9px "JetBrains Mono", monospace';
    ctx.fillStyle = "#34d399";
    ctx.fillText(`+৳${this.state.grossPotential.toFixed(1)}Cr`, grossTopP.x - 22, grossTopP.y - 8);
    ctx.font = '600 8px "Plus Jakarta Sans", sans-serif';
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(`A×N×${this.state.alpha}`, grossTopP.x - 16, grossTopP.y - 18);

    // 5. Draw Right Pillar / Cylinder: Commitment B & Target Tender Cost T
    const commitHeight = Math.min(60, Math.max(15, this.state.commitmentB * 1.6));
    const targetHeight = Math.min(80, Math.max(20, this.state.tenderCost * 1.2));
    const commitP = this.project3D(rightArmX, rightArmY, 0, cx, cy);
    const commitTopP = this.project3D(rightArmX, rightArmY - commitHeight, 0, cx, cy);

    ctx.beginPath();
    ctx.rect(commitP.x - colWidth / 2, commitTopP.y, colWidth, commitP.y - commitTopP.y);
    const gradCommit = ctx.createLinearGradient(commitP.x - colWidth, 0, commitP.x + colWidth, 0);
    gradCommit.addColorStop(0, "rgba(244, 63, 94, 0.65)");
    gradCommit.addColorStop(1, "rgba(225, 29, 72, 0.85)");
    ctx.fillStyle = gradCommit;
    ctx.strokeStyle = "#fb7185";
    ctx.lineWidth = 1.5;
    ctx.fill();
    ctx.stroke();

    // Commitment Label
    ctx.font = '700 9px "JetBrains Mono", monospace';
    ctx.fillStyle = "#fb7185";
    ctx.fillText(`-৳${this.state.commitmentB.toFixed(1)}Cr`, commitTopP.x - 20, commitTopP.y - 8);
    ctx.font = '600 8px "Plus Jakarta Sans", sans-serif';
    ctx.fillStyle = "#94a3b8";
    ctx.fillText("B Commitments", commitTopP.x - 26, commitTopP.y - 18);

    // 6. Draw Floating Target Tender Cost Plane / Horizon Line
    const targetPlaneP1 = this.project3D(-160, 5 - this.state.tenderCost * 0.9, -40, cx, cy);
    const targetPlaneP2 = this.project3D(160, 5 - this.state.tenderCost * 0.9, -40, cx, cy);
    ctx.beginPath();
    ctx.moveTo(targetPlaneP1.x, targetPlaneP1.y);
    ctx.lineTo(targetPlaneP2.x, targetPlaneP2.y);
    ctx.strokeStyle = "rgba(251, 191, 36, 0.7)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.font = '700 8.5px "JetBrains Mono", monospace';
    ctx.fillStyle = "#fbbf24";
    ctx.fillText(`TARGET TENDER COST: ৳${this.state.tenderCost.toFixed(1)} Cr`, targetPlaneP2.x - 145, targetPlaneP2.y - 4);

    // 7. Dynamic Data Energy Sparks
    if (Math.random() < 0.2) {
      this.particles.push({
        x: leftArmX + (Math.random() - 0.5) * 20,
        y: leftArmY - grossHeight,
        vx: (rightArmX - leftArmX) * 0.02 + (Math.random() - 0.5) * 0.5,
        vy: -0.5 - Math.random(),
        life: 1.0,
        color: this.state.isEligible ? "#10b981" : "#f59e0b"
      });
    }

    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.life -= 0.03;

      const proj = this.project3D(p.x, p.y, 0, cx, cy);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.beginPath();
      ctx.arc(proj.x, proj.y, 2.5 * proj.scale, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1.0;

      if (p.life <= 0) this.particles.splice(i, 1);
    }

    // 8. HUD Telemetry Overlay
    ctx.font = '700 10px "JetBrains Mono", monospace';
    ctx.fillStyle = this.state.isEligible ? "#10b981" : "#f43f5e";
    ctx.fillText(`● CPTU CAPACITY EQUILIBRIUM: ${this.state.isEligible ? "SAT (SURPLUS +৳" + (this.state.netCapacity - this.state.tenderCost).toFixed(1) + " Cr)" : "UNSAT (DEFICIT ৳" + Math.abs(this.state.netCapacity - this.state.tenderCost).toFixed(1) + " Cr)"}`, 14, 22);

    ctx.font = '500 9px "JetBrains Mono", monospace';
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(`FORMULA: (A×N×${this.state.alpha}) - B = ৳${this.state.netCapacity.toFixed(2)} Cr | LIQUID SOLVENCY: ৳${this.state.liquidAssets.toFixed(1)}Cr / ৳${this.state.liquidReq.toFixed(1)}Cr`, 14, 38);
  }
}

// Global Singleton Initializer
window.initCapacity3DVisualizer = function(canvasId = "capacity3dCanvas") {
  if (document.getElementById(canvasId)) {
    window.capacity3dInstance = new Capacity3DVisualizer(canvasId);
  }
};
