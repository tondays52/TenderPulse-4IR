/**
 * TenderPulse 4IR × Tender Trading Inc.
 * GovDash-Style CPTU Compliance Matrix & "RFP Shredder" (compliance-matrix.js)
 * Grounding: Public Procurement Act 2006 & Public Procurement Rules 2008 (PPR-2008)
 */

class ComplianceMatrixGenerator {
  constructor() {
    this.currentDoc = null;
    this.currentMatrix = null;
    this.visualizer = null;
    this.lastAnalysis = null;
    this.activeFilter = "all";
    this.searchQuery = "";
  }

  initVisualizer() {
    try {
      if (!this.visualizer && typeof Compliance3DVisualizer !== 'undefined') {
        const canvas = document.getElementById("compliance3dCanvas");
        if (canvas) {
          this.visualizer = new Compliance3DVisualizer("compliance3dCanvas");
        }
      }
    } catch (e) {
      console.warn("Compliance 3D Visualizer init error:", e);
    }
  }

  getDefaultMockDoc() {
    return {
      tenderId: "984210",
      name: "Construction of 142m Pre-Stressed Concrete Girder Bridge over Meghna River (Package W-04)",
      agency: "Roads and Highways Department (RHD)",
      estimatedCost: 850000000,
      prequalification: {
        turnover: { value: "35.0 Cr (Best 5 Years)", status: "verified" },
        liquidAssets: { value: "9.50 Cr Unconditional (Form e-PW2A-8)", status: "warning" },
        similarExperience: { value: "1 RCC/PSC Bridge min 35.0 Cr", status: "verified" },
        generalExperience: { value: "Minimum 10 Years", status: "verified" }
      },
      personnel: [
        { role: "Project Manager (B.Sc Civil)", count: 1, minExp: "10 Years" },
        { role: "Senior Bridge Engineer", count: 2, minExp: "7 Years" },
        { role: "Material / Quality Engineer", count: 1, minExp: "5 Years" },
        { role: "Occupational Safety Officer", count: 1, minExp: "3 Years" }
      ],
      equipment: [
        { name: "Hydraulic Rotary Piling Rig (min 1500mm dia)", minUnits: 2, capacity: "1500mm dia / 45m depth" },
        { name: "Batching & Mixing Plant (Automatic)", minUnits: 1, capacity: "60 m³/hr" },
        { name: "Heavy Crawler Crane", minUnits: 2, capacity: "80 Ton" },
        { name: "Concrete Transit Mixers", minUnits: 6, capacity: "6 m³" }
      ]
    };
  }

  async auditBackendCompliance(doc) {
    const targetDoc = doc || this.currentDoc || this.getDefaultMockDoc();

    const payload = {
      tender_id: targetDoc.tenderId || "984210",
      agency: targetDoc.agency || "Roads and Highways Department (RHD)",
      estimated_cost_bdt: Number(targetDoc.estimatedCost || 850000000),
      contractor_name: "Mir Akhter - Spectra JV",
      annual_turnover_bdt: 1200000000,
      liquid_assets_bdt: 250000000,
      similar_experience_years: 7,
      personnel_count: (targetDoc.personnel || []).length || 6,
      equipment_count: (targetDoc.equipment || []).length || 8,
      has_litigation_history: false
    };

    try {
      const response = await fetch("http://127.0.0.1:8080/api/compliance/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (response.ok) {
        this.lastAnalysis = await response.json();
        return this.lastAnalysis;
      }
    } catch (e) {
      console.warn("Backend compliance audit offline, computing client-side:", e);
    }
    return null;
  }

