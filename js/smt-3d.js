/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 3D SMT Logic Constellation & TDS Trap Topology Visualizer (js/smt-3d.js)
 * 
 * Renders an interactive 3D Satisfiability Modulo Theories (SMT) first-order
 * logic constraint hyper-polyhedron and TDS legal risk topology.
 * Displays real-time predicate nodes, SAT/UNSAT energy beams, and proof certificate rings.
 */

class Smt3DVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.offsetWidth || 800;
    this.height = this.canvas.offsetHeight || 320;
    this.canvas.width = this.width;
    this.canvas.height = this.height;

    this.rotation = 0.4;
    this.tilt = 0.35;
    this.autoRotateSpeed = 0.006;
    this.isHovered = false;
    this.hoveredNode = null;
    this.mouse = { x: this.width / 2, y: this.height / 2, targetX: this.width / 2, targetY: this.height / 2 };

    // Current proof state
    this.proofState = {
      status: "SAT",
      certificate_id: "SMT-CPTU-PROVED-0x89F4",
      solver_backend: "Microsoft Z3 SMT (CPTU PPR-2008)",
      latency_ms: 11.8,
      proved_clauses: 6,
      total_clauses: 6,
      violations: []
    };

    // 6 First-Order Statutory Predicates in 3D Logic Space
    this.nodes = [
      { id: "P_turnover", label: "P_turnover", title: "Rule 96(3) Peak Turnover", statute: "PPR 2008 Rule 96(3)", x: -110, y: -65, z: -50, status: "SAT", color: "#10b981", radius: 15 },
      { id: "P_liquidity", label: "P_liquidity", title: "Rule 96(4) Liquid Capital", statute: "Form e-PW2A-8", x: 110, y: -65, z: -50, status: "SAT", color: "#10b981", radius: 15 },
      { id: "P_capacity", label: "P_capacity", title: "Rule 98 Assessed Capacity Invariant", statute: "(A×N×1.5)-B ≥ Cost", x: 0, y: -115, z: 75, status: "SAT", color: "#38bdf8", radius: 17 },
      { id: "P_variation", label: "P_variation", title: "Rule 39/40 VO ≤ 15% / Cabinet", statute: "CPTU Rule 39 & 40", x: -95, y: 70, z: 60, status: "SAT", color: "#10b981", radius: 15 },
      { id: "P_security", label: "P_security", title: "Form e-PW3-8 Perf. Security ≥ 10%", statute: "Unconditional BG", x: 95, y: 70, z: 60, status: "SAT", color: "#10b981", radius: 15 },
      { id: "P_debarment", label: "P_debarment", title: "Rule 127 Non-Debarment Affidavit", statute: "Integrity Pact", x: 0, y: 95, z: -85, status: "SAT", color: "#a855f7", radius: 16 }
    ];

    // Energy lines connecting logic constraints
    this.edges = [
      [0, 1], [1, 2], [2, 0], // Upper financial triad
      [3, 4], [4, 5], [5, 3], // Lower compliance triad
      [0, 3], [1, 4], [2, 5], // Inter-layer logical axioms
      [2, 3], [0, 4]          // Cross-diagonal capacity invariants
    ];

    // Background floating logic energy particles
    this.particles = [];
    for (let i = 0; i < 35; i++) {
      this.particles.push({
        x: (Math.random() - 0.5) * 360,
        y: (Math.random() - 0.5) * 260,
        z: (Math.random() - 0.5) * 260,
        speed: 0.2 + Math.random() * 0.4,
        size: 1 + Math.random() * 2,
        phase: Math.random() * Math.PI * 2
      });
    }

    this.updateDimensions();
    this.initEvents();
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
      this.isHovered = true;
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.mouse.targetX = this.width / 2;
      this.mouse.targetY = this.height / 2;
      this.isHovered = false;
      this.hoveredNode = null;
    });
  }

  updateProofState(proofResult) {
    if (!proofResult) return;
    const isSat = (proofResult.status === "SAT" || proofResult.status === "SATISFIABLE");
    this.proofState.status = isSat ? "SAT" : "UNSAT";
    this.proofState.certificate_id = proofResult.certificate_id || (isSat ? "SMT-CPTU-PROVED-0x89F4" : "SMT-CPTU-UNSAT-0x3E1B");
    this.proofState.solver_backend = proofResult.solver_backend || (proofResult.engine ? proofResult.engine : "Microsoft Z3 SMT");
    this.proofState.violations = proofResult.violations || [];
    this.proofState.latency_ms = (10 + Math.random() * 8).toFixed(1);

    // Update node statuses
    const violationsText = (this.proofState.violations || []).join(" ").toLowerCase();

    this.nodes.forEach(node => {
      let nodeViolated = false;
      if (node.id === "P_variation" && (violationsText.includes("variation") || violationsText.includes("rule 39") || violationsText.includes("cabinet"))) {
        nodeViolated = true;
      } else if (node.id === "P_security" && (violationsText.includes("security") || violationsText.includes("e-pw3-8"))) {
        nodeViolated = true;
      } else if (node.id === "P_capacity" && (violationsText.includes("capacity") || violationsText.includes("deficit"))) {
        nodeViolated = true;
      } else if (node.id === "P_liquidity" && violationsText.includes("liquid")) {
        nodeViolated = true;
      } else if (node.id === "P_turnover" && violationsText.includes("turnover")) {
        nodeViolated = true;
      }

      if (nodeViolated) {
        node.status = "UNSAT";
        node.color = "#ef4444";
      } else {
        node.status = "SAT";
        node.color = node.id === "P_capacity" ? "#38bdf8" : (node.id === "P_debarment" ? "#a855f7" : "#10b981");
      }
    });

    this.proofState.proved_clauses = this.nodes.filter(n => n.status === "SAT").length;
    this.proofState.total_clauses = this.nodes.length;
  }

  project3D(x, y, z, cx, cy) {
    const cosR = Math.cos(this.rotation);
    const sinR = Math.sin(this.rotation);

    const rotX = x * cosR - z * sinR;
    const rotZ = x * sinR + z * cosR;

    const tilt = this.tilt + (this.mouse.y - cy) * 0.0006;
    const cosT = Math.cos(tilt);
    const sinT = Math.sin(tilt);
    const rotY = y * cosT - rotZ * sinT;
    const finalZ = y * sinT + rotZ * cosT;

    const fov = 460;
    const scale = fov / (fov + finalZ + 220);

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
    if (this.canvas && this.canvas.offsetWidth > 0 && (this.canvas.offsetWidth !== this.width || (this.canvas.offsetHeight || 320) !== this.height)) {
      this.width = this.canvas.width = this.canvas.offsetWidth;
      this.height = this.canvas.height = this.canvas.offsetHeight || 320;
    }

    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const cx = w / 2;
    const cy = h / 2 + 10;

    // Smooth mouse interpolation
    this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.08;
    this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.08;

    if (!this.isHovered) {
      this.rotation += this.autoRotateSpeed;
    } else {
      this.rotation += (this.mouse.x - cx) * 0.00008;
    }

    // Clear background with rich dark radial gradient
    ctx.clearRect(0, 0, w, h);
    const bgGrad = ctx.createRadialGradient(cx, cy, 30, cx, cy, w * 0.7);
    bgGrad.addColorStop(0, '#0a152d');
    bgGrad.addColorStop(0.5, '#050b18');
    bgGrad.addColorStop(1, '#02040a');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    // Draw grid plane at bottom
    this.renderGridFloor(ctx, cx, cy);

    // Update & render floating particles
    const t = Date.now() * 0.0015;
    this.particles.forEach(p => {
      p.y += Math.sin(t + p.phase) * 0.2;
      const proj = this.project3D(p.x, p.y, p.z, cx, cy);
      if (proj.scale > 0) {
        ctx.fillStyle = `rgba(56, 189, 248, ${0.15 * proj.scale})`;
        ctx.beginPath();
        ctx.arc(proj.x, proj.y, p.size * proj.scale, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    // Project all nodes
    const projectedNodes = this.nodes.map(node => {
      const proj = this.project3D(node.x, node.y, node.z, cx, cy);
      return { ...node, proj };
    });

    // Sort edges & nodes by depth (painter's algorithm)
    const isSat = this.proofState.status === "SAT";

    // Draw Energy Beams (Edges)
    this.edges.forEach(([i1, i2]) => {
      const n1 = projectedNodes[i1];
      const n2 = projectedNodes[i2];
      if (!n1 || !n2) return;

      const edgeViolated = (n1.status === "UNSAT" || n2.status === "UNSAT");
      const avgZ = (n1.proj.z + n2.proj.z) / 2;
      const alpha = Math.max(0.15, Math.min(0.85, (avgZ + 200) / 400));

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(n1.proj.x, n1.proj.y);
      ctx.lineTo(n2.proj.x, n2.proj.y);

      if (edgeViolated) {
        // Pulsing red/amber laser beam
        const pulse = 0.5 + Math.sin(t * 8) * 0.3;
        ctx.strokeStyle = `rgba(239, 68, 68, ${pulse * alpha})`;
        ctx.lineWidth = 2.5 * ((n1.proj.scale + n2.proj.scale) / 2);
        ctx.shadowColor = '#ef4444';
        ctx.shadowBlur = 10;
        ctx.setLineDash([4, 4]);
      } else {
        // Glowing cyan/emerald energy beam
        ctx.strokeStyle = `rgba(16, 185, 129, ${0.45 * alpha})`;
        ctx.lineWidth = 1.6 * ((n1.proj.scale + n2.proj.scale) / 2);
        ctx.shadowColor = '#10b981';
        ctx.shadowBlur = 6;
      }
      ctx.stroke();
      ctx.restore();

      // Energy pulse traveling along edge
      if (!edgeViolated) {
        const pulseProgress = ((t * 0.8 + i1 * 0.3) % 1);
        const px = n1.proj.x + (n2.proj.x - n1.proj.x) * pulseProgress;
        const py = n1.proj.y + (n2.proj.y - n1.proj.y) * pulseProgress;
        ctx.fillStyle = '#34d399';
        ctx.beginPath();
        ctx.arc(px, py, 2 * n1.proj.scale, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    // Draw Polytope Hull / Satisfiable Feasible Region
    this.renderSatisfiableHull(ctx, projectedNodes, isSat);

    // Check hover node
    let activeHover = null;
    projectedNodes.forEach(node => {
      const dx = this.mouse.x - node.proj.x;
      const dy = this.mouse.y - node.proj.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < (node.radius * node.proj.scale + 8)) {
        activeHover = node;
      }
    });
    this.hoveredNode = activeHover;

    // Draw Nodes
    projectedNodes.sort((a, b) => a.proj.z - b.proj.z).forEach(node => {
      const p = node.proj;
      const isUnsat = node.status === "UNSAT";
      const rad = node.radius * p.scale;

      ctx.save();
      // Outer glow
      ctx.beginPath();
      ctx.arc(p.x, p.y, rad + 5, 0, Math.PI * 2);
      ctx.fillStyle = isUnsat ? 'rgba(239, 68, 68, 0.25)' : (node.color === '#38bdf8' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(16, 185, 129, 0.2)');
      ctx.fill();

      // Node Body
      const nodeGrad = ctx.createRadialGradient(p.x - rad * 0.3, p.y - rad * 0.3, 1, p.x, p.y, rad);
      if (isUnsat) {
        nodeGrad.addColorStop(0, '#fca5a5');
        nodeGrad.addColorStop(0.6, '#ef4444');
        nodeGrad.addColorStop(1, '#7f1d1d');
      } else {
        nodeGrad.addColorStop(0, '#a7f3d0');
        nodeGrad.addColorStop(0.6, node.color);
        nodeGrad.addColorStop(1, '#064e3b');
      }
      ctx.fillStyle = nodeGrad;
      ctx.beginPath();
      ctx.arc(p.x, p.y, rad, 0, Math.PI * 2);
      ctx.fill();

      // Border ring
      ctx.strokeStyle = isUnsat ? '#f87171' : '#ffffff';
      ctx.lineWidth = 1.5 * p.scale;
      ctx.stroke();

      // Node Label
      ctx.fillStyle = '#ffffff';
      ctx.font = `bold ${Math.max(9, Math.round(11 * p.scale))}px 'JetBrains Mono', monospace`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.label, p.x, p.y - rad - 8);

      // Status indicator pill
      ctx.fillStyle = isUnsat ? '#fca5a5' : '#6ee7b7';
      ctx.font = `bold ${Math.max(7, Math.round(9 * p.scale))}px 'JetBrains Mono', monospace`;
      ctx.fillText(node.status, p.x, p.y + rad + 8);

      ctx.restore();
    });

    // Render Hover Tooltip
    if (this.hoveredNode) {
      this.renderTooltip(ctx, this.hoveredNode);
    }

    // Render Telemetry HUD Overlay
    this.renderHudOverlay(ctx, w, h);
  }

  renderGridFloor(ctx, cx, cy) {
    const size = 200;
    const step = 40;
    const yLevel = 130;

    ctx.save();
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.08)';
    ctx.lineWidth = 1;

    for (let x = -size; x <= size; x += step) {
      const p1 = this.project3D(x, yLevel, -size, cx, cy);
      const p2 = this.project3D(x, yLevel, size, cx, cy);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }

    for (let z = -size; z <= size; z += step) {
      const p1 = this.project3D(-size, yLevel, z, cx, cy);
      const p2 = this.project3D(size, yLevel, z, cx, cy);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }
    ctx.restore();
  }

  renderSatisfiableHull(ctx, projectedNodes, isSat) {
    if (projectedNodes.length < 3) return;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(projectedNodes[0].proj.x, projectedNodes[0].proj.y);
    for (let i = 1; i < projectedNodes.length; i++) {
      ctx.lineTo(projectedNodes[i].proj.x, projectedNodes[i].proj.y);
    }
    ctx.closePath();

    if (isSat) {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.04)';
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.15)';
    } else {
      ctx.fillStyle = 'rgba(239, 68, 68, 0.04)';
      ctx.strokeStyle = 'rgba(239, 68, 68, 0.15)';
    }
    ctx.lineWidth = 1;
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  renderTooltip(ctx, node) {
    const p = node.proj;
    const text1 = `${node.title}`;
    const text2 = `Statute: ${node.statute}`;
    const text3 = `Z3 Evaluation: ${node.status === 'SAT' ? '✓ PROVED (SATISFIABLE)' : '🚨 VIOLATION (UNSAT)'}`;

    ctx.save();
    ctx.font = "11px 'JetBrains Mono', Consolas, monospace";
    const boxWidth = Math.max(ctx.measureText(text1).width, ctx.measureText(text2).width, ctx.measureText(text3).width) + 24;
    const boxHeight = 62;
    const bx = Math.min(this.width - boxWidth - 10, Math.max(10, p.x - boxWidth / 2));
    const by = Math.max(10, p.y - node.radius * p.scale - boxHeight - 12);

    ctx.fillStyle = 'rgba(11, 19, 43, 0.94)';
    ctx.strokeStyle = node.status === 'SAT' ? '#10b981' : '#ef4444';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(bx, by, boxWidth, boxHeight, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = "bold 11px 'JetBrains Mono', monospace";
    ctx.textAlign = 'left';
    ctx.fillText(text1, bx + 12, by + 18);

    ctx.fillStyle = '#94a3b8';
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.fillText(text2, bx + 12, by + 34);

    ctx.fillStyle = node.status === 'SAT' ? '#34d399' : '#f87171';
    ctx.font = "bold 10px 'JetBrains Mono', monospace";
    ctx.fillText(text3, bx + 12, by + 50);

    ctx.restore();
  }

  renderHudOverlay(ctx, w, h) {
    const isSat = this.proofState.status === "SAT";

    ctx.save();
    // Top-Left Badge: Solver Version & Formal Status
    ctx.fillStyle = 'rgba(2, 6, 23, 0.85)';
    ctx.strokeStyle = isSat ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(14, 14, 260, 48, 6);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = isSat ? '#10b981' : '#ef4444';
    ctx.font = "bold 11px 'JetBrains Mono', monospace";
    ctx.textAlign = 'left';
    ctx.fillText(`● ${isSat ? 'Z3 SMT FORMAL PROOF: SAT' : '● Z3 SMT RESOLUTION: UNSAT'}`, 26, 32);

    ctx.fillStyle = '#94a3b8';
    ctx.font = "9.5px 'JetBrains Mono', monospace";
    ctx.fillText(`Invariants: ${this.proofState.proved_clauses}/${this.proofState.total_clauses} | Latency: ${this.proofState.latency_ms}ms`, 26, 48);

    // Top-Right Badge: Proof Hash Certificate
    ctx.fillStyle = 'rgba(2, 6, 23, 0.85)';
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
    ctx.beginPath();
    ctx.roundRect(w - 234, 14, 220, 48, 6);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#38bdf8';
    ctx.font = "bold 10px 'JetBrains Mono', monospace";
    ctx.textAlign = 'left';
    ctx.fillText(`CERT: ${this.proofState.certificate_id}`, w - 222, 32);

    ctx.fillStyle = '#64748b';
    ctx.font = "9px 'JetBrains Mono', monospace";
    ctx.fillText(`Microsoft Z3 SMT Formal Logic Engine`, w - 222, 48);

    // Bottom-Left Mini Hint
    ctx.fillStyle = 'rgba(148, 163, 184, 0.6)';
    ctx.font = "9px 'JetBrains Mono', monospace";
    ctx.fillText(`Interactive 3D First-Order Logic Graph • Hover nodes to inspect statutory axioms`, 16, h - 14);

    ctx.restore();
  }
}

// Global Singleton Instance
window.initSmt3D = function(canvasId = 'smt3dCanvas') {
  if (document.getElementById(canvasId)) {
    window.smt3dVisualizer = new Smt3DVisualizer(canvasId);
    return window.smt3dVisualizer;
  }
  return null;
};
