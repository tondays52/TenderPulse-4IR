/**
 * TenderPulse 4IR × Tender Trading Inc.
 * 64-District Bangladesh GIS Cartel Heat Map & Geospatial Threat Viewport (js/district-heatmap.js)
 * 
 * Renders an interactive, GPU-accelerated Canvas geospatial projection:
 * - 64 District Centroids with logarithmic volume scaling & threat-tier choropleth glow
 * - Dynamic pulsating sonar rings on CRITICAL cartel rings (<65 Integrity Score)
 * - Animated cross-district syndicate collusion tentacles (bezier arcs)
 * - Real-time filtering by Division, Agency, and Threat Tier
 * - Interactive Pan, Zoom, District Inspection Tooltip & High-Threat Leaderboard
 */

class BangladeshGisHeatmap {
  constructor(canvasId = "gisDistrictCanvas") {
    this.canvasId = canvasId;
    this.canvas = null;
    this.ctx = null;
    this.container = null;

    // Geographic Bounding Box for Bangladesh
    this.geoBounds = {
      minLon: 88.01,
      maxLon: 92.70,
      minLat: 20.55,
      maxLat: 26.65
    };

    // Camera / Viewport Transform
    this.scale = 1.0;
    this.offsetX = 0;
    this.offsetY = 0;
    this.isDragging = false;
    this.dragStart = { x: 0, y: 0 };
    this.mouse = { x: 0, y: 0, isHovered: false };
    this.hoveredDistrict = null;
    this.selectedDistrict = null;

    // Animation & Pulse
    this.animTime = 0;
    this.animationFrameId = null;

    // Telemetry Data State
    this.telemetry = null;
    this.districts = [];
    this.collusionArcs = [];
    this.filteredDistricts = [];

    // Active Filters
    this.currentFilters = {
      division: "All",
      agency: "All",
      year: "All",
      threatTier: "All"
    };

    // Styling Tokens
    this.tierColors = {
      CRITICAL: "#ef4444",
      HIGH: "#f97316",
      ELEVATED: "#f59e0b",
      MODERATE: "#06b6d4",
      CLEAN: "#10b981"
    };

    // Live WebSocket Stream State
    this.ws = null;
    this._wsReconnectDelay = 2000;
    this._wsRetries = 0;
    this._wsMaxRetries = 20;
    this.liveEnabled = true;

    // Active Sonar Blip Particles
    this.activeBlips = [];

    // Live Ticker History (last 4 events)
    this.liveTickerEvents = [];
    this.liveTotalEvents = 0;
    this.liveCollusiveCount = 0;

    // Audio Engine
    this._audioCtx = null;
    this._audioMuted = true;  // default: muted (browser autoplay policy)
  }

  init() {
    this.canvas = document.getElementById(this.canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext("2d");
    this.container = this.canvas.parentElement;

    this.resize();
    window.addEventListener("resize", () => this.resize());

    this.attachEventListeners();
    this.loadHeatmapData();
    this.startAnimationLoop();
    this.buildLiveTicker();
    this.connectLiveStream();
  }

  resize() {
    if (!this.canvas || !this.container) return;
    const rect = this.container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const w = rect.width || 800;
    const h = 540;

    this.width = w;
    this.height = h;
    this.canvas.width = w * dpr;
    this.canvas.height = h * dpr;
    this.canvas.style.width = `${w}px`;
    this.canvas.style.height = `${h}px`;

    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.scale(dpr, dpr);
  }

  attachEventListeners() {
    if (!this.canvas) return;

    this.canvas.addEventListener("mousedown", (e) => {
      this.isDragging = true;
      this.dragStart = { x: e.clientX - this.offsetX, y: e.clientY - this.offsetY };
    });

    window.addEventListener("mousemove", (e) => {
      if (this.isDragging) {
        this.offsetX = e.clientX - this.dragStart.x;
        this.offsetY = e.clientY - this.dragStart.y;
      }
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
    });

    this.canvas.addEventListener("mousemove", (e) => {
      const rect = this.canvas.getBoundingClientRect();
      this.mouse.x = e.clientX - rect.left;
      this.mouse.y = e.clientY - rect.top;
      this.mouse.isHovered = true;
      this.detectHoveredDistrict();
    });

    this.canvas.addEventListener("mouseleave", () => {
      this.mouse.isHovered = false;
      this.hoveredDistrict = null;
    });

    this.canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.88;
      this.zoomAtPoint(zoomFactor, this.mouse.x, this.mouse.y);
    }, { passive: false });

