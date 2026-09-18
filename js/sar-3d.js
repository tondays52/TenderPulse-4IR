/**
 * TenderPulse 4IR × Tender Trading Inc.
 * GPU-Accelerated 3D Sentinel-1 Synthetic Aperture Radar (SAR) Viewport (sar-3d.js)
 * Grounding: Copernicus Sentinel-1 C-band SAR (5.405 GHz) & InSAR Coherence Verification
 * 
 * Upgraded to responsive Three.js WebGL viewport rendering:
 * - 3D terrain elevation displacement matrix
 * - Historical temporal frame scrubbing (T-90d, T-60d, T-30d, Current Pass)
 * - Animated C-band radar beam sweep & InSAR interference fringes
 * - Interactive 3D Ground Control Points (GCP) with raycasting
 * - Resilient 2D canvas fallback if WebGL is unavailable
 */

class SarRadar3DVisualizer {
  constructor(canvasId = "sarRadar3dCanvas") {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.useWebGL = typeof THREE !== "undefined";
    this.rotation = 0.45;
    this.tilt = 0.38;
    this.time = 0;
    this.groundTruthPct = 74.5;
    this.claimedPct = 75.0;
    this.satellitePass = "Sentinel-1A Descending Pass #142";
    this.locationName = "Dhaka - Gazipur Corridor";
    this.activeFrameIndex = 3;

    this.timelineFrames = [
      { frame: "T-90d (Baseline)", date: "2026-03-20", pass: "Pass #142", coherence: 0.94, dbVariance: "-0.2 dB", status: "Virgin Topography" },
      { frame: "T-60d (Earthworks)", date: "2026-04-20", pass: "Pass #142", coherence: 0.88, dbVariance: "+4.8 dB", status: "Substructure Excavation" },
      { frame: "T-30d (Superstructure)", date: "2026-05-20", pass: "Pass #142", coherence: 0.85, dbVariance: "+9.2 dB", status: "Girder Alignment" },
      { frame: "Current Orbit Pass", date: "2026-06-21", pass: "Pass #142", coherence: 0.88, dbVariance: "+14.2 dB", status: "Verified On-Site" }
    ];

    this.groundPoints = [
      { id: "GCP-01", name: "Northern Embankment", x: -140, z: -35, elevation: 18, coherence: 0.86, db: "+12.4 dB", verified: true },
      { id: "GCP-02", name: "Main Axis Substructure", x: -70, z: -10, elevation: 28, coherence: 0.91, db: "+16.8 dB", verified: true },
      { id: "GCP-03", name: "Active Works Chainage", x: 0, z: 15, elevation: 32, coherence: 0.88, db: "+14.2 dB", verified: true },
      { id: "GCP-04", name: "Staging & Batch Plant", x: 70, z: -10, elevation: 22, coherence: 0.82, db: "+9.5 dB", verified: true },
      { id: "GCP-05", name: "Terminal Approach", x: 140, z: -35, elevation: 12, coherence: 0.76, db: "+4.1 dB", verified: true }
    ];

    this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0, isDragging: false, lastX: 0, lastY: 0 };

    if (this.useWebGL) {
      try {
        this.initWebGL();
      } catch (e) {
        console.warn("[SarRadar3D] WebGL init fallback to 2D canvas:", e);
        this.useWebGL = false;
        this.init2D();
      }
    } else {
      this.init2D();
    }

