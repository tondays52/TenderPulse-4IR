/**
 * TenderPulse 4IR × Tender Trading Inc.
 * MyTender.io-Style Bid Preparation Tracker, Countdown Engine & Resilient Pipeline
 * Converts Bangladesh e-GP tender deadlines into a 5-phase milestone workflow
 * with embedded AI actions, live countdown telemetry, persistent pipeline storage,
 * and resilient retry mechanisms.
 */

class BidPreparationTracker {
  constructor() {
    this.storageKey = "tp_bid_tracker_state";
    this.pipelineStorageKey = "tp_tracked_pipeline_tenders";
    this.defaultTenders = [
      { id: "984210", title: "RHD 4-Lane RCC Girder Bridge over Meghna (৳ 48.5 Cr)", agency: "Roads and Highways Department (RHD)", closingDate: "2026-10-18 12:00", cost: 485000000, securityBG: 9700000, stdType: "e-PW3", division: "Dhaka", district: "Gazipur" },
      { id: "986772", title: "LGED Rural Connectivity Upgrade Phase-IV (৳ 32.0 Cr)", agency: "Local Government Engineering Department (LGED)", closingDate: "2026-10-24 14:00", cost: 320000000, securityBG: 6400000, stdType: "e-PW2A", division: "Chattogram", district: "Cumilla" },
      { id: "989104", title: "PWD 250-Bed District Hospital Extension (৳ 55.0 Cr)", agency: "Public Works Department (PWD)", closingDate: "2026-11-02 11:30", cost: 550000000, securityBG: 11000000, stdType: "e-PW3", division: "Sylhet", district: "Sylhet" },
      { id: "991208", title: "BWDB Embankment Slope Protection (৳ 28.0 Cr)", agency: "Bangladesh Water Development Board (BWDB)", closingDate: "2026-11-15 15:00", cost: 280000000, securityBG: 5600000, stdType: "e-PW2A", division: "Khulna", district: "Khulna" },
      { id: "993415", title: "BREB 33/11kV Automated Grid Substation (৳ 21.0 Cr)", agency: "Bangladesh Rural Electrification Board (BREB)", closingDate: "2026-11-28 12:00", cost: 210000000, securityBG: 4200000, stdType: "e-PG3", division: "Rajshahi", district: "Bogura" }
    ];
  }

