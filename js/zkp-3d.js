/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D Holographic zk-SNARK Cryptographic Circuit & Groth16 Manifold (zkp-3d.js)
 * Grounding: Groth16 over BN254 Elliptic Curve & R1CS Zero-Knowledge Proof Manifold
 * 
 * Renders an interactive 3D cryptographic circuit mapping Merkle tree witness roots,
 * pairing-friendly elliptic curve torus, R1CS constraint gates, and confidential witness shield.
 */

class Zkp3DVisualizer {
  constructor(canvasId = "zkp3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width = this.canvas.offsetWidth || 800;
    this.height = this.canvas.height = this.canvas.offsetHeight || 320;
    this.rotation = 0.55;
    this.tilt = 0.28;
    this.zoom = 1.0;
    this.mouse = { isDown: false, lastX: 0, lastY: 0 };
    this.time = 0;
    this.proofPulse = 0;
    this.proofData = null;
    this.hoveredNode = null;

    // Initialize 3D Merkle Tree & Circuit Nodes
    this.initCircuitTopology();
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
      this.height = this.canvas.height = this.canvas.offsetHeight || 320;
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
        this.tilt = Math.max(-0.7, Math.min(0.7, this.tilt + dy * 0.008));
        this.mouse.lastX = e.clientX;
        this.mouse.lastY = e.clientY;
      }
    });

    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.zoom = Math.max(0.6, Math.min(1.8, this.zoom - e.deltaY * 0.001));
    }, { passive: false });
  }

  initCircuitTopology() {
    // 3D Merkle Tree Nodes
    this.nodes = [
      // Apex: Merkle Root
      { id: "ROOT", label: "Merkle Root", type: "root", x: 0, y: -110, z: 0, color: "#10b981", radius: 9 },
      // Level 1: Internal Hash Nodes
      { id: "L1_0", label: "Hash H(T || L)", type: "internal", x: -90, y: -45, z: -20, color: "#38bdf8", radius: 7 },
      { id: "L1_1", label: "Hash H(ID || TAX)", type: "internal", x: 90, y: -45, z: 20, color: "#38bdf8", radius: 7 },
      // Level 2: Confidential Witness Leaves (Behind privacy shield)
      { id: "W_TURNOVER", label: "Turnover Witness (৳51.2Cr)", type: "leaf", x: -140, y: 35, z: -50, color: "#a855f7", radius: 6, confidential: true },
      { id: "W_LIQUIDITY", label: "Liquid Assets (৳15.0Cr)", type: "leaf", x: -50, y: 35, z: -40, color: "#a855f7", radius: 6, confidential: true },
      { id: "W_IDENTITY", label: "Contractor EGP ID", type: "leaf", x: 50, y: 35, z: 40, color: "#a855f7", radius: 6, confidential: true },
      { id: "W_TAX", label: "Audited Tax Token", type: "leaf", x: 140, y: 35, z: 50, color: "#a855f7", radius: 6, confidential: true },
      
      // R1CS Constraint Gates (Groth16 QAP System)
      { id: "R1CS_0", label: "R1CS Gate: T >= T_req", type: "gate", x: -90, y: 110, z: 70, color: "#f59e0b", radius: 7 },
      { id: "R1CS_1", label: "R1CS Gate: L >= L_req", type: "gate", x: 0, y: 110, z: 90, color: "#f59e0b", radius: 7 },
      { id: "R1CS_2", label: "Pairing e(A,B) == e(α,β)", type: "gate", x: 90, y: 110, z: 70, color: "#ec4899", radius: 8 }
    ];

    // Edges & Constraint Wires
    this.edges = [
      { from: "W_TURNOVER", to: "L1_0", isWitness: true },
      { from: "W_LIQUIDITY", to: "L1_0", isWitness: true },
      { from: "W_IDENTITY", to: "L1_1", isWitness: true },
      { from: "W_TAX", to: "L1_1", isWitness: true },
      { from: "L1_0", to: "ROOT", isWitness: false },
      { from: "L1_1", to: "ROOT", isWitness: false },
      { from: "W_TURNOVER", to: "R1CS_0", isWitness: true },
      { from: "W_LIQUIDITY", to: "R1CS_1", isWitness: true },
      { from: "R1CS_0", to: "R1CS_2", isWitness: false },
      { from: "R1CS_1", to: "R1CS_2", isWitness: false },
      { from: "ROOT", to: "R1CS_2", isWitness: false }
    ];

    // Animated particle stream packets
    this.particles = [];
    for (let i = 0; i < 24; i++) {
      this.particles.push({
        edgeIndex: Math.floor(Math.random() * this.edges.length),
        t: Math.random(),
        speed: 0.008 + Math.random() * 0.012
      });
    }
  }

  setProofState(proof) {
    this.proofData = proof;
    this.proofPulse = 1.0;
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
      scale: Math.max(0.15, scale),
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
    if (this.proofPulse > 0) {
      this.proofPulse = Math.max(0, this.proofPulse - 0.015);
    }

    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Dark Futuristic Cybernetic Background
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

    // 2. Draw 3D Elliptic Curve Pairing Torus / Ring (BN254 Field)
    this.drawPairingTorus(ctx, cx, cy);

    // 3. Draw Holographic Privacy Shield Plane (Separates witness from public)
    this.drawPrivacyShieldPlane(ctx, cx, cy);

    // 4. Draw Circuit Wires & Edges
    this.drawEdges(ctx, cx, cy);

    // 5. Draw Animated Proof Verification Particles
    this.drawParticles(ctx, cx, cy);

    // 6. Draw 3D Tree & Constraint Nodes
    this.drawNodes(ctx, cx, cy);

    // 7. Render Telemetry HUD Overlay
    this.drawHUD(ctx);
  }

  drawPairingTorus(ctx, cx, cy) {
    ctx.save();
    const ringRadius = 180 * this.zoom;
    const segments = 36;
    ctx.beginPath();
    for (let i = 0; i <= segments; i++) {
      const angle = (i / segments) * Math.PI * 2 + this.time * 0.2;
      const px = Math.cos(angle) * ringRadius;
      const pz = Math.sin(angle) * ringRadius;
      const py = Math.sin(angle * 3 + this.time) * 15;
      const p = this.project3D(px, py + 40, pz, cx, cy);
      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.18)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 6]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  }

  drawPrivacyShieldPlane(ctx, cx, cy) {
    // 3D semi-transparent holographic curtain
    const corners = [
      { x: -190, y: 65, z: -80 },
      { x: 190, y: 65, z: -80 },
      { x: 190, y: 65, z: 70 },
      { x: -190, y: 65, z: 70 }
    ];
    const projCorners = corners.map(c => this.project3D(c.x, c.y, c.z, cx, cy));

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(projCorners[0].x, projCorners[0].y);
    for (let i = 1; i < projCorners.length; i++) {
      ctx.lineTo(projCorners[i].x, projCorners[i].y);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(168, 85, 247, 0.05)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(168, 85, 247, 0.35)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Center Shield Label
    const centerProj = this.project3D(0, 65, 0, cx, cy);
    ctx.font = '600 10px "JetBrains Mono", monospace';
    ctx.fillStyle = 'rgba(192, 132, 252, 0.7)';
    ctx.textAlign = 'center';
    ctx.fillText('🛡️ ZERO-KNOWLEDGE WITNESS BLINDING CURTAIN', centerProj.x, centerProj.y);
    ctx.restore();
  }

  drawEdges(ctx, cx, cy) {
    this.edges.forEach(edge => {
      const fromNode = this.nodes.find(n => n.id === edge.from);
      const toNode = this.nodes.find(n => n.id === edge.to);
      if (!fromNode || !toNode) return;

      const p1 = this.project3D(fromNode.x, fromNode.y, fromNode.z, cx, cy);
      const p2 = this.project3D(toNode.x, toNode.y, toNode.z, cx, cy);

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);

      if (edge.isWitness) {
        ctx.strokeStyle = 'rgba(168, 85, 247, 0.45)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 4]);
      } else {
        ctx.strokeStyle = this.proofPulse > 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(56, 189, 248, 0.4)';
        ctx.lineWidth = 1.8;
      }
      ctx.stroke();
      ctx.restore();
    });
  }

  drawParticles(ctx, cx, cy) {
    this.particles.forEach(p => {
      p.t += p.speed;
      if (p.t > 1) p.t = 0;

      const edge = this.edges[p.edgeIndex];
      const fromNode = this.nodes.find(n => n.id === edge.from);
      const toNode = this.nodes.find(n => n.id === edge.to);
      if (!fromNode || !toNode) return;

      const px = fromNode.x + (toNode.x - fromNode.x) * p.t;
      const py = fromNode.y + (toNode.y - fromNode.y) * p.t;
      const pz = fromNode.z + (toNode.z - fromNode.z) * p.t;

      const proj = this.project3D(px, py, pz, cx, cy);

      ctx.save();
      ctx.beginPath();
      ctx.arc(proj.x, proj.y, 2.5 * proj.scale, 0, Math.PI * 2);
      ctx.fillStyle = edge.isWitness ? '#c084fc' : '#10b981';
      ctx.shadowColor = edge.isWitness ? '#a855f7' : '#34d399';
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.restore();
    });
  }

  drawNodes(ctx, cx, cy) {
    // Sort nodes by Z-depth for proper occlusion
    const projectedNodes = this.nodes.map(node => {
      const proj = this.project3D(node.x, node.y, node.z, cx, cy);
      return { ...node, proj };
    }).sort((a, b) => a.proj.z - b.proj.z);

    projectedNodes.forEach(node => {
      const { proj } = node;
      const radius = node.radius * proj.scale;

      ctx.save();
      // Outer Glow Halo
      ctx.beginPath();
      ctx.arc(proj.x, proj.y, radius * (1.8 + this.proofPulse * 0.8), 0, Math.PI * 2);
      ctx.fillStyle = node.color + (this.proofPulse > 0 ? '44' : '22');
      ctx.fill();

      // Node Body
      ctx.beginPath();
      ctx.arc(proj.x, proj.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = node.color;
      ctx.shadowColor = node.color;
      ctx.shadowBlur = 12;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // Node Label
      ctx.font = `600 ${Math.max(9, Math.round(11 * proj.scale))}px "JetBrains Mono", monospace`;
      ctx.fillStyle = node.confidential ? '#e9d5ff' : '#f8fafc';
      ctx.textAlign = 'center';
      ctx.fillText(node.label, proj.x, proj.y - radius - 5);
      ctx.restore();
    });
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
    ctx.fillText('⚡ GROTH16 zk-SNARK PROOF MANIFOLD', 24, 32);

    ctx.font = '500 9.5px "JetBrains Mono", monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText('Curve: BN254 / Alt-bn128 (254-bit Field)', 24, 48);
    ctx.fillText('R1CS Constraints: 2,048 gates (Rank-1)', 24, 62);
    ctx.fillText('Pairing: e(G1, G2) -> GT [Constant O(1)]', 24, 76);

    // Top Right Proof Telemetry
    ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    ctx.strokeStyle = this.proofPulse > 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(168, 85, 247, 0.3)';
    ctx.beginPath();
    ctx.roundRect(this.width - 240, 14, 226, 68, 8);
    ctx.fill();
    ctx.stroke();

    ctx.font = '700 10.5px "JetBrains Mono", monospace';
    ctx.fillStyle = this.proofPulse > 0 ? '#34d399' : '#c084fc';
    ctx.fillText(this.proofData ? '🔐 VERIFIED ZERO-KNOWLEDGE PROOF' : '🔒 CONFIDENTIAL WITNESS ACTIVE', this.width - 228, 32);

    ctx.font = '500 9.5px "JetBrains Mono", monospace';
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText('Proof Size: 128 Bytes (Compressed)', this.width - 228, 48);
    ctx.fillText(`Verifier Gas: ~214,500 gas ($0.00)`, this.width - 228, 62);

    // Bottom Controls Hint
    ctx.font = '500 9.5px "Plus Jakarta Sans", sans-serif';
    ctx.fillStyle = 'rgba(148, 163, 184, 0.7)';
    ctx.textAlign = 'left';
    ctx.fillText('🖱️ Drag to rotate 3D circuit • Scroll to zoom', 16, this.height - 12);
    ctx.restore();
  }
}

window.Zkp3DVisualizer = Zkp3DVisualizer;