    this.canvas.addEventListener("click", () => {
      if (this.hoveredDistrict) {
        this.selectDistrict(this.hoveredDistrict);
      } else {
        this.selectedDistrict = null;
        this.updateInspectorCard();
      }
    });
  }

  zoomAtPoint(factor, px, py) {
    const newScale = Math.max(0.6, Math.min(6.0, this.scale * factor));
    const ratio = newScale / this.scale;
    this.offsetX = px - (px - this.offsetX) * ratio;
    this.offsetY = py - (py - this.offsetY) * ratio;
    this.scale = newScale;
  }

  resetView() {
    this.scale = 1.0;
    this.offsetX = 0;
    this.offsetY = 0;
    this.selectedDistrict = null;
    this.updateInspectorCard();
  }

  focusDistrict(districtName) {
    const dist = this.districts.find(d => d.district.toLowerCase() === districtName.toLowerCase());
    if (!dist) return;
    this.selectDistrict(dist);

    const pt = this.geoToScreen(dist.latitude, dist.longitude, 1.0, 0, 0);
    this.scale = 2.4;
    this.offsetX = (this.width / 2) - (pt.x * this.scale);
    this.offsetY = (this.height / 2) - (pt.y * this.scale);
  }

  geoToScreen(lat, lon, scale = this.scale, offX = this.offsetX, offY = this.offsetY) {
    const lonNorm = (lon - this.geoBounds.minLon) / (this.geoBounds.maxLon - this.geoBounds.minLon);
    const latNorm = (this.geoBounds.maxLat - lat) / (this.geoBounds.maxLat - this.geoBounds.minLat);

    const pad = 40;
    const drawW = this.width - (pad * 2);
    const drawH = this.height - (pad * 2);

    const baseCenterX = this.width / 2;
    const baseCenterY = this.height / 2;

    const rawX = pad + (lonNorm * drawW);
    const rawY = pad + (latNorm * drawH);

    const x = baseCenterX + ((rawX - baseCenterX) * scale) + offX;
    const y = baseCenterY + ((rawY - baseCenterY) * scale) + offY;

    return { x, y };
  }

  async loadHeatmapData() {
    try {
      if (window.TenderApiService && typeof window.TenderApiService.getDistrictHeatmap === "function") {
        const res = await window.TenderApiService.getDistrictHeatmap(this.currentFilters);
        if (res && res.districts) {
          this.telemetry = res;
          this.districts = res.districts;
          this.collusionArcs = res.collusion_arcs || [];
          this.applyClientFilters();
          this.renderTelemetryHUD();
          this.renderLeaderboard();
          return;
        }
      }
    } catch (err) {
      console.warn("[GisHeatmap] Backend fetch failed, generating local fallback telemetry:", err);
    }
    this.generateFallbackTelemetry();
  }

  generateFallbackTelemetry() {
    this.districts = [
      { district: "Dhaka", division: "Dhaka", latitude: 23.8103, longitude: 90.4125, total_packages: 6840, total_volume_cr: 11240.5, collusive_packages: 980, collusive_volume_cr: 1680.2, collusion_rate_pct: 14.95, integrity_score: 61.1, threat_score: 38.9, threat_tier: "CRITICAL", tier_color: "#ef4444", active_syndicates: ["Padma-Jamuna Highway Syndicate", "Dhaka South Metro Building Cartel"], primary_vector: "GUARANTEE" },
      { district: "Faridpur", division: "Dhaka", latitude: 23.6071, longitude: 89.8429, total_packages: 1840, total_volume_cr: 2450.0, collusive_packages: 340, collusive_volume_cr: 480.0, collusion_rate_pct: 19.59, integrity_score: 49.1, threat_score: 50.9, threat_tier: "CRITICAL", tier_color: "#ef4444", active_syndicates: ["Padma-Jamuna Highway Syndicate"], primary_vector: "GUARANTEE" },
      { district: "Rangpur", division: "Rangpur", latitude: 25.7439, longitude: 89.2752, total_packages: 2150, total_volume_cr: 3120.0, collusive_packages: 320, collusive_volume_cr: 460.0, collusion_rate_pct: 14.74, integrity_score: 61.7, threat_score: 38.3, threat_tier: "CRITICAL", tier_color: "#ef4444", active_syndicates: ["Northern Road Sector Ring"], primary_vector: "GUARANTEE" },
      { district: "Chattogram", division: "Chattogram", latitude: 22.3569, longitude: 91.7832, total_packages: 5120, total_volume_cr: 8920.0, collusive_packages: 640, collusive_volume_cr: 1150.0, collusion_rate_pct: 12.89, integrity_score: 66.5, threat_score: 33.5, threat_tier: "HIGH", tier_color: "#f97316", active_syndicates: ["Chittagong Coastal Embankment Cartel"], primary_vector: "ADDRESS" },
      { district: "Barishal", division: "Barishal", latitude: 22.7010, longitude: 90.3535, total_packages: 1920, total_volume_cr: 2840.0, collusive_packages: 290, collusive_volume_cr: 410.0, collusion_rate_pct: 14.44, integrity_score: 62.5, threat_score: 37.5, threat_tier: "CRITICAL", tier_color: "#ef4444", active_syndicates: ["Barisal River Dredging Alliance"], primary_vector: "ROTATIONAL" }
    ];
    this.collusionArcs = [
      { syndicate: "Padma-Jamuna Highway Syndicate", source_district: "Dhaka", target_district: "Faridpur", source_lat: 23.8103, source_lon: 90.4125, target_lat: 23.6071, target_lon: 89.8429, color: "#ef4444", risk: 94.8 }
    ];
    this.telemetry = {
      total_districts: 64,
      national_integrity_score: 72.7,
      total_packages: 50200,
      total_volume_cr: 74510.1,
      collusive_packages: 5488,
      collusive_volume_cr: 6935.9,
      critical_threat_districts_count: 14,
      high_threat_districts_count: 18,
      clean_districts_count: 22
    };
    this.applyClientFilters();
    this.renderTelemetryHUD();
    this.renderLeaderboard();
  }

  applyClientFilters() {
    this.filteredDistricts = this.districts.filter(d => {
      if (this.currentFilters.division !== "All" && d.division !== this.currentFilters.division) return false;
      if (this.currentFilters.threatTier !== "All" && d.threat_tier !== this.currentFilters.threatTier) return false;
      return true;
    });
  }

  detectHoveredDistrict() {
    let hovered = null;
    let minDistance = 16;

    for (const dist of this.filteredDistricts) {
      const pt = this.geoToScreen(dist.latitude, dist.longitude);
      const distPx = Math.hypot(this.mouse.x - pt.x, this.mouse.y - pt.y);
      const r = this.getDistrictRadius(dist);
      if (distPx <= Math.max(r + 6, minDistance)) {
        minDistance = distPx;
        hovered = dist;
      }
    }
    this.hoveredDistrict = hovered;
    this.canvas.style.cursor = hovered ? "pointer" : (this.isDragging ? "grabbing" : "grab");
  }

  getDistrictRadius(dist) {
    const vol = dist.total_volume_cr || 100;
    const baseR = 5 + Math.log10(vol + 1) * 3.5;
    return Math.max(6, Math.min(22, baseR * Math.sqrt(this.scale)));
  }

  selectDistrict(dist) {
    this.selectedDistrict = dist;
    this.updateInspectorCard();
  }

  startAnimationLoop() {
    const loop = () => {
      this.animTime += 0.025;
      this.render();
      this.animationFrameId = requestAnimationFrame(loop);
    };
    loop();
  }

  render() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    // 1. Clear & Background
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#020617";
    ctx.fillRect(0, 0, w, h);

    // 2. Coordinate Grid Lines
    this.renderCoordinateGrid(ctx);

    // 3. Ambient Bangladesh Regional Boundaries
    this.renderCountryOutline(ctx);

    // 4. Cross-District Collusion Tentacle Arcs
    this.renderCollusionArcs(ctx);

    // 5. District Nodes & Threat Glows
    this.renderDistrictNodes(ctx);

    // 6. Selected District Callout Highlight
    if (this.selectedDistrict) {
      this.renderSelectedHighlight(ctx, this.selectedDistrict);
    }

    // 7. Interactive Hover Tooltip
    if (this.hoveredDistrict && this.hoveredDistrict !== this.selectedDistrict) {
      this.renderTooltip(ctx, this.hoveredDistrict);
    }

    // 8. Live Sonar Blip Particles
    this.renderLiveBlips(ctx);
  }

  renderCoordinateGrid(ctx) {
    ctx.save();
    ctx.strokeStyle = "rgba(30, 41, 59, 0.4)";
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 6]);

    for (let lon = 88.5; lon <= 92.5; lon += 1.0) {
      const p1 = this.geoToScreen(26.6, lon);
      const p2 = this.geoToScreen(20.6, lon);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();

      ctx.fillStyle = "rgba(100, 116, 139, 0.4)";
      ctx.font = "9px 'JetBrains Mono', monospace";
      ctx.fillText(`${lon}°E`, p2.x + 2, Math.min(this.height - 10, p2.y));
    }

    for (let lat = 21.0; lat <= 26.0; lat += 1.0) {
      const p1 = this.geoToScreen(lat, 88.2);
      const p2 = this.geoToScreen(lat, 92.6);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();

      ctx.fillStyle = "rgba(100, 116, 139, 0.4)";
      ctx.font = "9px 'JetBrains Mono', monospace";
      ctx.fillText(`${lat}°N`, Math.max(10, p1.x - 30), p1.y - 3);
    }
    ctx.restore();
  }

  renderCountryOutline(ctx) {
    const boundaryCoords = [
      [26.60, 88.50], [26.40, 89.00], [26.00, 89.70], [25.20, 89.80],
      [25.10, 90.50], [25.15, 91.80], [24.80, 92.40], [24.20, 92.10],
      [23.70, 91.30], [23.10, 91.90], [22.40, 92.30], [21.50, 92.20],
      [20.90, 92.35], [21.20, 91.90], [21.80, 91.70], [22.20, 90.80],
      [21.80, 90.20], [21.80, 89.50], [22.30, 89.10], [23.00, 88.90],
      [23.80, 88.70], [24.70, 88.20], [25.30, 88.80], [26.20, 88.50]
    ];

    ctx.save();
    ctx.beginPath();
    boundaryCoords.forEach((pt, idx) => {
      const screenPt = this.geoToScreen(pt[0], pt[1]);
      if (idx === 0) ctx.moveTo(screenPt.x, screenPt.y);
      else ctx.lineTo(screenPt.x, screenPt.y);
    });
    ctx.closePath();

    const grad = ctx.createLinearGradient(0, 0, this.width, this.height);
    grad.addColorStop(0, "rgba(15, 23, 42, 0.7)");
    grad.addColorStop(1, "rgba(2, 6, 23, 0.85)");
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.strokeStyle = "rgba(56, 189, 248, 0.25)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    const seaPt = this.geoToScreen(21.2, 90.5);
    ctx.fillStyle = "rgba(56, 189, 248, 0.2)";
    ctx.font = "italic bold 12px 'Plus Jakarta Sans', sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("BAY OF BENGAL", seaPt.x, seaPt.y);
    ctx.restore();
  }

  renderCollusionArcs(ctx) {
    ctx.save();
    for (const arc of this.collusionArcs) {
      const p1 = this.geoToScreen(arc.source_lat, arc.source_lon);
      const p2 = this.geoToScreen(arc.target_lat, arc.target_lon);

      const midX = (p1.x + p2.x) / 2;
      const midY = (p1.y + p2.y) / 2;
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      const dist = Math.hypot(dx, dy);

      const curveAmount = Math.min(50, dist * 0.2);
      const cpX = midX - (dy / dist) * curveAmount;
      const cpY = midY + (dx / dist) * curveAmount;

      const isHighlight = (this.selectedDistrict && (this.selectedDistrict.district === arc.source_district || this.selectedDistrict.district === arc.target_district));
      const alpha = isHighlight ? 0.85 : 0.35;

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.quadraticCurveTo(cpX, cpY, p2.x, p2.y);

      ctx.strokeStyle = arc.color || "#ef4444";
      ctx.globalAlpha = alpha;
      ctx.lineWidth = isHighlight ? 2.5 : 1.2;
      ctx.setLineDash([4, 4]);
      ctx.stroke();

      const t = (this.animTime * 0.6 + (dist * 0.01)) % 1.0;
      const bx = Math.pow(1 - t, 2) * p1.x + 2 * (1 - t) * t * cpX + Math.pow(t, 2) * p2.x;
      const by = Math.pow(1 - t, 2) * p1.y + 2 * (1 - t) * t * cpY + Math.pow(t, 2) * p2.y;

      ctx.globalAlpha = 0.9;
      ctx.setLineDash([]);
      ctx.beginPath();
      ctx.arc(bx, by, isHighlight ? 3.5 : 2.5, 0, Math.PI * 2);
      ctx.fillStyle = arc.color || "#ef4444";
      ctx.fill();
    }
    ctx.restore();
  }

  renderDistrictNodes(ctx) {
    ctx.save();
    for (const dist of this.filteredDistricts) {
      const pt = this.geoToScreen(dist.latitude, dist.longitude);
      const r = this.getDistrictRadius(dist);
      const color = dist.tier_color || this.tierColors[dist.threat_tier] || "#10b981";
      const isCritical = (dist.threat_tier === "CRITICAL");
      const isHigh = (dist.threat_tier === "HIGH");

      // 1. Pulsing Sonar Ring for Critical / High Cartel Rings
      if (isCritical || isHigh) {
        const pulseMax = isCritical ? 24 : 16;
        const pulse = (this.animTime * 25) % pulseMax;
        const pulseAlpha = Math.max(0, 1 - (pulse / pulseMax)) * (isCritical ? 0.7 : 0.4);

        ctx.beginPath();
        ctx.arc(pt.x, pt.y, r + pulse, 0, Math.PI * 2);
        ctx.strokeStyle = color;
        ctx.globalAlpha = pulseAlpha;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // 2. Radial Heat Glow
      const glowR = r * (isCritical ? 2.2 : 1.6);
      const glowGrad = ctx.createRadialGradient(pt.x, pt.y, r * 0.4, pt.x, pt.y, glowR);
      glowGrad.addColorStop(0, color);
      glowGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.globalAlpha = isCritical ? 0.45 : 0.25;
      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, glowR, 0, Math.PI * 2);
      ctx.fill();

      // 3. Core Marker Circle
      ctx.globalAlpha = 1.0;
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, r, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.lineWidth = 1.8;
      ctx.strokeStyle = "#ffffff";
      ctx.stroke();

      // 4. District Label
      if (this.scale > 1.3 || isCritical || dist === this.hoveredDistrict || dist === this.selectedDistrict) {
        ctx.font = `${Math.min(13, Math.max(9, 10 * Math.sqrt(this.scale)))}px 'Plus Jakarta Sans', sans-serif`;
        ctx.fillStyle = "#f8fafc";
        ctx.textAlign = "center";
        ctx.shadowColor = "#000000";
        ctx.shadowBlur = 4;
        ctx.fillText(dist.district, pt.x, pt.y + r + 11);
        ctx.shadowBlur = 0;
      }
    }
    ctx.restore();
  }

  renderSelectedHighlight(ctx, dist) {
    ctx.save();
    const pt = this.geoToScreen(dist.latitude, dist.longitude);
    const r = this.getDistrictRadius(dist);

    ctx.beginPath();
    ctx.arc(pt.x, pt.y, r + 8, 0, Math.PI * 2);
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 2.5;
    ctx.setLineDash([4, 4]);
    ctx.stroke();

    ctx.setLineDash([]);
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(pt.x - r - 14, pt.y);
    ctx.lineTo(pt.x - r - 6, pt.y);
    ctx.moveTo(pt.x + r + 6, pt.y);
    ctx.lineTo(pt.x + r + 14, pt.y);
    ctx.moveTo(pt.x, pt.y - r - 14);
    ctx.lineTo(pt.x, pt.y - r - 6);
    ctx.moveTo(pt.x, pt.y + r + 6);
    ctx.lineTo(pt.x, pt.y + r + 14);
    ctx.stroke();
    ctx.restore();
  }

  renderTooltip(ctx, dist) {
    ctx.save();
    const pt = this.geoToScreen(dist.latitude, dist.longitude);
    const boxW = 220;
    const boxH = 118;
    let x = pt.x + 16;
    let y = pt.y - 45;

    if (x + boxW > this.width - 10) x = pt.x - boxW - 16;
    if (y < 10) y = 10;
    if (y + boxH > this.height - 10) y = this.height - boxH - 10;

    ctx.fillStyle = "rgba(15, 23, 42, 0.95)";
    ctx.strokeStyle = dist.tier_color || "#38bdf8";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(x, y, boxW, boxH, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 13px 'Plus Jakarta Sans', sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(`${dist.district} (${dist.division})`, x + 12, y + 22);

    ctx.font = "bold 10px 'JetBrains Mono', monospace";
    ctx.fillStyle = dist.tier_color || "#38bdf8";
    ctx.fillText(`TIER: ${dist.threat_tier}`, x + 12, y + 40);

    ctx.strokeStyle = "rgba(51, 65, 85, 0.7)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x + 12, y + 46);
    ctx.lineTo(x + boxW - 12, y + 46);
    ctx.stroke();

    ctx.font = "11px 'Plus Jakarta Sans', sans-serif";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText("Integrity Score:", x + 12, y + 64);
    ctx.fillStyle = dist.integrity_score < 70 ? "#ef4444" : "#10b981";
    ctx.font = "bold 11px 'JetBrains Mono', monospace";
    ctx.fillText(`${dist.integrity_score}/100`, x + 115, y + 64);

    ctx.font = "11px 'Plus Jakarta Sans', sans-serif";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText("Total Packages:", x + 12, y + 82);
    ctx.fillStyle = "#f1f5f9";
    ctx.fillText(`${(dist.total_packages || 0).toLocaleString()} (৳${dist.total_volume_cr || 0} Cr)`, x + 115, y + 82);

    ctx.fillStyle = "#94a3b8";
    ctx.fillText("Collusive Vol:", x + 12, y + 100);
    ctx.fillStyle = dist.collusive_volume_cr > 0 ? "#f87171" : "#10b981";
    ctx.fillText(`৳${dist.collusive_volume_cr || 0} Cr (${dist.collusion_rate_pct || 0}%)`, x + 115, y + 100);

    ctx.restore();
  }

  renderTelemetryHUD() {
    if (!this.telemetry) return;
    const hud = document.getElementById("gisDistrictHud");
    if (!hud) return;

    hud.innerHTML = `
      <div class="hud-stat-item" style="display: flex; align-items: center; gap: 8px;">
        <span class="pulse-dot" style="background: #10b981;"></span>
        <span style="font-size: 0.75rem; color: var(--text-muted);">Monitored: <strong style="color: #f8fafc;">${this.telemetry.total_districts || 64} / 64 Districts</strong></span>
      </div>
      <div class="hud-stat-item" style="display: flex; align-items: center; gap: 8px;">
        <span class="pulse-dot" style="background: #ef4444;"></span>
        <span style="font-size: 0.75rem; color: var(--text-muted);">Critical Rings: <strong style="color: #f87171;">${this.telemetry.critical_threat_districts_count || 14} Districts</strong></span>
      </div>
      <div class="hud-stat-item" style="display: flex; align-items: center; gap: 8px;">
        <span class="pulse-dot" style="background: #38bdf8;"></span>
        <span style="font-size: 0.75rem; color: var(--text-muted);">National Integrity: <strong style="color: #38bdf8;">${this.telemetry.national_integrity_score || 72.7}/100</strong></span>
      </div>
      <div class="hud-stat-item" style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 0.75rem; color: var(--text-muted);">Collusive Vol: <strong style="color: #fbbf24;">৳${(this.telemetry.collusive_volume_cr || 0).toLocaleString()} Cr</strong></span>
      </div>
    `;
  }

  renderLeaderboard() {
    const tableBody = document.getElementById("gisLeaderboardBody");
    if (!tableBody) return;

    const topDistricts = [...this.districts]
      .sort((a, b) => b.threat_score - a.threat_score)
      .slice(0, 10);

    tableBody.innerHTML = topDistricts.map((d, idx) => {
      const synList = (d.active_syndicates && d.active_syndicates.length > 0)
        ? d.active_syndicates.map(s => `<span class="tag-badge" style="font-size: 0.65rem; background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3);">${s}</span>`).join(" ")
        : '<span style="color: #64748b; font-size: 0.72rem;">None Detected</span>';

      return `
        <tr style="border-bottom: 1px solid var(--border-subtle); cursor: pointer;" onclick="window.bangladeshGisHeatmap.focusDistrict('${d.district}')">
          <td style="padding: 0.6rem 0.8rem; font-weight: 700; color: #94a3b8; font-family: monospace;">#${idx + 1}</td>
          <td style="padding: 0.6rem 0.8rem;">
            <div style="font-weight: 700; color: #f8fafc;">${d.district}</div>
            <div style="font-size: 0.7rem; color: #64748b;">${d.division} Division</div>
          </td>
          <td style="padding: 0.6rem 0.8rem;">
            <span class="badge" style="background: ${d.tier_color}22; color: ${d.tier_color}; border: 1px solid ${d.tier_color}55; font-size: 0.7rem; padding: 2px 7px; border-radius: 4px; font-weight: 700;">
              ${d.threat_tier}
            </span>
          </td>
          <td style="padding: 0.6rem 0.8rem; font-family: monospace; font-weight: 700; color: ${d.integrity_score < 70 ? '#f87171' : '#10b981'};">
            ${d.integrity_score}/100
          </td>
          <td style="padding: 0.6rem 0.8rem; font-family: monospace; font-size: 0.78rem;">
            <div>৳${d.total_volume_cr} Cr</div>
            <div style="color: #f87171; font-size: 0.7rem;">Flagged: ৳${d.collusive_volume_cr} Cr (${d.collusion_rate_pct}%)</div>
          </td>
          <td style="padding: 0.6rem 0.8rem;">
            <div style="display: flex; flex-wrap: wrap; gap: 4px;">${synList}</div>
          </td>
          <td style="padding: 0.6rem 0.8rem; text-align: right;">
            <button class="btn-secondary" style="padding: 0.25rem 0.6rem; font-size: 0.7rem;" onclick="event.stopPropagation(); window.bangladeshGisHeatmap.focusDistrict('${d.district}')">
              Target 🎯
            </button>
          </td>
        </tr>
      `;
    }).join("");
  }

  updateInspectorCard() {
    const card = document.getElementById("gisDistrictInspector");
    if (!card) return;

    if (!this.selectedDistrict) {
      card.style.display = "none";
      return;
    }

    const d = this.selectedDistrict;
    card.style.display = "block";
    card.innerHTML = `
      <div style="background: #0b1329; border: 1px solid ${d.tier_color || '#38bdf8'}; border-radius: 10px; padding: 1rem; margin-top: 1rem; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 0.6rem; margin-bottom: 0.8rem;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.2rem;">📍</span>
            <div>
              <h4 style="margin: 0; color: #f8fafc; font-size: 1rem;">District Dossier: ${d.district}</h4>
              <span style="font-size: 0.72rem; color: #94a3b8;">${d.division} Division &bull; GPS: [${d.latitude.toFixed(4)}°N, ${d.longitude.toFixed(4)}°E]</span>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="badge" style="background: ${d.tier_color}22; color: ${d.tier_color}; border: 1px solid ${d.tier_color}55; font-size: 0.75rem; padding: 3px 8px; border-radius: 4px; font-weight: 800;">
              ${d.threat_tier} THREAT TIER
            </span>
            <button class="btn-secondary" onclick="window.bangladeshGisHeatmap.resetView()" style="padding: 0.2rem 0.5rem; font-size: 0.7rem;">&times; Close</button>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.8rem; margin-bottom: 0.8rem;">
          <div style="background: #020617; padding: 0.6rem; border-radius: 6px; border: 1px solid #1e293b;">
            <div style="font-size: 0.7rem; color: #94a3b8;">Procurement Integrity</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: ${d.integrity_score < 70 ? '#f87171' : '#10b981'}; font-family: monospace;">${d.integrity_score} / 100</div>
          </div>
          <div style="background: #020617; padding: 0.6rem; border-radius: 6px; border: 1px solid #1e293b;">
            <div style="font-size: 0.7rem; color: #94a3b8;">Total Awarded Volume</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #38bdf8; font-family: monospace;">৳${d.total_volume_cr} Cr</div>
          </div>
          <div style="background: #020617; padding: 0.6rem; border-radius: 6px; border: 1px solid #1e293b;">
            <div style="font-size: 0.7rem; color: #94a3b8;">Collusive Exposure</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #f87171; font-family: monospace;">৳${d.collusive_volume_cr} Cr (${d.collusion_rate_pct}%)</div>
          </div>
          <div style="background: #020617; padding: 0.6rem; border-radius: 6px; border: 1px solid #1e293b;">
            <div style="font-size: 0.7rem; color: #94a3b8;">Primary Vector</div>
            <div style="font-size: 0.85rem; font-weight: 800; color: #fbbf24; font-family: monospace; margin-top: 4px;">${d.primary_vector || 'NONE'}</div>
          </div>
        </div>

        <div style="font-size: 0.76rem; color: #94a3b8;">
          <strong>Active Syndicate Rings in ${d.district}:</strong>
          ${d.active_syndicates && d.active_syndicates.length > 0
            ? `<div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">${d.active_syndicates.map(s => `<span class="tag-badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef444455; padding: 2px 6px; border-radius: 4px;">${s}</span>`).join('')}</div>`
            : '<span style="color: #10b981; margin-left: 6px;">✓ No organized syndicates detected under CPTU Rule 127.</span>'
          }
        </div>
      </div>
    `;
  }

  setFilter(filterName, value) {
    this.currentFilters[filterName] = value;
    this.loadHeatmapData();
  }

  connectLiveStream() {
    if (!this.liveEnabled || this._wsRetries >= this._wsMaxRetries) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const token = window.localStorage?.getItem("tenderpulse_access_token");
    const authQuery = token ? `?access_token=${encodeURIComponent(token)}` : "";
    const url = `${proto}://${window.location.host}/api/ws/cartel/live${authQuery}`;
    try {
      this.ws = new WebSocket(url);
    } catch (e) {
      this._scheduleWsReconnect();
      return;
    }

    this.ws.onopen = () => {
      this._wsRetries = 0;
      this._wsReconnectDelay = 2000;
      this._updateTickerBadge(true);
      console.log("[GisLive] WebSocket connected to live tender stream.");
    };

    this.ws.onmessage = (ev) => {
      try {
        const event = JSON.parse(ev.data);
        this.onLiveEvent(event);
      } catch (_) {}
    };

    this.ws.onclose = () => {
      this._updateTickerBadge(false);
      this._scheduleWsReconnect();
    };

    this.ws.onerror = () => {
      this._updateTickerBadge(false);
    };
  }

  _scheduleWsReconnect() {
    if (!this.liveEnabled || this._wsRetries >= this._wsMaxRetries) return;
    this._wsRetries++;
    this._wsReconnectDelay = Math.min(30000, this._wsReconnectDelay * 1.5);
    setTimeout(() => this.connectLiveStream(), this._wsReconnectDelay);
  }

  onLiveEvent(event) {
    if (event.event_type === "STREAM_CONNECTED" || event.event_type === "PONG") return;

    const lat = event.latitude;
    const lon = event.longitude;
    if (!lat || !lon) return;

    this.liveTotalEvents++;
    if (event.is_collusive) this.liveCollusiveCount++;

    // Spawn blip particle
    this.spawnBlip(lat, lon, event);

    // Update district data in-memory for live counts
    const dist = this.districts.find(d => d.district === event.district);
    if (dist) {
      dist.total_packages = (dist.total_packages || 0) + 1;
      dist.total_volume_cr = (dist.total_volume_cr || 0) + (event.estimated_cost_cr || 0);
      if (event.is_collusive) {
        dist.collusive_packages = (dist.collusive_packages || 0) + 1;
        dist.collusive_volume_cr = (dist.collusive_volume_cr || 0) + (event.estimated_cost_cr || 0);
      }
    }

    // Spawn partner arc flares
    if (event.is_collusive && event.partner_districts && event.partner_districts.length) {
      event.partner_districts.forEach(partnerName => {
        const partner = this.districts.find(d => d.district === partnerName);
        if (partner) {
          this.spawnArcFlare(lat, lon, partner.latitude, partner.longitude, event);
        }
      });
    }

    // Push to ticker
    this.liveTickerEvents.unshift(event);
    if (this.liveTickerEvents.length > 4) this.liveTickerEvents.pop();
    this.renderLiveTickerEvents();

    // Audio ping
    if (!this._audioMuted) this._pingSound(event.is_collusive);
  }

  spawnBlip(lat, lon, event) {
    const color = this.tierColors[event.threat_tier] || "#94a3b8";
    this.activeBlips.push({
      lat, lon,
      maxRadius: event.threat_tier === "CRITICAL" ? 80 : event.threat_tier === "HIGH" ? 60 : 40,
      currentRadius: 4,
      alpha: 1.0,
      color,
      isCollusive: event.is_collusive,
      label: event.district,
      eventType: event.event_type,
    });
    // Cap particle count
    if (this.activeBlips.length > 30) this.activeBlips.shift();
  }

  _arcFlares = [];

  spawnArcFlare(lat1, lon1, lat2, lon2, event) {
    const color = this.tierColors[event.threat_tier] || "#f97316";
    this._arcFlares.push({
      lat1, lon1, lat2, lon2,
      color,
      progress: 0,
      alpha: 1.0,
    });
    if (this._arcFlares.length > 12) this._arcFlares.shift();
  }

  renderLiveBlips(ctx) {
    const dt = 0.028;  // tick advance per frame

    // Render & age arc flares
    this._arcFlares = this._arcFlares.filter(f => f.alpha > 0.01);
    for (const f of this._arcFlares) {
      const p1 = this.geoToScreen(f.lat1, f.lon1);
      const p2 = this.geoToScreen(f.lat2, f.lon2);
      const cpx = (p1.x + p2.x) / 2;
      const cpy = Math.min(p1.y, p2.y) - 40;

      // Animated photon along arc
      const t = f.progress;
      const px = (1-t)*(1-t)*p1.x + 2*(1-t)*t*cpx + t*t*p2.x;
      const py = (1-t)*(1-t)*p1.y + 2*(1-t)*t*cpy + t*t*p2.y;

      ctx.save();
      ctx.globalAlpha = f.alpha;
      // Arc line
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.quadraticCurveTo(cpx, cpy, p2.x, p2.y);
      ctx.strokeStyle = f.color;
      ctx.lineWidth = 1.2;
      ctx.shadowColor = f.color;
      ctx.shadowBlur = 6;
      ctx.setLineDash([4, 6]);
      ctx.stroke();
      // Photon particle
      ctx.beginPath();
      ctx.arc(px, py, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "#fff";
      ctx.shadowColor = f.color;
      ctx.shadowBlur = 12;
      ctx.fill();
      ctx.restore();

      f.progress = Math.min(1, f.progress + dt * 1.2);
      if (f.progress >= 1) f.alpha -= 0.04;
    }

    // Render & age sonar blip rings
    this.activeBlips = this.activeBlips.filter(b => b.alpha > 0.02);
    for (const blip of this.activeBlips) {
      const pt = this.geoToScreen(blip.lat, blip.lon);
      ctx.save();

      // Three concentric expanding rings
      for (let ring = 0; ring < 3; ring++) {
        const ringR = blip.currentRadius * (1 - ring * 0.25);
        if (ringR <= 0) continue;
        const ringAlpha = blip.alpha * (1 - ring * 0.3);
        ctx.globalAlpha = ringAlpha;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, ringR, 0, Math.PI * 2);
        ctx.strokeStyle = blip.color;
        ctx.lineWidth = 1.5 - ring * 0.4;
        ctx.shadowColor = blip.color;
        ctx.shadowBlur = 8;
        ctx.stroke();
      }

      // Injected award: extra solid fill flash
      if (blip.eventType === "INJECTED_AWARD") {
        ctx.globalAlpha = blip.alpha * 0.25;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, blip.currentRadius * 0.5, 0, Math.PI * 2);
        ctx.fillStyle = blip.color;
        ctx.fill();
      }

      ctx.restore();

      // Advance
      blip.currentRadius = Math.min(blip.maxRadius, blip.currentRadius + dt * blip.maxRadius * 0.7);
      if (blip.currentRadius >= blip.maxRadius * 0.7) {
        blip.alpha -= dt * 0.8;
      }
    }
  }

  // ──────────────────────────────────────────────
  // Live Ticker HUD
  // ──────────────────────────────────────────────
  buildLiveTicker() {
    const container = document.getElementById("gisDistrictMapContainer");
    if (!container || document.getElementById("gisLiveTicker")) return;

    const ticker = document.createElement("div");
    ticker.id = "gisLiveTicker";
    ticker.style.cssText = [
      "position:relative", "width:100%", "background:rgba(2,6,23,0.85)",
      "border-bottom:1px solid rgba(239,68,68,0.25)",
      "padding:6px 14px", "display:flex", "align-items:center", "gap:12px",
      "font-family:'JetBrains Mono',monospace", "font-size:11px", "z-index:10",
      "flex-wrap:wrap",
    ].join(";");

    ticker.innerHTML = `
      <span id="gisLiveBadge" style="display:inline-flex;align-items:center;gap:5px;color:#ef4444;font-weight:700;">
        <span id="gisLiveDot" style="width:7px;height:7px;border-radius:50%;background:#ef4444;animation:gisLivePulse 1s infinite;"></span>
        <span id="gisLiveBadgeText">🔴 CONNECTING…</span>
      </span>
      <span id="gisLiveStats" style="color:#64748b;">— events</span>
      <span style="flex:1;"></span>
      <button id="gisLiveToggleBtn" style="background:rgba(30,41,59,0.8);border:1px solid rgba(100,116,139,0.4);color:#94a3b8;padding:3px 10px;border-radius:4px;cursor:pointer;font-size:10px;font-family:inherit;">⏸ Pause</button>
      <button id="gisLiveInjectBtn" style="background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.5);color:#f87171;padding:3px 10px;border-radius:4px;cursor:pointer;font-size:10px;font-family:inherit;">⚡ Inject Anomaly</button>
      <button id="gisLiveAudioBtn" style="background:rgba(30,41,59,0.8);border:1px solid rgba(100,116,139,0.4);color:#64748b;padding:3px 10px;border-radius:4px;cursor:pointer;font-size:10px;font-family:inherit;">🔇 Audio</button>
    `;

    // Inject CSS keyframe for badge pulse
    if (!document.getElementById("gisLiveStyles")) {
      const style = document.createElement("style");
      style.id = "gisLiveStyles";
      style.textContent = `
        @keyframes gisLivePulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(1.6)} }
        .gis-live-pill { display:inline-flex;align-items:center;gap:5px;padding:2px 8px;border-radius:12px;font-size:10px; }
        .gis-live-pill-clean { background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.35);color:#10b981; }
        .gis-live-pill-alert { background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.4);color:#f87171; }
        .gis-live-pill-elevated { background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.35);color:#f59e0b; }
      `;
      document.head.appendChild(style);
    }

    // Insert before canvas
    const canvas = container.querySelector(`#${this.canvasId}`);
    if (canvas) {
      container.insertBefore(ticker, canvas);
    } else {
      container.prepend(ticker);
    }

    // Event row container below ticker
    const evRow = document.createElement("div");
    evRow.id = "gisLiveEventRow";
    evRow.style.cssText = [
      "display:flex", "gap:6px", "padding:4px 14px", "overflow:hidden",
      "background:rgba(2,6,23,0.7)", "min-height:28px", "align-items:center",
      "font-family:'JetBrains Mono',monospace", "font-size:10px", "flex-wrap:wrap",
    ].join(";");
    evRow.innerHTML = `<span style="color:#334155;">Awaiting live e-GP tender stream…</span>`;
    if (canvas) container.insertBefore(evRow, canvas); else container.prepend(evRow);

    // Wire buttons
    document.getElementById("gisLiveToggleBtn").addEventListener("click", () => this._toggleStream());
    document.getElementById("gisLiveInjectBtn").addEventListener("click", () => this._injectAnomaly());
    document.getElementById("gisLiveAudioBtn").addEventListener("click", () => this._toggleAudio());
  }

  _updateTickerBadge(connected) {
    const badge = document.getElementById("gisLiveBadgeText");
    const dot = document.getElementById("gisLiveDot");
    if (badge) badge.textContent = connected ? "🔴 LIVE RADAR" : "⚫ RECONNECTING…";
    if (dot) dot.style.background = connected ? "#ef4444" : "#475569";
  }

  renderLiveTickerEvents() {
    const row = document.getElementById("gisLiveEventRow");
    const stats = document.getElementById("gisLiveStats");
    if (!row) return;
    if (stats) stats.textContent = `${this.liveTotalEvents} events | ${this.liveCollusiveCount} collusion flags`;

    const pills = this.liveTickerEvents.map(ev => {
      const tierKey = ev.threat_tier || "CLEAN";
      const cls = tierKey === "CRITICAL" || tierKey === "HIGH"
        ? "gis-live-pill-alert"
        : tierKey === "ELEVATED" ? "gis-live-pill-elevated" : "gis-live-pill-clean";
      const icon = ev.is_collusive ? "🚨" : "✅";
      const syn = ev.syndicate ? `·${ev.syndicate.split(" ")[0]}` : "";
      return `<span class="gis-live-pill ${cls}">${icon} ${ev.district} [${ev.agency}] ৳${ev.estimated_cost_cr}Cr${syn}</span>`;
    }).join("");
    row.innerHTML = pills || `<span style="color:#334155;">Awaiting live e-GP tender stream…</span>`;
  }

  async _toggleStream() {
    try {
      const token = window.localStorage?.getItem("tenderpulse_access_token");
      if (!token) return;
      const res = await fetch("/api/cartel/live/toggle", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      const btn = document.getElementById("gisLiveToggleBtn");
      if (btn) btn.textContent = data.stream_state === "PAUSED" ? "▶ Resume" : "⏸ Pause";
    } catch (_) {}
  }

  async _injectAnomaly() {
    try {
      const token = window.localStorage?.getItem("tenderpulse_access_token");
      if (!token) return;
      // High-threat Dhaka cartel injection
      await fetch("/api/cartel/live/inject", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          district: "Dhaka", division: "Dhaka", agency: "RHD",
          estimated_cost_cr: 98.5, work_type: "Road Pavement & Embankment",
          latitude: 23.8103, longitude: 90.4125
        })
      });
    } catch (_) {}
  }

  _toggleAudio() {
    this._audioMuted = !this._audioMuted;
    const btn = document.getElementById("gisLiveAudioBtn");
    if (btn) btn.textContent = this._audioMuted ? "🔇 Audio" : "🔊 Audio";
    if (!this._audioMuted && !this._audioCtx) {
      try { this._audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch (_) {}
    }
  }

  _pingSound(isCollusive) {
    try {
      if (!this._audioCtx) return;
      const osc = this._audioCtx.createOscillator();
      const gain = this._audioCtx.createGain();
      osc.connect(gain);
      gain.connect(this._audioCtx.destination);
      osc.frequency.value = isCollusive ? 330 : 880;
      osc.type = isCollusive ? "sawtooth" : "sine";
      gain.gain.setValueAtTime(0.08, this._audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this._audioCtx.currentTime + 0.35);
      osc.start(this._audioCtx.currentTime);
      osc.stop(this._audioCtx.currentTime + 0.35);
    } catch (_) {}
  }
}