  /**
   * Loads all tracked tenders from localStorage or initializes defaults
   */
  getTrackedTenders() {
    try {
      const stored = localStorage.getItem(this.pipelineStorageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.warn("Failed to load pipeline tenders from storage:", e);
    }
    this.saveTrackedTenders(this.defaultTenders);
    return [...this.defaultTenders];
  }

  /**
   * Saves tracked tenders list to localStorage
   */
  saveTrackedTenders(tenders) {
    try {
      localStorage.setItem(this.pipelineStorageKey, JSON.stringify(tenders));
    } catch (e) {
      console.error("Failed to save pipeline tenders:", e);
    }
  }

  /**
   * Adds a tender to the active pipeline tracking list
   */
  addTenderToPipeline(tender) {
    if (!tender) return false;
    const tenders = this.getTrackedTenders();
    const tenderId = String(tender.id || tender.tenderId || "999000");

    const existingIndex = tenders.findIndex(t => String(t.id || t.tenderId) === tenderId);
    const normalized = {
      id: tenderId,
      tenderId: tenderId,
      title: tender.title || `e-GP Procurement Package #${tenderId}`,
      agency: tender.agency || "Procuring Entity",
      closingDate: tender.closingDate || "2026-11-30 12:00",
      cost: tender.cost || tender.estimatedCost || 50000000,
      securityBG: tender.securityBG || tender.tenderSecurity || Math.round((tender.cost || 50000000) * 0.025),
      stdType: tender.stdType || "e-PW3",
      division: tender.division || "Dhaka",
      district: tender.district || "Dhaka"
    };

    if (existingIndex >= 0) {
      tenders[existingIndex] = normalized;
    } else {
      tenders.unshift(normalized);
    }

    this.saveTrackedTenders(tenders);
    return true;
  }

  /**
   * Removes a tender from the pipeline
   */
  removeTenderFromPipeline(tenderId) {
    let tenders = this.getTrackedTenders();
    tenders = tenders.filter(t => String(t.id || t.tenderId) !== String(tenderId));
    if (tenders.length === 0) {
      tenders = [...this.defaultTenders];
    }
    this.saveTrackedTenders(tenders);
    return tenders;
  }

  /**
   * Computes the 5-phase preparation milestones for a given tender
   */
  getMilestones(tender) {
    const tenderId = tender ? String(tender.tenderId || tender.id || "984210") : "984210";
    const closingDate = tender ? (tender.closingDate || "2026-10-18 12:00") : "2026-10-18 12:00";
    const title = tender ? (tender.title || `Tender #${tenderId}`) : "Tender Package";
    const agency = tender ? (tender.agency || "Procuring Entity") : "RHD";
    const estCost = tender ? (tender.cost || tender.estimatedCost || 485000000) : 485000000;
    const stdType = tender ? (tender.stdType || "e-PW3") : "e-PW3";

    const savedState = this.loadState(tenderId);

    const phases = [
      {
        phaseId: "p1",
        name: "Phase 1: Prequalification & Trap Audit",
        timeframe: "Days -15 to -12",
        description: "Verify procurement notices, eliminate hidden qualifying traps, and confirm financial turnover eligibility.",
        tasks: [
          {
            id: `${tenderId}_t1_1`,
            label: `Download Section 2 (TDS), Section 4 (PCC), Section 6 (BOQ) for ${stdType}`,
            role: "Procurement Exec",
            actionType: "sample_boq",
            actionLabel: "Preview BOQ & TDS"
          },
          {
            id: `${tenderId}_t1_2`,
            label: "Run AI TDS Auditor to detect proprietary brand traps and 14-day setup traps",
            role: "Legal Counsel",
            actionType: "auditor_view",
            actionLabel: "Audit TDS Traps"
          },
          {
            id: `${tenderId}_t1_3`,
            label: "Calculate CPTU capacity (A × N × 1.5 - B) & determine JV requirement",
            role: "Managing Director",
            actionType: "calculator_view",
            actionLabel: "Calculate Capacity"
          }
        ]
      },
      {
        phaseId: "p2",
        name: "Phase 2: Financial Guarantees & Bank Solvency",
        timeframe: "Days -12 to -8",
        description: "Issue bank credit lines, purchase tender security pay orders, and verify audited turnover.",
        tasks: [
          {
            id: `${tenderId}_t2_1`,
            label: "Submit 1-Click Bank Credit Line request (Form e-PW2A-8 / e-PW3-8)",
            role: "Finance Manager",
            actionType: "bank_view",
            actionLabel: "1-Click Bank PG"
          },
          {
            id: `${tenderId}_t2_2`,
            label: "Purchase Tender Security Pay Order / Bank Guarantee (Form e-PW3-7)",
            role: "Finance Manager",
            actionType: "bank_view",
            actionLabel: "Generate Security BG"
          },
          {
            id: `${tenderId}_t2_3`,
            label: "Verify audited turnover declarations and NBR tax certificates with Z3 SMT Prover",
            role: "Chartered Accountant",
            actionType: "smt_verify",
            actionLabel: "Run SMT Tax Check"
          }
        ]
      },
      {
        phaseId: "p3",
        name: "Phase 3: Technical Dossier & Site Equipment",
        timeframe: "Days -8 to -4",
        description: "Assemble verified engineering personnel CVs, equipment leases, and past completion certificates.",
        tasks: [
          {
            id: `${tenderId}_t3_1`,
            label: "Compile signed Key Personnel CVs (Form e-PW3-5) and IEB numbers",
            role: "HR / Project Lead",
            actionType: "std_view",
            stdForm: "pw3-5",
            actionLabel: "Build Form e-PW3-5"
          },
          {
            id: `${tenderId}_t3_2`,
            label: "Attach Equipment Ownership / Lease Agreements (Form e-PW3-6)",
            role: "Equipment Officer",
            actionType: "std_view",
            stdForm: "pw3-6",
            actionLabel: "Build Form e-PW3-6"
          },
          {
            id: `${tenderId}_t3_3`,
            label: "Verify similar bridge/building completion certificate with Sentinel-1 SAR Ground Truth",
            role: "Managing Director",
            actionType: "sar_audit",
            actionLabel: "Audit SAR Ground Truth"
          }
        ]
      },
      {
        phaseId: "p4",
        name: "Phase 4: AI Optimal Pricing & Rate Cap Check",
        timeframe: "Days -4 to -2",
        description: "Price line items using historical agency databases, predict Nash Equilibrium sweet spots, and check rate caps.",
        tasks: [
          {
            id: `${tenderId}_t4_1`,
            label: "Analyze BOQ market price variance vs PWD/RHD Schedule of Rates (SoR)",
            role: "Chief Estimator",
            actionType: "sample_boq",
            actionLabel: "Check BOQ Variance"
          },
          {
            id: `${tenderId}_t4_2`,
            label: "Run AI Winning Bid Price Predictor for agency sweet spot",
            role: "Chief Estimator",
            actionType: "predictor_view",
            actionLabel: "Bayesian Sweetspot"
          },
          {
            id: `${tenderId}_t4_3`,
            label: "Confirm proposed discount does not violate CPTU Rule 98 10% rate cap",
            role: "Managing Director",
            actionType: "smt_verify",
            actionLabel: "Verify Rule 98 SMT"
          }
        ]
      },
      {
        phaseId: "p5",
        name: "Phase 5: Digital e-GP Submission & Encryption",
        timeframe: "Days -1 to Closing",
        description: "Perform end-to-end encrypted submission on e-GP with USB token validation and receipt archiving.",
        tasks: [
          {
            id: `${tenderId}_t5_1`,
            label: "Verify e-GP digital certificate USB token and browser Java runtime",
            role: "IT Admin",
            actionType: "token_check",
            actionLabel: "Test USB Token"
          },
          {
            id: `${tenderId}_t5_2`,
            label: "Upload encrypted Technical & Financial proposal files to eprocure.gov.bd",
            role: "Procurement Exec",
            actionType: "egp_submit",
            actionLabel: "Encrypt & Submit"
          },
          {
            id: `${tenderId}_t5_3`,
            label: "Download official e-GP Submission Acknowledgement Receipt before cutoff",
            role: "Managing Director",
            actionType: "download_receipt",
            actionLabel: "View Official Receipt"
          }
        ]
      }
    ];

    // Compute progress & phase status
    let totalTasks = 0;
    let completedTasks = 0;
    let currentPhaseIndex = 0;

    phases.forEach((p, pIdx) => {
      let phaseCompleted = 0;
      p.tasks.forEach(t => {
        t.completed = !!savedState[t.id];
        totalTasks++;
        if (t.completed) {
          completedTasks++;
          phaseCompleted++;
        }
      });

      p.completed = phaseCompleted === p.tasks.length;
      p.completionPct = Math.round((phaseCompleted / p.tasks.length) * 100);
      if (p.completed && pIdx === currentPhaseIndex && pIdx < phases.length - 1) {
        currentPhaseIndex = pIdx + 1;
      }
    });

    const progressPercent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    const isFullySubmitted = progressPercent === 100;

    // Calculate Countdown Telemetry
    const countdown = this.calculateCountdown(closingDate);

    return {
      tenderId,
      title,
      agency,
      estCost,
      stdType,
      closingDate,
      totalTasks,
      completedTasks,
      progressPercent,
      currentPhaseIndex,
      isFullySubmitted,
      countdown,
      phases
    };
  }

  /**
   * Computes remaining time until tender closing
   */
  calculateCountdown(closingDateStr) {
    try {
      const now = new Date().getTime();
      const target = new Date(closingDateStr.replace(" ", "T")).getTime();
      const diff = target - now;

      if (isNaN(diff) || diff <= 0) {
        return {
          expired: true,
          formatted: "00d 00h 00m 00s",
          days: 0, hours: 0, minutes: 0, seconds: 0,
          urgency: "danger",
          label: "Submission Window Closed"
        };
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      let urgency = "normal";
      if (days < 2) urgency = "danger";
      else if (days < 7) urgency = "warning";

      return {
        expired: false,
        formatted: `${days}d ${hours}h ${minutes}m ${seconds}s`,
        days, hours, minutes, seconds,
        urgency,
        label: `${days} Days Remaining`
      };
    } catch {
      return { expired: false, formatted: "14d 06h 22m 10s", days: 14, hours: 6, minutes: 22, seconds: 10, urgency: "normal", label: "14 Days Remaining" };
    }
  }

  /**
   * Toggles task completion state
   */
  toggleTask(tenderId, taskId) {
    const state = this.loadState(tenderId);
    state[taskId] = !state[taskId];
    this.saveState(tenderId, state);
    return state[taskId];
  }

  /**
   * Sets all tasks in a phase to completed
   */
  completePhase(tenderId, phaseIndex) {
    const doc = this.getTrackedTenders().find(t => String(t.id || t.tenderId) === String(tenderId));
    const tracker = this.getMilestones(doc);
    if (!tracker.phases[phaseIndex]) return;

    const state = this.loadState(tenderId);
    tracker.phases[phaseIndex].tasks.forEach(t => {
      state[t.id] = true;
    });
    this.saveState(tenderId, state);
  }

  /**
   * Resets / retries a specific phase (clears tasks in that phase for re-evaluation)
   */
  resetPhase(tenderId, phaseIndex) {
    const doc = this.getTrackedTenders().find(t => String(t.id || t.tenderId) === String(tenderId));
    const tracker = this.getMilestones(doc);
    if (!tracker.phases[phaseIndex]) return;

    const state = this.loadState(tenderId);
    tracker.phases[phaseIndex].tasks.forEach(t => {
      state[t.id] = false;
    });
    this.saveState(tenderId, state);
  }

  /**
   * Retries Phase 5 (e-GP re-submission flow)
   */
  retrySubmissionPhase(tenderId) {
    this.resetPhase(tenderId, 4); // Phase 5 index is 4
  }

  /**
   * Resets all tasks for a tender (Full Pipeline Reset)
   */
  resetAllTasks(tenderId) {
    this.saveState(tenderId, {});
  }

  loadState(tenderId) {
    try {
      const all = JSON.parse(localStorage.getItem(this.storageKey) || "{}");
      return all[tenderId] || {};
    } catch {
      return {};
    }
  }

  saveState(tenderId, state) {
    try {
      const all = JSON.parse(localStorage.getItem(this.storageKey) || "{}");
      all[tenderId] = state;
      localStorage.setItem(this.storageKey, JSON.stringify(all));
    } catch (e) {
      console.error("Failed to save bid tracker state:", e);
    }
  }

  /**
   * Renders the interactive MyTender.io-style pipeline UI
   */
  renderTrackerHTML(tracker) {
    if (!tracker) return "";

    const urgencyColor = tracker.countdown.urgency === "danger" ? "#f87171" : (tracker.countdown.urgency === "warning" ? "#fbbf24" : "#34d399");
    const urgencyBg = tracker.countdown.urgency === "danger" ? "rgba(239, 68, 68, 0.12)" : (tracker.countdown.urgency === "warning" ? "rgba(245, 158, 11, 0.12)" : "rgba(16, 185, 129, 0.12)");
    const urgencyBorder = tracker.countdown.urgency === "danger" ? "rgba(239, 68, 68, 0.3)" : (tracker.countdown.urgency === "warning" ? "rgba(245, 158, 11, 0.3)" : "rgba(16, 185, 129, 0.3)");
    const estCostCr = (tracker.estCost / 10000000).toFixed(2);

    return `
      <div class="bid-tracker-container" style="background: rgba(255,255,255,0.01); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1.25rem;">
        
        <!-- Header Banner & Countdown Strip -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 1rem;">
          <div style="flex: 1; min-width: 280px;">
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 0.45rem;">
              <span class="tender-id-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.76rem;">
                Tender #${tracker.tenderId}
              </span>
              <span style="font-size: 0.74rem; background: var(--bg-input); color: #cbd5e1; padding: 0.2rem 0.5rem; border-radius: 6px; border: 1px solid var(--border-subtle); font-weight: 600;">
                STD: ${tracker.stdType}
              </span>
              <span style="font-size: 0.74rem; background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 0.2rem 0.5rem; border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.3); font-weight: 700;">
                Budget: ৳ ${estCostCr} Cr
              </span>
            </div>
            <h3 style="font-size: 1.2rem; color: #fff; font-weight: 800; margin: 0.25rem 0; letter-spacing: -0.01em;">${tracker.title}</h3>
            <p style="font-size: 0.8rem; color: var(--text-dim); margin-top: 0.25rem;">
              Procuring Entity: <strong style="color: #cbd5e1;">${tracker.agency}</strong> &bull; Submission Cutoff: <strong style="color: #fbbf24;">${tracker.closingDate}</strong>
            </p>
          </div>

          <!-- Live Countdown & Overall Readiness Box -->
          <div style="display: flex; gap: 0.85rem; align-items: center; flex-wrap: wrap;">
            <!-- Countdown Pill -->
            <div style="background: ${urgencyBg}; border: 1px solid ${urgencyBorder}; border-radius: 10px; padding: 0.65rem 1.1rem; text-align: center;">
              <div style="font-size: 0.68rem; text-transform: uppercase; font-weight: 800; color: ${urgencyColor}; letter-spacing: 0.05em;">Closing Countdown</div>
              <div class="live-countdown-clock" data-closing="${tracker.closingDate}" style="font-size: 1.15rem; font-weight: 800; color: ${urgencyColor}; font-family: 'JetBrains Mono', monospace; margin-top: 0.15rem;">
                ${tracker.countdown.formatted}
              </div>
            </div>

            <!-- Readiness Score Box -->
            <div style="background: var(--bg-input); border: 1px solid var(--border-subtle); border-radius: 10px; padding: 0.65rem 1.1rem; text-align: right; min-width: 140px;">
              <div style="font-size: 1.65rem; font-weight: 900; color: ${tracker.progressPercent === 100 ? '#10b981' : '#38bdf8'}; line-height: 1.1;">
                ${tracker.progressPercent}%
              </div>
              <div style="font-size: 0.72rem; color: var(--text-dim); margin-top: 0.2rem; font-weight: 600;">
                ${tracker.completedTasks} of ${tracker.totalTasks} Tasks Compliant
              </div>
            </div>
          </div>
        </div>

        <!-- 5-Phase Interactive Stepper Progress Bar -->
        <div style="margin-bottom: 1.5rem; background: var(--bg-input); padding: 0.85rem 1rem; border-radius: 10px; border: 1px solid var(--border-subtle);">
          <div style="display: flex; justify-content: space-between; margin-bottom: 0.45rem; font-size: 0.72rem; color: var(--text-dim); font-weight: 700; flex-wrap: wrap; gap: 0.3rem;">
            <span style="color: ${tracker.phases[0]?.completed ? '#10b981' : '#38bdf8'};">Phase 1: Prequalification</span>
            <span style="color: ${tracker.phases[1]?.completed ? '#10b981' : (tracker.currentPhaseIndex === 1 ? '#38bdf8' : 'var(--text-dim)')};">Phase 2: Bank PG</span>
            <span style="color: ${tracker.phases[2]?.completed ? '#10b981' : (tracker.currentPhaseIndex === 2 ? '#38bdf8' : 'var(--text-dim)')};">Phase 3: Technical Dossier</span>
            <span style="color: ${tracker.phases[3]?.completed ? '#10b981' : (tracker.currentPhaseIndex === 3 ? '#38bdf8' : 'var(--text-dim)')};">Phase 4: AI Pricing</span>
            <span style="color: ${tracker.phases[4]?.completed ? '#10b981' : (tracker.currentPhaseIndex === 4 ? '#38bdf8' : 'var(--text-dim)')};">Phase 5: e-GP Submitted</span>
          </div>
          <div class="progress-track" style="height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden;">
            <div class="progress-fill" style="width: ${tracker.progressPercent}%; height: 100%; background: linear-gradient(90deg, #38bdf8 0%, #2563eb 50%, #10b981 100%); transition: width 0.4s ease;"></div>
          </div>
        </div>

        <!-- Phase Cards Accordion -->
        <div style="display: flex; flex-direction: column; gap: 1.15rem;">
          ${tracker.phases.map((p, pIdx) => {
            const isPhaseDone = p.completed;
            const phaseStatusColor = isPhaseDone ? "#10b981" : (pIdx === tracker.currentPhaseIndex ? "#38bdf8" : "#94a3b8");
            const phaseBadgeBg = isPhaseDone ? "rgba(16, 185, 129, 0.15)" : (pIdx === tracker.currentPhaseIndex ? "rgba(56, 189, 248, 0.15)" : "rgba(255,255,255,0.04)");
            const phaseBorderColor = isPhaseDone ? "rgba(16, 185, 129, 0.35)" : (pIdx === tracker.currentPhaseIndex ? "rgba(56, 189, 248, 0.35)" : "var(--border-subtle)");

            return `
              <div class="phase-card-wrapper" style="background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px solid ${phaseBorderColor}; padding: 1.15rem; transition: all 0.25s ease;">
                
                <!-- Phase Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem; border-bottom: 1px solid var(--border-subtle); padding-bottom: 0.65rem; flex-wrap: wrap; gap: 0.5rem;">
                  <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; background: ${phaseBadgeBg}; color: ${phaseStatusColor}; font-weight: 800; font-size: 0.82rem; border: 1.5px solid ${phaseStatusColor};">
                      ${isPhaseDone ? '✓' : (pIdx + 1)}
                    </span>
                    <div>
                      <span style="font-size: 0.95rem; font-weight: 800; color: #fff;">${p.name}</span>
                      <div style="font-size: 0.74rem; color: var(--text-dim); margin-top: 0.1rem;">${p.description}</div>
                    </div>
                  </div>

                  <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="font-size: 0.72rem; color: #38bdf8; font-weight: 700; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.3); padding: 0.25rem 0.6rem; border-radius: 6px;">${p.timeframe}</span>
                    <span style="font-size: 0.72rem; color: ${phaseStatusColor}; font-weight: 700; background: ${phaseBadgeBg}; padding: 0.25rem 0.6rem; border-radius: 6px; border: 1px solid ${phaseBorderColor};">
                      ${p.completionPct}% Completed
                    </span>
                    
                    <!-- Quick Phase Action: Advance or Reset/Retry -->
                    <button class="btn-secondary btn-phase-action" data-tender="${tracker.tenderId}" data-phase="${pIdx}" data-action="${isPhaseDone ? 'retry' : 'complete'}" style="padding: 0.25rem 0.65rem; font-size: 0.72rem; height: 28px; border-color: ${isPhaseDone ? 'rgba(239, 68, 68, 0.4)' : 'rgba(16, 185, 129, 0.4)'}; color: ${isPhaseDone ? '#fca5a5' : '#34d399'}; background: var(--bg-input);">
                      ${isPhaseDone ? '🔄 Reset &amp; Retry' : '✓ Mark Phase Done'}
                    </button>
                  </div>
                </div>

                <!-- Phase Tasks List -->
                <div style="display: flex; flex-direction: column; gap: 0.65rem;">
                  ${p.tasks.map(t => `
                    <div class="task-item-row" style="display: flex; align-items: center; justify-content: space-between; gap: 0.85rem; background: var(--bg-input); border: 1px solid ${t.completed ? 'rgba(16, 185, 129, 0.35)' : 'var(--border-subtle)'}; padding: 0.65rem 0.95rem; border-radius: 8px; transition: background 0.2s;">
                      
                      <!-- Checkbox + Label -->
                      <label style="display: flex; align-items: center; gap: 10px; font-size: 0.84rem; color: ${t.completed ? 'var(--text-dim)' : '#fff'}; font-weight: ${t.completed ? '400' : '600'}; cursor: pointer; text-decoration: ${t.completed ? 'line-through' : 'none'}; flex: 1; margin: 0;">
                        <input type="checkbox" class="task-checkbox" data-tender="${tracker.tenderId}" data-task="${t.id}" ${t.completed ? 'checked' : ''} style="width: 17px; height: 17px; accent-color: #10b981; cursor: pointer;">
                        <span>${t.label}</span>
                      </label>

                      <!-- Role Badge + Interactive AI Action Button -->
                      <div style="display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0;">
                        <span style="font-size: 0.68rem; color: #94a3b8; background: rgba(255,255,255,0.04); border: 1px solid var(--border-subtle); padding: 2px 8px; border-radius: 4px; font-weight: 600;">
                          ${t.role}
                        </span>

                        ${t.actionType ? `
                          <button class="btn-secondary btn-task-trigger" data-action="${t.actionType}" data-tender="${tracker.tenderId}" data-std="${t.stdForm || ''}" style="padding: 0.22rem 0.6rem; font-size: 0.72rem; height: 26px; border-color: rgba(56, 189, 248, 0.4); color: #38bdf8; background: var(--bg-card); white-space: nowrap; font-weight: 700;">
                            ⚡ ${t.actionLabel || 'Action'}
                          </button>
                        ` : ''}
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            `;
          }).join('')}
        </div>

        <!-- Bottom Action Strip -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1.5rem; padding-top: 1.1rem; border-top: 1px solid var(--border-subtle); flex-wrap: wrap; gap: 0.8rem;">
          <div style="display: flex; gap: 0.6rem; align-items: center;">
            <button class="btn-secondary" id="btnResetPipelineTasks" data-tender="${tracker.tenderId}" style="padding: 0.45rem 0.85rem; font-size: 0.76rem; border-color: rgba(239, 68, 68, 0.4); color: #fca5a5;">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
              <span>Reset All 15 Tasks</span>
            </button>
            <button class="btn-secondary" id="btnRemoveFromPipeline" data-tender="${tracker.tenderId}" style="padding: 0.45rem 0.85rem; font-size: 0.76rem; border-color: var(--border-subtle); color: var(--text-dim);">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              <span>Remove from Tracker</span>
            </button>
          </div>

          <div style="display: flex; gap: 0.6rem; align-items: center;">
            ${tracker.isFullySubmitted ? `
              <button class="btn-primary" onclick="window.openEgpReceiptModal('${tracker.tenderId}')" style="background: linear-gradient(135deg, #059669, #10b981); color: #ffffff; padding: 0.5rem 1.15rem; font-size: 0.82rem; font-weight: 700;">
                📜 Download Official e-GP Receipt
              </button>
            ` : `
              <button class="btn-secondary" onclick="window.triggerEgpSubmissionFlow('${tracker.tenderId}')" style="border-color: #10b981; color: #10b981; background: rgba(16, 185, 129, 0.1); padding: 0.5rem 1.1rem; font-size: 0.8rem; font-weight: 700;">
                🚀 Test e-GP Encryption &amp; Submit
              </button>
            `}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Renders the cross-tender multi-pipeline overview table
   */
  renderAllTendersTable(tenders, activeTenderId) {
    if (!Array.isArray(tenders) || tenders.length === 0) {
      return `<div style="padding: 1rem; color: var(--text-dim); font-size: 0.8rem;">No active tenders tracked in pipeline.</div>`;
    }

    return tenders.map(t => {
      const tracker = this.getMilestones(t);
      const isSelected = String(t.id || t.tenderId) === String(activeTenderId);
      const estCr = ((t.cost || 50000000) / 10000000).toFixed(1);
      const bgLakh = (((t.securityBG || Math.round((t.cost || 50000000) * 0.025))) / 100000).toFixed(1);

      return `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 1rem; background: ${isSelected ? 'rgba(56, 189, 248, 0.08)' : 'rgba(255,255,255,0.02)'}; border: 1px solid ${isSelected ? '#38bdf8' : 'var(--border-subtle)'}; border-radius: 8px; font-size: 0.78rem; flex-wrap: wrap; gap: 0.6rem;">
          <div style="display: flex; align-items: center; gap: 0.8rem; flex: 1; min-width: 260px;">
            <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.78rem;">
              #${t.id || t.tenderId}
            </div>
            <div>
              <div style="font-weight: 700; color: #fff; display: flex; align-items: center; gap: 6px;">
                <span>${(t.title || 'Procurement Package').slice(0, 50)}</span>
                <span style="font-size: 0.68rem; background: var(--bg-input); padding: 1px 6px; border-radius: 4px; border: 1px solid var(--border-subtle); color: #cbd5e1;">${t.stdType || 'e-PW3'}</span>
              </div>
              <div style="font-size: 0.7rem; color: var(--text-dim); margin-top: 2px;">
                ${t.agency || 'Procuring Entity'} &bull; Cutoff: <strong style="color: #fbbf24;">${t.closingDate}</strong>
              </div>
            </div>
          </div>

          <!-- Phase Milestone Mini Dots -->
          <div style="display: flex; align-items: center; gap: 4px;">
            ${tracker.phases.map((p, idx) => `
              <span title="${p.name} (${p.completionPct}%)" style="display: inline-block; width: 14px; height: 14px; border-radius: 50%; background: ${p.completed ? '#10b981' : (idx === tracker.currentPhaseIndex ? '#38bdf8' : 'rgba(255,255,255,0.1)')}; border: 1px solid ${p.completed ? '#10b981' : (idx === tracker.currentPhaseIndex ? '#38bdf8' : 'rgba(255,255,255,0.2)')}; text-align: center; font-size: 0.55rem; color: #fff; line-height: 12px; font-weight: 700;">
                ${p.completed ? '✓' : (idx + 1)}
              </span>
            `).join('')}
          </div>

          <!-- Readiness & Budget -->
          <div style="display: flex; align-items: center; gap: 1.2rem;">
            <div style="font-size: 0.72rem; text-align: right;">
              <div style="color: #fff; font-weight: 700;">৳ ${estCr} Cr</div>
              <div style="color: #c084fc; font-size: 0.68rem;">BG: ৳ ${bgLakh}L</div>
            </div>

            <div style="text-align: right; min-width: 90px;">
              <div style="font-weight: 800; font-size: 0.95rem; color: ${tracker.progressPercent === 100 ? '#10b981' : '#38bdf8'};">${tracker.progressPercent}%</div>
              <div style="font-size: 0.68rem; color: var(--text-dim);">${tracker.completedTasks}/15 Tasks</div>
            </div>

            <button class="btn-secondary" onclick="window.selectPipelineTender('${t.id || t.tenderId}')" style="padding: 0.35rem 0.75rem; font-size: 0.74rem; border-color: ${isSelected ? '#38bdf8' : 'var(--border-subtle)'}; color: ${isSelected ? '#38bdf8' : '#fff'};">
              ${isSelected ? 'Active Dossier' : 'Open Dossier'}
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  /**
   * Renders the Tender Security Bank Guarantee (BG) Exposure Ledger
   */
  renderSecurityExposureTable(tenders) {
    if (!Array.isArray(tenders) || tenders.length === 0) {
      return `<div style="padding: 1rem; color: var(--text-dim); font-size: 0.8rem;">No active security guarantees recorded.</div>`;
    }

    const partnerBanks = ["Prime Bank PLC", "BRAC Bank PLC", "City Bank PLC", "Eastern Bank PLC", "Islami Bank Bangladesh"];

    return tenders.map((t, idx) => {
      const securityAmtBDT = t.securityBG || Math.round((t.cost || 50000000) * 0.025);
      const securityLakh = (securityAmtBDT / 100000).toFixed(2);
      const bank = partnerBanks[idx % partnerBanks.length];
      const formType = t.stdType === 'e-PG3' ? 'Form e-PG3-4 BG' : (t.stdType === 'e-PW2A' ? 'Form e-PW2A-7 Pay Order' : 'Form e-PW3-7 Bank Guarantee');

      return `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 1rem; background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: 8px; font-size: 0.78rem; flex-wrap: wrap; gap: 0.6rem;">
          <div style="display: flex; align-items: center; gap: 0.8rem;">
            <div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(192, 132, 252, 0.15); color: #c084fc; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.78rem;">
              🏦
            </div>
            <div>
              <div style="font-weight: 700; color: #fff;">${formType} &bull; Tender #${t.id || t.tenderId}</div>
              <div style="font-size: 0.7rem; color: var(--text-dim); margin-top: 2px;">
                Issuing Partner: <strong style="color: #cbd5e1;">${bank}</strong> &bull; Validity: <strong style="color: #10b981;">120 Days from Opening</strong>
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 1.2rem;">
            <div style="text-align: right;">
              <div style="font-weight: 800; font-size: 0.95rem; color: #c084fc;">৳ ${securityLakh} Lakh</div>
              <div style="font-size: 0.68rem; color: var(--text-dim);">2.5% Security Required</div>
            </div>

            <span class="tag-badge live" style="font-size: 0.68rem;">✓ AAA ISSUED</span>
          </div>
        </div>
      `;
    }).join('');
  }
}

// Global Singleton
window.bidTracker = new BidPreparationTracker();

