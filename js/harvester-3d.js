/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D Isometric Procurement Radar & Live Ingestion Matrix (harvester-3d.js)
 * Renders an interactive 3D particle radar with division nodes, crawler data streams,
 * and holographic wireframes on HTML5 Canvas.
 */

class Harvester3DRadar {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width = this.canvas.offsetWidth || 800;
    this.height = this.canvas.height = this.canvas.offsetHeight || 320;
    this.rotation = 0;
    this.mouse = { x: this.width / 2, y: this.height / 2, targetX: this.width / 2, targetY: this.height / 2 };
    this.packets = [];
    this.pulseRadius = 0;

    // 8 Strategic National Division Nodes
    this.divisionNodes = [
      { name: "Dhaka (e-GP Central)", x: 0, y: 0, z: 0, agency: "CPTU Core", color: "#10b981", active: true },
      { name: "Chittagong (Port/RHD)", x: 120, y: 60, z: 40, agency: "RHD/CPA", color: "#38bdf8", active: true },
      { name: "Rajshahi (LGED/BMDA)", x: -130, y: -40, z: -30, agency: "LGED Zone", color: "#fbbf24", active: true },
      { name: "Khulna (BWDB/Coastal)", x: -100, y: 80, z: 20, agency: "BWDB Div", color: "#34d399", active: true },
      { name: "Sylhet (RHD/Bridges)", x: 140, y: -70, z: -50, agency: "RHD North", color: "#60a5fa", active: true },
      { name: "Barisal (Payra/Inland)", x: -20, y: 120, z: 50, agency: "BIWTA/LGED", color: "#a78bfa", active: true },
      { name: "Rangpur (Teesta/BREB)", x: -90, y: -110, z: -60, agency: "BREB Grid", color: "#f43f5e", active: true },
      { name: "Mymensingh (PWD Hub)", x: 30, y: -80, z: -20, agency: "PWD Works", color: "#10b981", active: true }
    ];