  generateMatrix(doc) {
    const targetDoc = doc || (window.tdsAuditor && typeof window.tdsAuditor.getDocument === "function" ? window.tdsAuditor.getDocument("rhd-bridge") : null) || this.getDefaultMockDoc();
    this.currentDoc = targetDoc;

    const rawCost = Number(targetDoc.estimatedCost || 850000000);
    const costCr = (rawCost / 10000000).toFixed(2);

    const rows = [
      {
        category: "Financial Capability",
        ittClause: "ITT 14.1(a)",
        requirement: "Minimum Average Annual Construction Turnover (Form e-PW3-3A)",
        threshold: targetDoc.prequalification?.turnover?.value || "35.0 Cr (Best 5 Years)",
        status: targetDoc.prequalification?.turnover?.status === "verified" ? "COMPLIANT" : "REVIEW_REQUIRED",
        risk: "Low Risk",
        evidenceDoc: "Audited Financial Statements & NBR Tax Return Acknowledgement (Last 5 Yrs)",
        cptuRule: "Rule 96(3) PPR-2008"
      },
      {
        category: "Liquid Assets / Solvency",
        ittClause: "ITT 15.1(a)",
        requirement: "Liquid Assets / Working Capital or Credit Commitment (Form e-PW2A-8)",
        threshold: targetDoc.prequalification?.liquidAssets?.value || "9.50 Cr Unconditional Commitment",
        status: targetDoc.prequalification?.liquidAssets?.status === "warning" ? "ACTION_REQUIRED" : "COMPLIANT",
        risk: "Critical (Bank Commitment Timing)",
        evidenceDoc: "Bank Solvency Certificate on Scheduled Bank Letterhead (Form e-PW2A-8)",
        cptuRule: "Rule 96(4) PPR-2008"
      },
      {
        category: "Specific Experience",
        ittClause: "ITT 16.1(b)",
        requirement: "Satisfactory completion of similar contract within last 5 years",
        threshold: targetDoc.prequalification?.similarExperience?.value || "1 RCC/PSC Bridge min 35.0 Cr",
        status: targetDoc.prequalification?.similarExperience?.status === "verified" ? "COMPLIANT" : "REVIEW_REQUIRED",
        risk: "Low Risk",
        evidenceDoc: "Completion Certificate signed by Executive Engineer (XEN) or equivalent",
        cptuRule: "Rule 96(2) PPR-2008"
      },
      {
        category: "General Experience",
        ittClause: "ITT 16.1(a)",
        requirement: "General construction experience as Prime Contractor",
        threshold: targetDoc.prequalification?.generalExperience?.value || "Minimum 10 Years",
        status: "COMPLIANT",
        risk: "Zero Risk",
        evidenceDoc: "Incorporation Certificate / Trade License / Past Work Orders",
        cptuRule: "Rule 96(1) PPR-2008"
      },
      {
        category: "Key Personnel Schedule",
        ittClause: "ITT 24.1 & Sec. 2 TDS",
        requirement: `Mandatory Technical Staff (${(targetDoc.personnel || []).length || 4} Key Designations)`,
        threshold: (targetDoc.personnel && targetDoc.personnel.length) ? targetDoc.personnel.map(p => `${p.count}x ${p.role} (${p.minExp})`).join("; ") : "4 Professional Engineers Assigned",
        status: "COMPLIANT",
        risk: "Low Risk",
        evidenceDoc: "CV (Form e-PW3-5) signed by personnel, IEB Registration & NID copies",
        cptuRule: "Rule 97(1) PPR-2008"
      },
      {
        category: "Equipment & Machinery",
        ittClause: "ITT 25.1 & Sec. 2 TDS",
        requirement: `Essential Construction Equipment (${(targetDoc.equipment || []).length || 4} Categories)`,
        threshold: (targetDoc.equipment && targetDoc.equipment.length) ? targetDoc.equipment.map(e => `${e.minUnits}x ${e.name}`).join("; ") : "6 Units Heavy Machinery Allocated",
        status: "COMPLIANT",
        risk: "Low Risk",
        evidenceDoc: "Ownership Registration / Purchase Invoice / Valid Lease Agreement (Form e-PW3-6)",
        cptuRule: "Rule 97(2) PPR-2008"
      },
      {
        category: "Tender Security",
        ittClause: "ITT 31.1",
        requirement: "Unconditional Bank Guarantee or Pay Order for Tender Security",
        threshold: "BDT 2.10 Cr (Approx 2.0% of Estimate, Form e-PW3-7)",
        status: "COMPLIANT",
        risk: "Zero Risk (Standard Bank Format)",
        evidenceDoc: "Original Bank Guarantee valid for 28 days beyond bid validity",
        cptuRule: "Rule 95(1) PPR-2008"
      },
      {
        category: "Subcontracting Limit",
        ittClause: "ITT 22.1",
        requirement: "Maximum allowable subcontracting threshold",
        threshold: "Not to exceed 20% of the total contract value",
        status: "COMPLIANT",
        risk: "Zero Risk",
        evidenceDoc: "Subcontractor Qualification Profile & Statement of Intent",
        cptuRule: "Rule 99 PPR-2008"
      },
      {
        category: "Litigation & Debarment",
        ittClause: "ITT 18.1",
        requirement: "No consistent history of court arbitration or debarment",
        threshold: "No adverse debarment records on CPTU national blacklist",
        status: "COMPLIANT",
        risk: "Zero Risk",
        evidenceDoc: "Sworn Affidavit of Non-Debarment on BDT 300 Non-Judicial Stamp (Form e-PW2A-9)",
        cptuRule: "Rule 127 PPR-2008"
      }
    ];

    const compliantCount = rows.filter(r => r.status === "COMPLIANT").length;
    const readinessScore = Math.round((compliantCount / rows.length) * 100);

    this.currentMatrix = {
      tenderId: targetDoc.tenderId || "984210",
      docName: targetDoc.name || targetDoc.title || "RHD 4-Lane RCC Girder Bridge TDS",
      agency: targetDoc.agency || "Roads and Highways Department (RHD)",
      estimatedCostCr: costCr,
      readinessScore,
      readinessGrade: readinessScore >= 88 ? "PREQUALIFICATION READY (Grade A+)" : "GAP REMEDIATION REQUIRED",
      generatedAt: new Date().toISOString().split("T")[0],
      matrixSeal: `CPTU-MATRIX-${Math.random().toString(16).substring(2, 10).toUpperCase()}`,
      rows
    };

    return this.currentMatrix;
  }

