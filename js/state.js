/**
 * TenderPulse 4IR × Tender Trading Inc.
 * Centralized Reactive State Store (state.js)
 * Implements a lightweight reactive state store with event listeners.
 */

class TenderStore {
  constructor() {
    let savedUser = null;
    let savedToken = null;
    try {
      const uStr = localStorage.getItem('tenderpulse_auth_user');
      if (uStr) savedUser = JSON.parse(uStr);
      savedToken = localStorage.getItem('tenderpulse_auth_token');
    } catch (e) {
      console.warn('Could not read auth from localStorage', e);
    }

    const defaultUser = {
      id: 'usr_admin',
      name: 'Enterprise Executive',
      role: 'Managing Director & Lead',
      initials: 'EE',
      clearance: 'Level 4 (Executive)',
      email: 'admin@tendertrading.gov.bd',
      agency: 'Tender Trading Inc.'
    };

    this.state = {
      tenders: [],
      filteredTenders: [],
      searchQuery: '',
      selectedAgency: 'ALL',
      selectedCategory: 'ALL',
      activeTab: 'overview-view',
      selectedTender: null,
      isAuthenticated: !!savedToken,
      authToken: savedToken || null,
      currentUser: savedUser || { id: 'guest', name: 'Guest User', role: 'Signed Out', initials: 'GU', clearance: 'Public View', email: '' },
      userProfiles: [
        { id: 'usr_admin', name: 'Enterprise Executive', role: 'Managing Director & Lead', initials: 'EE', clearance: 'Level 4 (Executive)', email: 'admin@tendertrading.gov.bd', agency: 'Tender Trading Inc.' },
        { id: 'usr_02', name: 'Engr. M. A. Karim, FIEB', role: 'Chief Procurement Estimator', initials: 'MK', clearance: 'Level 3 (Senior)', email: 'karim.engr@tendertrading.gov.bd', agency: 'RHD Engineering Division' },
        { id: 'usr_03', name: 'Tanzina Rahman, PMP', role: 'GovTech Bid Strategist', initials: 'TR', clearance: 'Level 3 (Senior)', email: 'tanzina.pmp@tendertrading.gov.bd', agency: 'LGED Procurement Cell' },
        { id: 'usr_04', name: 'Dr. S. K. Majumder', role: 'Legal & SMT Compliance Auditor', initials: 'SM', clearance: 'Level 4 (Executive)', email: 'majumder.law@tendertrading.gov.bd', agency: 'CPTU Legal Review Board' }
      ],
      stats: {
        totalTenders: 8,
        totalPipelineValueCr: 1485.60,
        totalSpentCr: 420.00,
        currentWorkCr: 1200.00,
        inProgressCr: 376.00,
        reservedCr: 210.00,
        activeContractsCount: 8,
        awaitingDecisionCount: 2,
        monitoredCount: 12,
        smtComplianceIndex: 3.9,
        cartelRiskIndex: 0.042
      },
      loading: {
        tenders: false,
        smt: false,
        sar: false,
        pdf: false,
        scraper: false,
        auth: false
      },
      backendStatus: {
        online: false,
        pythonVersion: '3.11',
        uptimeSeconds: 0,
        engines: {}
      },
      logs: []
    };

    if (typeof INITIAL_TENDERS !== 'undefined' && Array.isArray(INITIAL_TENDERS) && INITIAL_TENDERS.length > 0) {
      this.state.tenders = [...INITIAL_TENDERS];
      this.state.filteredTenders = [...INITIAL_TENDERS];
    }

    this.subscribers = new Map();
    this._initAuthSync();
  }

  async _initAuthSync() {
    if (window.TenderApiService && typeof window.TenderApiService.getPublicUsers === 'function') {
      try {
        const users = await window.TenderApiService.getPublicUsers();
        if (users && users.length > 0) {
          this.state.userProfiles = users;
          this._notify('userProfilesUpdated', users);
        }
      } catch (e) {
        // Fallback to local user profiles
      }
    }
  }

  getState() {
    return this.state;
  }

  setState(updates) {
    const prevState = { ...this.state };
    this.state = { ...this.state, ...updates };
    this._notify('stateChange', { prevState, currentState: this.state });
  }

  subscribe(event, callback) {
    if (typeof event === 'function') {
      callback = event;
      event = '*';
    }
    if (!this.subscribers.has(event)) {
      this.subscribers.set(event, new Set());
    }
    this.subscribers.get(event).add(callback);
    return () => this.subscribers.get(event).delete(callback);
  }