// Global Singleton
window.bangladeshGisHeatmap = new BangladeshGisHeatmap();

window.initBangladeshGisHeatmap = function() {
  if (window.bangladeshGisHeatmap) {
    window.bangladeshGisHeatmap.init();
  }
};

// ---------------------------------------------------------------------------
// Viewport Switcher (external API)
// ---------------------------------------------------------------------------
window.switchCartelViewport = function (mode) {
  const topo = document.getElementById("gatCartelRadarContainer");
  const gis = document.getElementById("gisDistrictMapContainer");
  const btnTopo = document.getElementById("btnViewGatTopology");
  const btnGis = document.getElementById("btnViewGisHeatmap");

  if (mode === "gis") {
    if (topo) topo.style.display = "none";
    if (gis) {
      gis.style.display = "block";
      if (window.bangladeshGisHeatmap) {
        if (!window.bangladeshGisHeatmap.canvas) {
          window.bangladeshGisHeatmap.init();
        } else {
          window.bangladeshGisHeatmap.resize();
          window.bangladeshGisHeatmap.loadHeatmapData();
        }
      }
    }
    if (btnTopo) {
      btnTopo.className = "btn-secondary";
      btnTopo.style.borderColor = "rgba(239, 68, 68, 0.4)";
      btnTopo.style.color = "#f87171";
    }
    if (btnGis) {
      btnGis.className = "btn-primary";
      btnGis.style.borderColor = "";
      btnGis.style.color = "";
    }
  } else {
    if (topo) topo.style.display = "block";
    if (gis) gis.style.display = "none";
    if (btnTopo) {
      btnTopo.className = "btn-primary";
      btnTopo.style.borderColor = "";
      btnTopo.style.color = "";
    }
    if (btnGis) {
      btnGis.className = "btn-secondary";
      btnGis.style.borderColor = "rgba(56, 189, 248, 0.4)";
      btnGis.style.color = "#38bdf8";
    }
  }
};

// Auto-initialize when DOM is ready
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    // If user switches to awards-view, canvas will initialize on view
  });
}