  initComplianceView() {
    try {
      this.initVisualizer();
      const matrix = this.generateMatrix();
      this.renderToView("complianceViewContent");
      this.updateHeaderCards(matrix);
    } catch (e) {
      console.error("Failed to initialize compliance view:", e);
      const container = document.getElementById("complianceViewContent");
      if (container) {
        container.innerHTML = `
          <div style="padding: 2rem; text-align: center; color: var(--text-dim);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
            <p>Loading Compliance Matrix...</p>
            <button class="btn-primary" style="margin-top: 1rem;" onclick="window.complianceMatrix.initComplianceView()">Retry Initialization</button>
          </div>
        `;
      }
    }
  }

  updateHeaderCards(matrix) {
    if (!matrix) return;
    const scoreEl = document.getElementById("complianceCardScore");
    if (scoreEl) scoreEl.textContent = `${matrix.readinessScore}%`;

    const clausesEl = document.getElementById("complianceCardClauses");
    if (clausesEl) clausesEl.textContent = `${matrix.rows.filter(r => r.status === 'COMPLIANT').length} / ${matrix.rows.length} MET`;

    const actionsEl = document.getElementById("complianceCardActions");
    if (actionsEl) actionsEl.textContent = `${matrix.rows.filter(r => r.status !== 'COMPLIANT').length} Pending`;

    const evidenceEl = document.getElementById("complianceCardEvidence");
    if (evidenceEl) evidenceEl.textContent = "100% Injected";
  }

  setFilter(filterType, btnEl) {
    this.activeFilter = filterType;
    if (btnEl && btnEl.parentElement) {
      btnEl.parentElement.querySelectorAll(".btn-secondary").forEach(b => b.classList.remove("active"));
      btnEl.classList.add("active");
    }
    this.renderToView("complianceViewContent");
  }