  _notify(event, payload) {
    if (this.subscribers.has(event)) {
      this.subscribers.get(event).forEach(cb => {
        try { cb(payload); } catch (e) { console.error(`[State Error] in ${event} listener:`, e); }
      });
    }
    if (event !== '*' && this.subscribers.has('*')) {
      this.subscribers.get('*').forEach(cb => {
        try { cb({ event, payload, state: this.state }); } catch (e) { console.error(`[State Error] in * listener:`, e); }
      });
    }
  }

  /**
   * Central User Profile & Authentication Management
   */
  async login(email, password) {
    this.setLoading('auth', true);
    try {
      let result;
      if (window.TenderApiService && typeof window.TenderApiService.login === 'function') {
        result = await window.TenderApiService.login(email, password);
      } else {
        // Local deterministic authentication
        const user = this.state.userProfiles.find(u => u.email.toLowerCase() === email.toLowerCase());
        if (!user) throw new Error('No registered account matches this email.');
        result = { token: 'mock_jwt_' + Date.now(), user };
      }

      this.state.isAuthenticated = true;
      this.state.authToken = result.access_token || result.token;
      this.state.currentUser = result.user;

      try {
        localStorage.setItem('tenderpulse_auth_user', JSON.stringify(result.user));
        localStorage.setItem('tenderpulse_auth_token', result.access_token || result.token);
      } catch (e) {}

      this._notify('authChange', { isAuthenticated: true, user: result.user });
      this._notify('userChanged', result.user);
      this._notify('stateChange', { prevState: this.state, currentState: this.state });
      return result;
    } finally {
      this.setLoading('auth', false);
    }
  }

  async register(userData) {
    this.setLoading('auth', true);
    try {
      let result;
      if (window.TenderApiService && typeof window.TenderApiService.register === 'function') {
        result = await window.TenderApiService.register(userData);
      } else {
        const initials = userData.name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase();
        const newUser = {
          id: 'usr_' + Date.now(),
          name: userData.name,
          email: userData.email,
          role: userData.role || 'Tender Analyst',
          initials: initials || 'TP',
          clearance: 'Level 3 (Senior)',
          agency: userData.agency || 'Tender Trading Inc.'
        };
        this.state.userProfiles.push(newUser);
        result = { token: 'mock_reg_jwt_' + Date.now(), user: newUser };
      }

      if (result.user) {
        if (!this.state.userProfiles.some(p => p.id === result.user.id)) {
          this.state.userProfiles.push(result.user);
        }
        this.state.isAuthenticated = true;
        this.state.authToken = result.access_token || result.token;
        this.state.currentUser = result.user;

        try {
          localStorage.setItem('tenderpulse_auth_user', JSON.stringify(result.user));
          localStorage.setItem('tenderpulse_auth_token', result.access_token || result.token);
        } catch (e) {}

        this._notify('authChange', { isAuthenticated: true, user: result.user });
        this._notify('userChanged', result.user);
        this._notify('stateChange', { prevState: this.state, currentState: this.state });
      }
      return result;
    } finally {
      this.setLoading('auth', false);
    }
  }

  async logout() {
    try {
      if (window.TenderApiService && typeof window.TenderApiService.logout === 'function') {
        await window.TenderApiService.logout(this.state.authToken);
      }
    } catch (e) {
      console.warn('Logout API error:', e);
    }

    this.state.isAuthenticated = false;
    this.state.authToken = null;
    this.state.currentUser = {
      id: 'guest',
      name: 'Guest User',
      role: 'Signed Out',
      initials: 'GU',
      clearance: 'Public View',
      email: ''
    };

    try {
      localStorage.removeItem('tenderpulse_auth_user');
      localStorage.removeItem('tenderpulse_auth_token');
    } catch (e) {}

    this._notify('authChange', { isAuthenticated: false, user: this.state.currentUser });
    this._notify('userChanged', this.state.currentUser);
    this._notify('stateChange', { prevState: this.state, currentState: this.state });
  }