    this.initEvents();
    this.startLoop();
  }

  initEvents() {
    window.addEventListener('resize', () => {
      if (!this.canvas) return;
      this.width = this.canvas.width = this.canvas.offsetWidth;
      this.height = this.canvas.height = this.canvas.offsetHeight || 320;
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

  spawnDataPacket(sourceIndex = 0, targetIndex) {
    if (!this.divisionNodes[sourceIndex] || !this.divisionNodes[targetIndex]) return;
    this.packets.push({
      source: sourceIndex,
      target: targetIndex,
      progress: 0,
      speed: 0.02 + Math.random() * 0.025,
      color: this.divisionNodes[targetIndex].color || "#38bdf8",
      size: 2 + Math.random() * 2
    });
  }

  project3D(x, y, z, cx, cy) {
    const cosR = Math.cos(this.rotation);
    const sinR = Math.sin(this.rotation);

    // Rotate around Y-axis
    const rotX = x * cosR - z * sinR;
    const rotZ = x * sinR + z * cosR;

    // Slight tilt around X-axis based on mouse
    const tilt = (this.mouse.y - cy) * 0.0015;
    const cosT = Math.cos(tilt);
    const sinT = Math.sin(tilt);
    const rotY = y * cosT - rotZ * sinT;
    const finalZ = y * sinT + rotZ * cosT;

    const fov = 400;
    const scale = fov / (fov + finalZ + 200);

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

    // Center coordinates
    const cx = this.width / 2;
    const cy = this.height / 2;

    // Smooth mouse interpolation
    this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
    this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

    // Constant slow 3D rotation
    this.rotation += 0.008;
    this.pulseRadius = (this.pulseRadius + 1.2) % 180;

    // 1. Draw Holographic Radar Background Grid
    ctx.save();
    ctx.strokeStyle = "rgba(16, 185, 129, 0.06)";
    ctx.lineWidth = 1;
    const gridStep = 40;
    for (let x = 0; x < this.width; x += gridStep) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, this.height);
      ctx.stroke();
    }
    for (let y = 0; y < this.height; y += gridStep) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.width, y);
      ctx.stroke();
    }

    // 2. Draw 3D Isometric Ellipses & Radar Rings
    ctx.strokeStyle = "rgba(56, 189, 248, 0.12)";
    ctx.beginPath();
    ctx.ellipse(cx, cy, 180, 75, this.rotation * 0.2, 0, Math.PI * 2);
    ctx.stroke();

    ctx.strokeStyle = "rgba(16, 185, 129, 0.15)";
    ctx.beginPath();
    ctx.ellipse(cx, cy, 120, 50, -this.rotation * 0.3, 0, Math.PI * 2);
    ctx.stroke();

    // Pulse wave from center node
    ctx.strokeStyle = `rgba(16, 185, 129, ${Math.max(0, 0.4 - this.pulseRadius / 180)})`;
    ctx.beginPath();
    ctx.ellipse(cx, cy, this.pulseRadius, this.pulseRadius * 0.45, 0, 0, Math.PI * 2);
    ctx.stroke();

    // 3. Project Nodes to 2D Screen Space
    const projected = this.divisionNodes.map((node, i) => {
      const p = this.project3D(node.x, node.y, node.z, cx, cy);
      return { ...node, ...p, index: i };
    });

    // Sort by Z for proper depth rendering
    projected.sort((a, b) => a.z - b.z);

    // 4. Draw Connecting Stream Vectors
    const centerNode = projected.find(p => p.name.includes("Dhaka"));
    if (centerNode) {
      projected.forEach(p => {
        if (p !== centerNode) {
          ctx.beginPath();
          ctx.moveTo(centerNode.x, centerNode.y);
          ctx.lineTo(p.x, p.y);
          ctx.strokeStyle = "rgba(148, 163, 184, 0.15)";
          ctx.setLineDash([3, 4]);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      });
    }

    // Randomly spawn data packets
    if (Math.random() < 0.08) {
      const target = Math.floor(1 + Math.random() * (this.divisionNodes.length - 1));
      this.spawnDataPacket(0, target);
    }

    // 5. Update & Draw Data Packets
    for (let i = this.packets.length - 1; i >= 0; i--) {
      const pkt = this.packets[i];
      pkt.progress += pkt.speed;

      const p1 = this.project3D(this.divisionNodes[pkt.source].x, this.divisionNodes[pkt.source].y, this.divisionNodes[pkt.source].z, cx, cy);
      const p2 = this.project3D(this.divisionNodes[pkt.target].x, this.divisionNodes[pkt.target].y, this.divisionNodes[pkt.target].z, cx, cy);

      const px = p1.x + (p2.x - p1.x) * pkt.progress;
      const py = p1.y + (p2.y - p1.y) * pkt.progress;

      ctx.fillStyle = pkt.color;
      ctx.shadowColor = pkt.color;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(px, py, pkt.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      if (pkt.progress >= 1) {
        this.packets.splice(i, 1);
      }
    }

    // 6. Draw 3D Nodes & Badges
    projected.forEach(p => {
      const isCenter = p.name.includes("Dhaka");
      const radius = isCenter ? 7 * p.scale : 4.5 * p.scale;

      // Glow halo
      ctx.fillStyle = p.color;
      ctx.shadowColor = p.color;
      ctx.shadowBlur = isCenter ? 16 : 8;
      ctx.beginPath();
      ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      // Inner bright center
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.arc(p.x, p.y, radius * 0.4, 0, Math.PI * 2);
      ctx.fill();

      // Node Label
      ctx.font = `600 ${Math.max(9, Math.round(11 * p.scale))}px "Plus Jakarta Sans", sans-serif`;
      ctx.fillStyle = isCenter ? "#34d399" : "#e2e8f0";
      ctx.fillText(p.name, p.x + radius + 6, p.y + 3);

      // Agency Subtitle
      ctx.font = `500 ${Math.max(8, Math.round(9 * p.scale))}px "JetBrains Mono", monospace`;
      ctx.fillStyle = "#64748b";
      ctx.fillText(p.agency, p.x + radius + 6, p.y + 14);
    });

    // 7. HUD Telemetry Overlay in Top Corners
    ctx.font = '700 10px "JetBrains Mono", monospace';
    ctx.fillStyle = "#10b981";
    ctx.fillText("● 4IR AUTONOMOUS MATRIX — 8 DIVISION MESH ONLINE", 14, 22);

    ctx.font = '500 9px "JetBrains Mono", monospace';
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(`ROTATION: ${(this.rotation % (Math.PI * 2)).toFixed(2)} rad | FOV: 400 | ACTIVE PACKETS: ${this.packets.length}`, 14, 38);

    ctx.restore();
  }
}

// Global Singleton Initializer
window.initHarvester3DRadar = function(canvasId = "harvester3dCanvas") {
  if (document.getElementById(canvasId)) {
    window.harvesterRadarInstance = new Harvester3DRadar(canvasId);
  }
};