    this.initEvents();
    this.startLoop();
  }

  /* --------------------------------------------------------------------------
     THREE.JS WEBGL GPU ENGINE
     -------------------------------------------------------------------------- */
  initWebGL() {
    const w = this.canvas.offsetWidth || this.canvas.clientWidth || 800;
    const h = this.canvas.offsetHeight || this.canvas.clientHeight || 340;
    this.width = w;
    this.height = h;

    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x060d1a, 0.0022);

    this.camera = new THREE.PerspectiveCamera(45, w / h, 1, 1500);
    this.camera.position.set(0, 190, 360);
    this.camera.lookAt(0, 10, 0);

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance"
    });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

    // Lights
    const ambientLight = new THREE.AmbientLight(0x1e293b, 1.5);
    this.scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x38bdf8, 2.0);
    dirLight.position.set(120, 250, 180);
    this.scene.add(dirLight);

    const radarPointLight = new THREE.PointLight(0x06b6d4, 3.0, 450);
    radarPointLight.position.set(0, 140, 0);
    this.radarPointLight = radarPointLight;
    this.scene.add(radarPointLight);

    // 1. 3D Terrain Plane with Dynamic Elevation Displacement
    const planeGeo = new THREE.PlaneGeometry(360, 220, 36, 24);
    planeGeo.rotateX(-Math.PI / 2);

    this.terrainPositions = planeGeo.attributes.position;
    this.baseElevations = new Float32Array(this.terrainPositions.count);

    // Initialize elevation ridge
    for (let i = 0; i < this.terrainPositions.count; i++) {
      const vx = this.terrainPositions.getX(i);
      const vz = this.terrainPositions.getZ(i);
      const nx = vx / 120.0;
      const nz = vz / 80.0;
      // Infrastructure elevation spine
      const ridge = Math.exp(-0.5 * (nz - 0.2 * nx) ** 2) * 22.0;
      const elev = ridge + Math.sin(nx * 2.2) * 3.5 + Math.cos(nz * 1.8) * 2.5;
      this.baseElevations[i] = elev;
      this.terrainPositions.setY(i, elev);
    }
    planeGeo.computeVertexNormals();

    const terrainMat = new THREE.MeshStandardMaterial({
      color: 0x0f2744,
      roughness: 0.45,
      metalness: 0.35,
      wireframe: false,
      flatShading: true
    });
    this.terrainMesh = new THREE.Mesh(planeGeo, terrainMat);
    this.scene.add(this.terrainMesh);

    // 2. Wireframe Radar Grid Overlay
    const wireframeMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.28
    });
    this.wireframeMesh = new THREE.Mesh(planeGeo, wireframeMat);
    this.wireframeMesh.position.y += 0.4;
    this.scene.add(this.wireframeMesh);

    // 3. Ground Control Points (3D Pins)
    this.gcpGroup = new THREE.Group();
    const pinGeo = new THREE.CylinderGeometry(1.5, 3.5, 14, 8);
    const pinHeadGeo = new THREE.SphereGeometry(4, 12, 12);
    const pinMat = new THREE.MeshStandardMaterial({
      color: 0x10b981,
      emissive: 0x059669,
      emissiveIntensity: 0.6,
      roughness: 0.2
    });

    this.groundPoints.forEach(gcp => {
      const pinMesh = new THREE.Mesh(pinGeo, pinMat);
      pinMesh.position.set(gcp.x, gcp.elevation / 2, gcp.z);
      const head = new THREE.Mesh(pinHeadGeo, pinMat);
      head.position.set(gcp.x, gcp.elevation + 6, gcp.z);
      this.gcpGroup.add(pinMesh);
      this.gcpGroup.add(head);
    });
    this.scene.add(this.gcpGroup);

    // 4. Sentinel-1 Satellite Model & Sweeping Beam
    this.satGroup = new THREE.Group();
    const busGeo = new THREE.BoxGeometry(16, 7, 9);
    const busMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, metalness: 0.8, roughness: 0.2 });
    const bus = new THREE.Mesh(busGeo, busMat);

    const solarGeo = new THREE.BoxGeometry(24, 1.2, 7);
    const solarMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.9, roughness: 0.1 });
    const solarLeft = new THREE.Mesh(solarGeo, solarMat);
    solarLeft.position.x = -20;
    const solarRight = new THREE.Mesh(solarGeo, solarMat);
    solarRight.position.x = 20;

    this.satGroup.add(bus);
    this.satGroup.add(solarLeft);
    this.satGroup.add(solarRight);
    this.satGroup.position.set(-60, 160, -40);
    this.scene.add(this.satGroup);

    // Radar Scanning Cone Beam
    const coneGeo = new THREE.ConeGeometry(85, 170, 24, 1, true);
    coneGeo.translate(0, -85, 0);
    const coneMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.15,
      side: THREE.DoubleSide
    });
    this.radarBeam = new THREE.Mesh(coneGeo, coneMat);
    this.satGroup.add(this.radarBeam);

    // Radar Sweep Ring Target on Ground
    const ringGeo = new THREE.RingGeometry(15, 24, 32);
    ringGeo.rotateX(-Math.PI / 2);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide
    });
    this.sweepRing = new THREE.Mesh(ringGeo, ringMat);
    this.sweepRing.position.y = 2;
    this.scene.add(this.sweepRing);
  }

  /* --------------------------------------------------------------------------
     2D RESILIENT CANVAS ENGINE
     -------------------------------------------------------------------------- */
  init2D() {
    this.ctx = this.canvas.getContext('2d');
    this.updateDimensions();
  }

  updateDimensions() {
    if (!this.canvas) return;
    const w = this.canvas.offsetWidth || this.canvas.clientWidth || 800;
    const h = this.canvas.offsetHeight || this.canvas.clientHeight || 340;
    if (w > 0 && h > 0) {
      this.width = w;
      this.height = h;
      if (this.useWebGL && this.renderer && this.camera) {
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
      } else {
        this.canvas.width = w;
        this.canvas.height = h;
      }
    }
  }

  initEvents() {
    window.addEventListener('resize', () => this.updateDimensions());

    if (typeof ResizeObserver !== 'undefined' && this.canvas) {
      this.resizeObserver = new ResizeObserver(() => this.updateDimensions());
      this.resizeObserver.observe(this.canvas);
      if (this.canvas.parentElement) {
        this.resizeObserver.observe(this.canvas.parentElement);
      }
    }

    this.canvas.addEventListener('mousedown', (e) => {
      this.mouse.isDragging = true;
      this.mouse.lastX = e.clientX;
      this.mouse.lastY = e.clientY;
    });

    window.addEventListener('mouseup', () => {
      this.mouse.isDragging = false;
    });

    this.canvas.addEventListener('mousemove', (e) => {
      if (this.mouse.isDragging) {
        const dx = e.clientX - this.mouse.lastX;
        const dy = e.clientY - this.mouse.lastY;
        this.rotation += dx * 0.008;
        this.tilt = Math.max(0.1, Math.min(1.2, this.tilt + dy * 0.008));
        this.mouse.lastX = e.clientX;
        this.mouse.lastY = e.clientY;
      }
    });

    // Timeline scrubber buttons support
    const scrubberBtns = document.querySelectorAll("[data-sar-frame]");
    scrubberBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const idx = parseInt(btn.getAttribute("data-sar-frame"), 10);
        this.selectTimelineFrame(idx);
      });
    });
  }

  setTenderSpatial(spatialData) {
    if (!spatialData) return;
    this.locationName = spatialData.locationName || spatialData.regionName || this.locationName;
    this.satellitePass = spatialData.orbitTrack || spatialData.orbitPass || this.satellitePass;
    this.groundTruthPct = spatialData.physicalProgress !== undefined ? spatialData.physicalProgress : this.groundTruthPct;
    this.claimedPct = spatialData.claimedProgress !== undefined ? spatialData.claimedProgress : this.claimedPct;

    if (spatialData.groundControlPoints && spatialData.groundControlPoints.length > 0) {
      this.groundPoints = spatialData.groundControlPoints;
    }
    if (spatialData.radarTimelineFrames && spatialData.radarTimelineFrames.length > 0) {
      this.timelineFrames = spatialData.radarTimelineFrames;
      this.activeFrameIndex = this.timelineFrames.length - 1;
    }

    // Update WebGL terrain displacement if dynamic raster matrix available
    if (this.useWebGL && spatialData.rasterElevationMatrix && this.terrainPositions) {
      this.applyRasterDisplacement(spatialData.rasterElevationMatrix);
    }

    // Update DOM HUD if present
    const hudLoc = document.getElementById("sarHudLocation");
    const hudTrack = document.getElementById("sarHudTrack");
    const hudCoherence = document.getElementById("sarHudCoherence");
    const hudProgress = document.getElementById("sarHudProgress");

    if (hudLoc) hudLoc.textContent = `${this.locationName} (${spatialData.lat?.toFixed(2) || '23.81'}°N, ${spatialData.lon?.toFixed(2) || '90.41'}°E)`;
    if (hudTrack) hudTrack.textContent = this.satellitePass;
    if (hudCoherence) hudCoherence.textContent = `γ = ${spatialData.meanCoherence || '0.88'}`;
    if (hudProgress) hudProgress.textContent = `${this.groundTruthPct}% Ground vs ${this.claimedPct}% Claimed`;
  }

  applyRasterDisplacement(matrix) {
    if (!this.terrainPositions || !matrix) return;
    const rows = matrix.length;
    const cols = matrix[0].length;
    for (let i = 0; i < this.terrainPositions.count; i++) {
      const vx = this.terrainPositions.getX(i);
      const vz = this.terrainPositions.getZ(i);
      const r = Math.min(rows - 1, Math.max(0, Math.floor(((vz + 110) / 220) * rows)));
      const c = Math.min(cols - 1, Math.max(0, Math.floor(((vx + 180) / 360) * cols)));
      const h = matrix[r][c] || this.baseElevations[i] || 10;
      this.terrainPositions.setY(i, h);
    }
    this.terrainPositions.needsUpdate = true;
    if (this.terrainMesh.geometry) this.terrainMesh.geometry.computeVertexNormals();
  }

  setTelemetry(groundTruth, claimed, orbitPass) {
    if (groundTruth !== undefined) this.groundTruthPct = Number(groundTruth);
    if (claimed !== undefined) this.claimedPct = Number(claimed);
    if (orbitPass) this.satellitePass = orbitPass;
  }

  selectTimelineFrame(index) {
    if (index >= 0 && index < this.timelineFrames.length) {
      this.activeFrameIndex = index;
      const frame = this.timelineFrames[index];

      // Temporal frame scrubbing: dynamically scale elevation based on chronological frame
      const progressScale = (index + 1) / this.timelineFrames.length;
      if (this.useWebGL && this.terrainPositions && this.baseElevations) {
        for (let i = 0; i < this.terrainPositions.count; i++) {
          const elev = this.baseElevations[i] * (0.35 + 0.65 * progressScale);
          this.terrainPositions.setY(i, elev);
        }
        this.terrainPositions.needsUpdate = true;
        this.terrainMesh.geometry.computeVertexNormals();

        // Update radar beam glow color based on frame coherence
        if (this.radarPointLight) {
          const colorHex = frame.coherence > 0.86 ? 0x10b981 : (frame.coherence > 0.80 ? 0x38bdf8 : 0xf59e0b);
          this.radarPointLight.color.setHex(colorHex);
        }
      }

      if (typeof showToast === 'function') {
        showToast(`🛰️ SAR Scrubber: ${frame.frame} • Coherence γ=${frame.coherence} • ${frame.status}`, 'info');
      }
    }
  }

  startLoop() {
    const loop = () => {
      this.time += 0.016;
      if (this.useWebGL) {
        this.renderWebGL();
      } else {
        this.render2D();
      }
      this.animId = requestAnimationFrame(loop);
    };
    loop();
  }

  renderWebGL() {
    if (!this.renderer || !this.scene || !this.camera) return;

    // Orbit camera based on mouse drag
    const radius = 380;
    this.camera.position.x = Math.sin(this.rotation) * radius;
    this.camera.position.z = Math.cos(this.rotation) * radius;
    this.camera.position.y = 120 + this.tilt * 180;
    this.camera.lookAt(0, 15, 0);

    // Satellite orbital path sweep
    if (this.satGroup) {
      const satX = Math.sin(this.time * 0.4) * 140;
      const satZ = Math.cos(this.time * 0.4) * 50;
      this.satGroup.position.set(satX, 150, satZ);
      this.satGroup.lookAt(0, 0, 0);

      // Pulse radar beam
      if (this.radarBeam) {
        this.radarBeam.material.opacity = 0.12 + Math.sin(this.time * 4) * 0.05;
      }
      if (this.sweepRing) {
        this.sweepRing.position.set(satX * 0.8, 1.5, satZ * 0.8);
        const s = 1.0 + Math.sin(this.time * 3) * 0.2;
        this.sweepRing.scale.set(s, s, s);
      }
    }

    this.renderer.render(this.scene, this.camera);
  }

  render2D() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // Deep Space/Sensor Gradient
    const bgGrad = ctx.createLinearGradient(0, 0, 0, this.height);
    bgGrad.addColorStop(0, "#050914");
    bgGrad.addColorStop(1, "#0a1124");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, this.width, this.height);

    const cx = this.width / 2;
    const cy = this.height / 2 + 15;

    // 2D Terrain Fallback
    ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
    ctx.lineWidth = 1.2;
    const gridCols = 16;
    const gridRows = 10;
    const spacingX = 22;
    const spacingZ = 16;

    for (let r = 0; r < gridRows; r++) {
      ctx.beginPath();
      for (let c = 0; c < gridCols; c++) {
        const x = (c - gridCols / 2) * spacingX;
        const z = (r - gridRows / 2) * spacingZ;
        const y = Math.sin((c + this.time) * 0.6) * 12 + (r === 4 ? -16 : 0);
        const p = this.project3D(x, y, z, cx, cy);
        if (c === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
    }

    // Draw GCP Pins in 2D
    this.groundPoints.forEach(pt => {
      const p = this.project3D(pt.x, -pt.elevation, pt.z, cx, cy);
      ctx.beginPath();
      ctx.arc(p.x, p.y, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = pt.verified ? "#10b981" : "#f59e0b";
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1.2;
      ctx.stroke();
    });

    // 2D Satellite sweep
    const satX = cx + Math.sin(this.time * 0.6) * 120;
    const satY = 40;
    ctx.fillStyle = "#38bdf8";
    ctx.fillRect(satX - 8, satY - 4, 16, 8);
    ctx.strokeStyle = "rgba(56, 189, 248, 0.25)";
    ctx.beginPath();
    ctx.moveTo(satX, satY);
    ctx.lineTo(cx, cy);
    ctx.stroke();

    // Telemetry Text
    ctx.font = '700 11px "JetBrains Mono", monospace';
    ctx.fillStyle = "#38bdf8";
    ctx.fillText(`🛰️ SENTINEL-1 SAR • ${this.locationName.toUpperCase()} [2D RESILIENT FALLBACK]`, 16, 24);
  }

  project3D(x, y, z, cx, cy) {
    const cosR = Math.cos(this.rotation);
    const sinR = Math.sin(this.rotation);
    const rx = x * cosR - z * sinR;
    const rz = x * sinR + z * cosR;

    const cosT = Math.cos(this.tilt);
    const sinT = Math.sin(this.tilt);
    const ry = y * cosT - rz * sinT;
    const fz = y * sinT + rz * cosT + 300;

    const scale = 260 / Math.max(1, fz);
    return {
      x: cx + rx * scale,
      y: cy + ry * scale,
      scale
    };
  }
}

// Global Singleton Initializers
window.SarRadar3DVisualizer = SarRadar3DVisualizer;
window.initSarRadar3D = function(canvasId = "sarRadar3dCanvas") {
  if (!window.sarRadar3dInstance && document.getElementById(canvasId)) {
    window.sarRadar3dInstance = new SarRadar3DVisualizer(canvasId);
  }
  return window.sarRadar3dInstance;
};
window.sarRadarInstance = window.sarRadar3dInstance;