  setCurrentUser(userId) {
    const profile = this.state.userProfiles.find(p => p.id === userId);
    if (profile) {
      this.state.currentUser = { ...profile };
      this.state.isAuthenticated = true;
      try {
        localStorage.setItem('tenderpulse_auth_user', JSON.stringify(this.state.currentUser));
      } catch (e) {}
      this._notify('userChanged', this.state.currentUser);
      this._notify('stateChange', { prevState: this.state, currentState: this.state });
    }
  }

  getCurrentUser() {
    return this.state.currentUser;
  }

  getUserProfiles() {
    return this.state.userProfiles;
  }

  /**
   * Set and filter tenders
   */
  setTenders(tenders) {
    this.state.tenders = tenders;
    this.applyFilters();
    this.recalculateStats();
  }

  /**
   * Filter tenders by search query and agency
   */
  applyFilters() {
    const q = (this.state.searchQuery || '').toLowerCase().trim();
    const agency = this.state.selectedAgency;

    this.state.filteredTenders = this.state.tenders.filter(t => {
      const matchAgency = (agency === 'ALL' || !agency) || (t.agency && t.agency.includes(agency));
      const matchSearch = !q || (
        (t.title && t.title.toLowerCase().includes(q)) ||
        (t.tenderId && t.tenderId.toString().includes(q)) ||
        (t.refNo && t.refNo.toLowerCase().includes(q)) ||
        (t.district && t.district.toLowerCase().includes(q)) ||
        (t.office && t.office.toLowerCase().includes(q))
      );
      return matchAgency && matchSearch;
    });

    this._notify('tendersUpdated', this.state.filteredTenders);
  }

  setSelectedAgency(agency) {
    this.state.selectedAgency = agency || 'ALL';
    this.applyFilters();
  }

  setSearchQuery(q) {
    this.state.searchQuery = q;
    this.applyFilters();
  }

  recalculateStats() {
    const tenders = this.state.tenders || [];
    const totalCount = tenders.length;
    let totalValBDT = 0;
    const agencyDist = {};

    tenders.forEach(t => {
      const cost = Number(t.cost || t.estimatedCost || 0);
      totalValBDT += cost;
      const ag = t.agency ? (t.agency.includes("LGED") ? "LGED" : (t.agency.includes("RHD") ? "RHD" : (t.agency.includes("BWDB") ? "BWDB" : (t.agency.includes("DPHE") ? "DPHE" : (t.agency.includes("PGCB") ? "PGCB" : (t.agency.includes("PWD") ? "PWD" : (t.agency.includes("DGHS") ? "DGHS" : "OTHER"))))))) : "OTHER";
      agencyDist[ag] = (agencyDist[ag] || 0) + 1;
    });

    const totalCr = (totalValBDT / 10000000);
    this.state.stats = {
      ...this.state.stats,
      totalTenders: totalCount,
      totalPipelineValueBDT: totalValBDT,
      totalPipelineValueCr: totalCr.toFixed(2),
      avgTenderBDT: totalCount > 0 ? Math.round(totalValBDT / totalCount) : 0,
      totalSpentCr: (totalCr * 0.88).toFixed(2),
      currentWorkCr: (totalCr * 0.72).toFixed(2),
      agencyDistribution: agencyDist
    };
    this._notify('statsUpdated', this.state.stats);
  }

  async loadLiveTenders() {
    this.setLoading('tenders', true);
    try {
      if (window.TenderApiService && typeof window.TenderApiService.getLiveTenders === 'function') {
        const liveTenders = await window.TenderApiService.getLiveTenders();
        if (Array.isArray(liveTenders) && liveTenders.length > 0) {
          console.info(`[TenderStore] Successfully loaded ${liveTenders.length} persistent tenders from backend.`);
          this.setTenders(liveTenders);
          return liveTenders;
        }
      }
    } catch (e) {
      console.warn('[TenderStore] Could not load live tenders from backend:', e);
    } finally {
      this.setLoading('tenders', false);
    }
    return this.state.tenders;
  }


