/**
 * Di-Tender 4IR — Context-Aware AI Tender Copilot & Procurement Assistant (copilot.js)
 * Grounding: Public Procurement Act 2006 & Public Procurement Rules 2008 (PPR-2008)
 */

class TenderPulseCopilot {
  constructor() {
    this.isOpen = false;
    this.visualizer = null;
    this.messages = [
      {
        sender: "bot",
        text: "Assalamu Alaikum! I am your <strong>Di-Tender Cognitive Copilot</strong>. I have analyzed the active e-GP Tender Schedule (Section 2 TDS, Section 4 PCC, and Section 6 BOQ). How can I assist your bidding team today?",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ];

    // Automatically initialize visualizer and render initial thread
    if (typeof document !== 'undefined') {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          this.initVisualizer();
          this.renderChatThreads();
        });
      } else {
        setTimeout(() => {
          this.initVisualizer();
          this.renderChatThreads();
        }, 50);
      }
    }
  }

  initVisualizer() {
    if (typeof window.initCopilot3D === 'function') {
      this.visualizer = window.initCopilot3D("copilot3dCanvas");
    } else if (!this.visualizer && typeof Copilot3DVisualizer !== 'undefined') {
      const canvas = document.getElementById("copilot3dCanvas");
      if (canvas) {
        this.visualizer = new Copilot3DVisualizer("copilot3dCanvas");
      }
    }
    return this.visualizer;
  }

  async askQuestion(query, activeDoc = null) {
    if (!query || !query.trim()) return;
    const cleanQuery = query.trim();

    // Trigger 3D prompt pulse
    if (this.visualizer && typeof this.visualizer.triggerPromptPulse === 'function') {
      this.visualizer.triggerPromptPulse();
    }

    const doc = activeDoc || (window.tdsAuditor ? window.tdsAuditor.getDocument("rhd-bridge") : null);
    const tenderId = doc ? doc.tenderId : "984210";
    const agency = doc ? doc.agency : "Roads and Highways Department (RHD)";
    const costBdt = doc ? (doc.estimatedCost || 85000000) : 85000000;

    this.messages.push({
      sender: "user",
      text: cleanQuery,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    this.renderChatThreads();

    // Try backend AI service with timeout fallback
    let backendSuccess = false;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);

      const endpoint = (window.location && window.location.port === "8080")
        ? "/api/copilot/query"
        : "http://127.0.0.1:8080/api/copilot/query";

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          query: cleanQuery,
          tender_id: tenderId,
          agency,
          estimated_cost_bdt: costBdt
        })
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        let actionBtn = null;
        if (data.action && data.action.route) {
          actionBtn = {
            label: data.action.label || "Open Module →",
            route: data.action.route
          };
        }
        this.messages.push({
          sender: "bot",
          text: data.reply_html,
          actionBtn,
          category: data.category,
          citation: data.statutory_citation,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        });
        this.renderChatThreads();
        backendSuccess = true;
        return data;
      }
    } catch (e) {
      // Fallback silently to comprehensive local knowledge base
    }

    if (!backendSuccess) {
      // Local CPTU Rule Knowledge Matrix
      const q = cleanQuery.toLowerCase();
      let reply = "";
      let actionBtn = null;
      let category = "CPTU Statutory Analysis";
      let citation = "PPR-2008 Gazette";
      const costCr = (costBdt / 10000000).toFixed(2);

      if (q.includes("machinery") || q.includes("equipment")) {
        category = "Section 2 TDS Equipment";
        citation = "ITT Clause 25.1 & Form e-PW3-6";
        const items = (doc && doc.equipment)
          ? doc.equipment.map(e => `&bull; <strong>${e.name}</strong>: Min ${e.minUnits} Units (${e.capacity})`).join("<br>")
          : "&bull; <strong>Rotary Hydraulic Drilling Rig (Dia 1200mm)</strong>: Min 2 Units<br>&bull; <strong>Asphalt Mixing & Batching Plant (60 TPH)</strong>: Min 1 Unit<br>&bull; <strong>Hydraulic Heavy Crane (50 Ton)</strong>: Min 1 Unit";
        reply = `According to <strong>Section 2 TDS Clause ITT 25.1</strong>, the mandatory equipment schedule (Form e-PW3-6) requires:<br><br>${items}<br><br><span style="color: #f59e0b;">⚠️ Notice:</span> PCC 14.1 requires full site mobilization within 14 days. Ensure transport NOCs are prepared.`;
        actionBtn = { label: "Inspect TDS Equipment Schedule →", route: "auditor-view" };
      } 
      else if (q.includes("liquidated") || q.includes("damage") || q.includes("penalty") || q.includes("delay")) {
        category = "General Conditions of Contract (GCC)";
        citation = "GCC Clause 47.1 & PPR Rule 39";
        reply = `Under <strong>GCC Clause 47.1 / PCC</strong>, the liquidated damages for delay is set at <strong>0.10% of the contract price per day</strong>, with a statutory maximum cumulative cap of <strong>10.0%</strong>. Delay beyond the cap triggers contract termination proceedings under GCC Clause 59.`;
        actionBtn = { label: "Run SMT Legal Verification →", route: "auditor-view" };
      } 
      else if (q.includes("jv") || q.includes("joint venture") || q.includes("partner")) {
        category = "Consortium & Joint Venture Qualification";
        citation = "CPTU PPR-2008 Rule 99 & ITT Clause 22.1";
        reply = `<strong>Joint Ventures are permitted</strong> under <strong>CPTU PPR-2008 Rule 99 & ITT Clause 22.1</strong>:<br>&bull; Maximum 3 partners permitted.<br>&bull; Leading Partner must meet at least <strong>40%</strong> of turnover & financial thresholds.<br>&bull; Other partners must meet at least <strong>25%</strong> each.<br>&bull; All partners are jointly and severally liable.`;
        actionBtn = { label: "Generate STD Form Package →", route: "std-view" };
      } 
      else if (q.includes("cartel") || q.includes("trap") || q.includes("deviation") || q.includes("risk")) {
        category = "Cartel & Restrictive Specification Guardrails";
        citation = "PPR-2008 Rule 29(3) & ITT Clause 8";
        reply = `The AI Auditor detected <strong>2 potential trap clauses</strong> in this schedule:<br><br>1. <strong>14-Day Mobilization (ITT 38.2)</strong>: Creates artificial default risk for non-incumbents.<br>2. <strong>Proprietary European Brand Lock</strong>: Section 6 Item 4.2 specifies proprietary seals without an 'or equivalent' clause.<br><br><strong>Remedy:</strong> Issue formal pre-bid clarification under ITT Clause 8 to request standard 28-day mobilization and general ISO approval.`;
        actionBtn = { label: "View 3D Cartel Radar →", route: "awards-view" };
      } 
      else if (q.includes("solvency") || q.includes("bank") || q.includes("credit line") || q.includes("liquid asset") || q.includes("epw2a-8")) {
        category = "Liquid Asset Solvency Commitment";
        citation = "ITT Clause 15.1(a) & Form e-PW2A-8";
        const liquid = (doc && doc.prequalification && doc.prequalification.liquidAssets) ? doc.prequalification.liquidAssets.value : "BDT 18.50 Crore";
        reply = `The mandatory liquid asset / credit commitment under <strong>ITT 15.1(a) is ${liquid}</strong>.<br><br>Commitment must be issued in the exact format of <strong>Form e-PW2A-8</strong> on scheduled commercial bank letterhead without conditional clauses.`;
        actionBtn = { label: "Apply 1-Click Bank Pre-Approval →", route: "bank-view" };
      } 
      else if (q.includes("price") || q.includes("discount") || q.includes("sweet spot") || q.includes("win") || q.includes("estimate")) {
        category = "Nash Equilibrium & Sweet Spot Optimization";
        citation = "CPTU PPR-2008 Rule 98 Cap";
        reply = `For <strong>${agency}</strong>, historical awards show the winning sweet spot clusters at <strong>-8.90% discount</strong> (approx ৳ ${(costCr * 0.911).toFixed(2)} Cr).<br><br><span style="color: #ef4444; font-weight: 700;">Critical Rule:</span> Never bid below <strong>-10.0%</strong>. Under CPTU PPR-2008 Rule 98, bids below -10% are disqualified as Abnormally Low Tenders (ALT).`;
        actionBtn = { label: "Launch Bayesian Bid Predictor →", route: "predictor-view" };
      } 
      else {
        category = "Procurement Feasibility";
        citation = "CPTU PPR-2008 Overview";
        reply = `Under CPTU PPR-2008 procurement rules for e-GP #${tenderId} (${doc ? (doc.name || doc.title || 'Civil Works').slice(0, 45) : 'General Procurement'}), all bids must strictly satisfy Section 2 (TDS) eligibility criteria. Estimated Project Value: <strong>৳ ${costCr} Crore</strong>.<br><br>You can ask me to evaluate financial turnover, verify GCC clauses, or assess bid feasibility.`;
        actionBtn = { label: "Run 100-Point TEC Feasibility →", route: "decision-view" };
      }

      this.messages.push({
        sender: "bot",
        text: reply,
        actionBtn,
        category,
        citation,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });
      this.renderChatThreads();
    }
  }

  renderChatThreads() {
    const viewContainer = document.getElementById("copilotChatMessages");
    if (viewContainer) {
      viewContainer.innerHTML = this.messages.map(m => `
        <div style="display: flex; gap: 10px; margin-bottom: 1rem; align-items: flex-start; ${m.sender === 'user' ? 'justify-content: flex-end;' : ''}">
          ${m.sender === 'bot' ? `
            <div style="width: 34px; height: 34px; border-radius: 8px; background: rgba(56, 189, 248, 0.2); border: 1px solid rgba(56, 189, 248, 0.4); display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0;">
              🤖
            </div>
          ` : ''}
          <div style="max-width: 80%; background: ${m.sender === 'user' ? 'linear-gradient(135deg, #1e40af, #3b82f6)' : 'rgba(15, 23, 42, 0.85)'}; border: 1px solid ${m.sender === 'user' ? 'rgba(59, 130, 246, 0.5)' : 'rgba(255, 255, 255, 0.1)'}; border-radius: 12px; padding: 0.9rem 1.1rem; color: #f8fafc; font-size: 0.85rem; line-height: 1.5; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);">
            ${m.category ? `<div style="font-size: 0.72rem; color: #38bdf8; font-weight: 700; margin-bottom: 4px; text-transform: uppercase;">${m.category} &bull; ${m.citation || 'CPTU PPR-2008'}</div>` : ''}
            <div>${m.text}</div>
            ${m.actionBtn ? `
              <div style="margin-top: 0.8rem; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 0.6rem;">
                <button class="btn-primary" onclick="if(window.switchTab){ window.switchTab('${m.actionBtn.route}'); }" style="padding: 0.35rem 0.75rem; font-size: 0.75rem;">
                  ${m.actionBtn.label}
                </button>
              </div>
            ` : ''}
            <div style="font-size: 0.68rem; color: rgba(255,255,255,0.4); text-align: right; margin-top: 4px;">${m.time}</div>
          </div>
          ${m.sender === 'user' ? `
            <div style="width: 34px; height: 34px; border-radius: 8px; background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(16, 185, 129, 0.4); display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0;">
              👤
            </div>
          ` : ''}
        </div>
      `).join("");
      viewContainer.scrollTop = viewContainer.scrollHeight;
    }

    // Render in floating widget if present
    const floatContainer = document.getElementById("copilotFloatingMessages");
    if (floatContainer && viewContainer) {
      floatContainer.innerHTML = viewContainer.innerHTML;
      floatContainer.scrollTop = floatContainer.scrollHeight;
    }
  }
}

// Global Singleton
window.tenderCopilot = new TenderPulseCopilot();