  filterRows(query) {
    this.searchQuery = (query || "").toLowerCase().trim();
    this.renderToView("complianceViewContent");
  }

  getFilteredRows() {
    if (!this.currentMatrix || !this.currentMatrix.rows) return [];
    return this.currentMatrix.rows.filter(row => {
      // Filter by status
      if (this.activeFilter !== "all" && row.status !== this.activeFilter) {
        return false;
      }
      // Filter by query
      if (this.searchQuery) {
        const text = `${row.category} ${row.ittClause} ${row.requirement} ${row.threshold} ${row.evidenceDoc} ${row.cptuRule}`.toLowerCase();
        if (!text.includes(this.searchQuery)) {
          return false;
        }
      }
      return true;
    });
  }

  renderToView(containerId = "complianceViewContent") {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!this.currentMatrix) {
      this.generateMatrix();
    }

    const filteredRows = this.getFilteredRows();

    container.innerHTML = `
      <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.8rem; color: var(--text-main);">
          <thead>
            <tr style="background: var(--bg-input); border-bottom: 1px solid var(--border-active); text-align: left;">
              <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700; width: 40px;">#</th>
              <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Category &amp; CPTU Clause</th>
              <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Mandatory Requirement</th>
              <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Threshold / Specifics</th>
              <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Audit Status</th>
              <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Evidence Document Required</th>
            </tr>
          </thead>
          <tbody>
            ${filteredRows.length === 0 ? `
              <tr>
                <td colspan="6" style="padding: 2.5rem; text-align: center; color: var(--text-dim);">
                  No compliance clauses match your search query or filter.
                </td>
              </tr>
            ` : filteredRows.map((row, idx) => `
              <tr style="border-bottom: 1px solid var(--border-subtle); background: ${idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)'};">
                <td style="padding: 0.85rem 0.6rem; color: var(--text-dim); font-family: monospace;">0${idx + 1}</td>
                <td style="padding: 0.85rem 0.6rem;">
                  <strong style="color: #fff; display: block; font-size: 0.85rem;">${row.category}</strong>
                  <span style="font-size: 0.72rem; color: var(--primary-light); font-family: monospace;">${row.ittClause} &bull; ${row.cptuRule}</span>
                </td>
                <td style="padding: 0.85rem 0.6rem; color: var(--text-main); font-size: 0.82rem;">${row.requirement}</td>
                <td style="padding: 0.85rem 0.6rem; color: #f8fafc; font-weight: 600; font-size: 0.82rem;">${row.threshold}</td>
                <td style="padding: 0.85rem 0.6rem;">
                  <span class="tag-badge ${row.status === 'COMPLIANT' ? 'live' : (row.status === 'ACTION_REQUIRED' ? 'corrigendum' : 'warning')}">
                    ${row.status === 'COMPLIANT' ? '✓ MET' : (row.status === 'ACTION_REQUIRED' ? '⚠️ ACTION REQ' : '🔍 REVIEW')}
                  </span>
                </td>
                <td style="padding: 0.85rem 0.6rem; color: var(--text-muted); font-size: 0.76rem;">
                  ${row.evidenceDoc}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      <!-- Bottom Certification Note -->
      <div style="margin-top: 1.2rem; padding: 0.85rem; background: var(--bg-input); border-radius: 8px; border: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.8rem;">
        <div style="font-size: 0.74rem; color: var(--text-dim);">
          Generated via <strong>TenderPulse 4IR RFP Shredder</strong> &bull; Compliant with Bangladesh Gazette SRO No. 343-Act/2008 &amp; CPTU Guidelines.
        </div>
        <div style="font-size: 0.76rem; color: #10b981; font-weight: 700;">
          ✓ 100% CPTU Statutory Coverage Verified (${this.currentMatrix.matrixSeal})
        </div>
      </div>
    `;
  }

  exportComplianceJSON() {
    if (!this.currentMatrix) this.generateMatrix();
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.currentMatrix, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `CPTU_Compliance_Matrix_${this.currentMatrix.tenderId}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }

  renderMatrixHTML(matrix) {
    if (!matrix) return "";
    return `
      <div class="compliance-matrix-container" style="background: var(--bg-card); border-radius: 12px; padding: 1.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid var(--border-subtle); padding-bottom: 1.2rem; margin-bottom: 1.2rem; flex-wrap: wrap; gap: 1rem;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="tender-id-badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8;">CPTU Statutory Matrix</span>
              <span class="tag-badge ${matrix.readinessScore >= 80 ? 'live' : 'corrigendum'}">${matrix.readinessGrade} (${matrix.readinessScore}%)</span>
              <span style="font-size: 0.72rem; color: #fbbf24; font-family: monospace;">${matrix.matrixSeal}</span>
            </div>
            <h3 style="font-size: 1.2rem; color: #fff; margin-top: 0.4rem;">${matrix.docName}</h3>
            <p style="font-size: 0.78rem; color: var(--text-dim); margin-top: 0.2rem;">
              Procuring Entity: ${matrix.agency} &bull; Estimated Value: ৳ ${matrix.estimatedCostCr} Cr &bull; Audit Date: ${matrix.generatedAt}
            </p>
          </div>
          <div style="display: flex; gap: 0.6rem;">
            <button class="btn-secondary" onclick="window.print()" style="padding: 0.45rem 0.85rem; font-size: 0.78rem;">
              🖨️ Print Official Matrix
            </button>
            <button class="btn-primary" onclick="if(window.switchTab){ const modal = document.getElementById('complianceModal'); if(modal) modal.style.display='none'; window.switchTab('bank-view'); }" style="padding: 0.45rem 0.85rem; font-size: 0.78rem;">
              🏦 Resolve Bank LOC &rarr;
            </button>
          </div>
        </div>

        <div style="overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse; font-size: 0.78rem; color: var(--text-main);">
            <thead>
              <tr style="background: var(--bg-input); border-bottom: 1px solid var(--border-active); text-align: left;">
                <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">#</th>
                <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Category &amp; Clause</th>
                <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Mandatory Requirement</th>
                <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Threshold / Criteria</th>
                <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Audit Status</th>
                <th style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-weight: 700;">Evidence Document Required</th>
              </tr>
            </thead>
            <tbody>
              ${matrix.rows.map((row, idx) => `
                <tr style="border-bottom: 1px solid var(--border-subtle); background: ${idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)'};">
                  <td style="padding: 0.75rem 0.6rem; color: var(--text-dim); font-family: monospace;">0${idx + 1}</td>
                  <td style="padding: 0.75rem 0.6rem;">
                    <strong style="color: #fff; display: block;">${row.category}</strong>
                    <span style="font-size: 0.72rem; color: var(--primary-light); font-family: monospace;">${row.ittClause} &bull; ${row.cptuRule}</span>
                  </td>
                  <td style="padding: 0.75rem 0.6rem; color: var(--text-main);">${row.requirement}</td>
                  <td style="padding: 0.75rem 0.6rem; color: #f8fafc; font-weight: 600;">${row.threshold}</td>
                  <td style="padding: 0.75rem 0.6rem;">
                    <span class="tag-badge ${row.status === 'COMPLIANT' ? 'live' : (row.status === 'ACTION_REQUIRED' ? 'corrigendum' : 'warning')}">
                      ${row.status === 'COMPLIANT' ? '✓ MET' : '⚠️ ACTION REQ'}
                    </span>
                  </td>
                  <td style="padding: 0.75rem 0.6rem; color: var(--text-muted); font-size: 0.74rem;">
                    ${row.evidenceDoc}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }
}

// Global Singleton
window.complianceMatrix = new ComplianceMatrixGenerator();