  /**
   * Universal Dynamic Tender Selection & Reactive Parameter Enrichment
   */
  setSelectedTender(tenderOrId) {
    if (!tenderOrId) return null;

    let tender = null;
    if (typeof tenderOrId === 'string' || typeof tenderOrId === 'number') {
      const idStr = String(tenderOrId).toLowerCase();
      tender = this.state.tenders.find(t => 
        (t.id && String(t.id).toLowerCase() === idStr) ||
        (t.tenderId && String(t.tenderId).toLowerCase() === idStr) ||
        (t.refNo && String(t.refNo).toLowerCase() === idStr)
      );
      if (!tender) {
        tender = {
          id: tenderOrId,
          tenderId: tenderOrId,
          title: `Tender #${tenderOrId} Civil Infrastructure Works`,
          agency: String(tenderOrId).includes("RHD") ? "RHD" : (String(tenderOrId).includes("BWDB") ? "BWDB" : "LGED"),
          cost: 425000000,
          estimatedCost: 425000000,
          district: "Dhaka",
          location: "Dhaka Division, Bangladesh"
        };
      }
    } else if (typeof tenderOrId === 'object') {
      tender = { ...tenderOrId };
    }

    if (!tender) return null;

    const numBudget = Number(tender.cost || tender.estimatedCost || 500000000);
    const agency = tender.agency || (tender.tenderId ? String(tender.tenderId).split("/")[0] : "RHD");
    const district = tender.district || tender.location || "Dhaka";

    // 1. Spatial GIS Enrichment
    let spatialData = null;
    if (window.spatialGIS && typeof window.spatialGIS.resolveSpatialData === 'function') {
      spatialData = window.spatialGIS.resolveSpatialData(tender);
    } else {
      spatialData = {
        locationName: district,
        lat: 23.8103,
        lon: 90.4125,
        orbitTrack: "Sentinel-1A Descending Pass #142",
        meanCoherence: 0.88,
        elevationMeters: 18,
        claimedProgress: tender.progressClaimed || 75.0,
        physicalProgress: tender.progressPhysical || 74.5,
        varianceDiscrepancy: 0.5,
        isVerified: true
      };
    }

    // 2. Dynamic SMT Legal Math Predicates
    const smtClauses = {
      budgetBDT: numBudget,
      budgetCr: (numBudget / 10000000).toFixed(2),
      rule39TurnoverReq: Math.round(numBudget * 0.75),
      rule39TurnoverReqCr: (numBudget * 0.75 / 10000000).toFixed(2),
      rule40TurnoverReq: Math.round(numBudget * 0.75),
      rule40TurnoverReqCr: (numBudget * 0.75 / 10000000).toFixed(2),
      contractorTurnoverCr: "51.20",
      rule40LiquidityReq: Math.round(numBudget * 0.20),
      rule40LiquidityReqCr: (numBudget * 0.20 / 10000000).toFixed(2),
      contractorLiquidityCr: "15.00",
      bgRequired: Math.round(numBudget * 0.025),
      bgRequiredCr: (numBudget * 0.025 / 10000000).toFixed(2),
      maxExecutionTimeMonths: 18,
      assessedCapacityCr: (51.2 * 1.5 * 1.5 - 12.0).toFixed(2),
      status: "SATISFIABLE",
      zeroDisqualifiers: true
    };

    // 3. Dynamic Syndicate Risk Profile
    const isHighRisk = agency === "LGED" && numBudget < 100000000;
    const cartelProfile = {
      riskScore: isHighRisk ? 0.78 : (agency === "BWDB" ? 0.42 : 0.12),
      syndicateClassification: isHighRisk ? "SUSPECTED_ROTATIONAL_RING" : "COMPETITIVE_OPEN",
      activeCompetitors: isHighRisk ? ["Spectra Eng.", "Taher Brothers", "MM Builders"] : ["Abdul Monem", "Mir Akhter", "Max Infra"]
    };

    // Store complete enriched entity
    this.state.selectedTender = {
      ...tender,
      numBudget,
      agency,
      district,
      spatial: spatialData,
      smt: smtClauses,
      cartel: cartelProfile
    };

    // Notify all listeners
    this._notify('tenderSelected', this.state.selectedTender);
    this._notify('smtUpdated', smtClauses);
    this._notify('spatialUpdated', spatialData);
    this._notify('stateChange', { prevState: this.state, currentState: this.state });

    // Downstream 1: Sentinel-1 SAR Viewport Synchronization
    if (window.sarRadarInstance && typeof window.sarRadarInstance.setTenderSpatial === 'function') {
      window.sarRadarInstance.setTenderSpatial(spatialData);
    }
    if (window.spatialGIS && typeof window.spatialGIS.fetchLiveRaster === 'function') {
      window.spatialGIS.fetchLiveRaster(spatialData.bbox, tender.tenderId || tender.id).then(rasterRes => {
        if (rasterRes && window.sarRadarInstance && typeof window.sarRadarInstance.applyRasterDisplacement === 'function') {
          if (rasterRes.elevation_matrix) {
            window.sarRadarInstance.applyRasterDisplacement(rasterRes.elevation_matrix);
          }
        }
      }).catch(() => {});
    }

    // Downstream 2: GAT Cartel Radar & Consortia Graph Synchronization
    if (window.cartelRadarInstance && typeof window.cartelRadarInstance.setTenderProfile === 'function') {
      window.cartelRadarInstance.setTenderProfile(this.state.selectedTender);
    }

    // Downstream 3: e-CMS Contract Hub Synchronization
    if (window.ecmsHub) {
      if (typeof window.ecmsHub.setTender === 'function') {
        window.ecmsHub.setTender(this.state.selectedTender);
      } else if (window.ecmsHub.activeContract) {
        window.ecmsHub.activeContract.contractId = tender.tenderId || tender.id || "e-CMS-2026-RHD-0842";
        window.ecmsHub.activeContract.name = tender.title || "Civil Works";
        window.ecmsHub.activeContract.value = numBudget;
      }
    }
    if (window.ecmsHubInstance && typeof window.ecmsHubInstance.setTender === 'function') {
      window.ecmsHubInstance.setTender(this.state.selectedTender);
    }
    const ecmsGrossInput = typeof document !== 'undefined' ? document.getElementById("ecmsGrossBillInput") : null;
    if (ecmsGrossInput) {
      ecmsGrossInput.value = Math.round(numBudget * 0.45);
      if (typeof window.updateEcmsBillCalculation === 'function') {
        window.updateEcmsBillCalculation();
      }
    }

    // Downstream 4: Z3 SMT Formal Solver Parameter Ingestion
    const smtOrig = typeof document !== 'undefined' ? document.getElementById("smtOrigValue") : null;
    const smtVo = typeof document !== 'undefined' ? document.getElementById("smtVoValue") : null;
    const smtTurnover = typeof document !== 'undefined' ? document.getElementById("smtTurnoverA") : null;
    if (smtOrig) smtOrig.value = smtClauses.budgetCr;
    if (smtVo) smtVo.value = (numBudget * 0.12 / 10000000).toFixed(2);
    if (smtTurnover) smtTurnover.value = smtClauses.rule39TurnoverReqCr;
    if (typeof window.executeSmtResolution === 'function') {
      window.executeSmtResolution(false);
    }

    // Downstream 5: Capacity Math Parameter Ingestion
    const sliderTender = typeof document !== 'undefined' ? document.getElementById("sliderTenderCost") : null;
    const sliderTurnover = typeof document !== 'undefined' ? document.getElementById("sliderTurnoverA") : null;
    const sliderLiquid = typeof document !== 'undefined' ? document.getElementById("sliderLiquidReq") : null;
    if (sliderTender) sliderTender.value = numBudget;
    if (sliderTurnover) sliderTurnover.value = smtClauses.rule39TurnoverReq;
    if (sliderLiquid) sliderLiquid.value = smtClauses.rule40LiquidityReq;
    if (typeof window.updateCapacityMath === 'function') {
      window.updateCapacityMath();
    }

    // Downstream 6: Executive AI Copilot & Bid Decision Grounding
    if (window.tenderCopilot) {
      window.tenderCopilot.activeTenderContext = this.state.selectedTender;
    }
    if (window.bidDecision && typeof window.bidDecision.evaluateTender === 'function') {
      window.bidDecision.evaluateTender(this.state.selectedTender);
    }

    return this.state.selectedTender;
  }

  getSelectedTender() {
    if (!this.state.selectedTender && this.state.tenders && this.state.tenders.length > 0) {
      this.setSelectedTender(this.state.tenders[0]);
    }
    return this.state.selectedTender;
  }

  addLog(log) {
    this.state.logs.push(log);
    if (this.state.logs.length > 200) this.state.logs.shift();
    this._notify('newLog', log);
  }

  setLoading(key, isLoading) {
    this.state.loading[key] = isLoading;
    this._notify('loadingChange', { key, isLoading });
  }

  setBackendStatus(status) {
    this.state.backendStatus = { ...this.state.backendStatus, ...status };
    this._notify('backendStatusChange', this.state.backendStatus);
  }
}

// Global Singleton Instance
window.tenderStore = new TenderStore();
