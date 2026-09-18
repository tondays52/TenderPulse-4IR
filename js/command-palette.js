/**
 * TenderPulse 4IR AI - Spotlight Command Palette (Ctrl + K / Cmd + K)
 * Instant search & navigation modal across all views, tools, and live tenders.
 */

(function() {
  'use strict';

  // Search items index
  const SEARCH_ITEMS = [
    // Views / Workspaces
    { id: 'mining-view', title: '24/7 Autonomous Harvester Terminal', subtitle: 'Live e-GP crawler, packet streams, and gazette diff', category: 'Pipeline', icon: '⛏️', tab: 'mining-view', workspace: 'ws-pipeline' },
    { id: 'search-view', title: 'Tender Explorer & Advanced Filter', subtitle: 'Browse 1,300+ indexed tenders with agency filter', category: 'Pipeline', icon: '🔍', tab: 'search-view', workspace: 'ws-pipeline' },
    { id: 'awards-view', title: 'Awards Intelligence & "Who Won?"', subtitle: 'Historical contract awards, winning rates & syndicate tracking', category: 'Pipeline', icon: '🏆', tab: 'awards-view', workspace: 'ws-pipeline' },
    { id: 'predictor-view', title: 'AI Optimal Bid Price Predictor', subtitle: 'Agency-specific rate cap predictor (-8.9% RHD / -9.8% LGED)', category: 'AI & Forensics', icon: '🧠', tab: 'predictor-view', workspace: 'ws-forensics' },
    { id: 'auditor-view', title: 'TDS Auditor & SMT Legal Prover', subtitle: 'Z3 SMT satisfiability proof certificate for CPTU Rule 39/40', category: 'AI & Forensics', icon: '⚖️', tab: 'auditor-view', workspace: 'ws-forensics' },
    { id: 'cartel-tool', title: 'GAT Cartel & Collusion Radar', subtitle: 'Bipartite network analysis for rotational winning & cover-bidding', category: 'AI & Forensics', icon: '🕸️', tab: 'mining-view', action: 'openCartel', workspace: 'ws-forensics' },
    { id: 'ecms-view', title: 'e-CMS Contract Hub & SAR Satellite Auditor', subtitle: 'Sentinel-1 radar backscatter coherence vs claimed MB bill', category: 'AI & Forensics', icon: '🛰️', tab: 'ecms-view', workspace: 'ws-forensics' },
    { id: 'calculator-view', title: 'Tenderer Capacity & JV Math', subtitle: 'Calculate Cap = (A x N x 1.5) - B per PPR Rule 98', category: 'Capital & Compliance', icon: '🧮', tab: 'calculator-view', workspace: 'ws-capital' },
    { id: 'bank-view', title: 'Bank Credit Hub & Pre-Approval', subtitle: 'Form e-PW2A-8 liquid credit commitments & shariah financing', category: 'Capital & Compliance', icon: '🏦', tab: 'bank-view', workspace: 'ws-capital' },
    { id: 'std-view', title: 'Smart STD & Proposal Generator', subtitle: 'Automated Form e-PW2/3 document packet builder', category: 'Capital & Compliance', icon: '📑', tab: 'std-view', workspace: 'ws-capital' },
    { id: 'vault-view', title: 'Knowledge Vault & zk-SNARK Locker', subtitle: 'Company audited balance sheets & zero-knowledge turnover proofs', category: 'Capital & Compliance', icon: '🔒', tab: 'vault-view', workspace: 'ws-capital' },
    { id: 'heatmap-view', title: 'Procurement GIS Map', subtitle: 'Spatial visualization of tenders across 64 districts', category: 'Pipeline', icon: '🗺️', tab: 'heatmap-view', workspace: 'ws-pipeline' },

    // Quick Tools & Actions
    { id: 'act-smt', title: 'Run Z3 SMT Formal Legal Prover', subtitle: 'Compute mathematical SAT/UNSAT certificate for Rule 39/40', category: 'AI Actions', icon: '⚡', action: 'runSmt' },
    { id: 'act-sar', title: 'Run Sentinel-1 SAR Satellite Audit', subtitle: 'Verify RHD ৳85.80 Cr physical progress via radar coherence', category: 'AI Actions', icon: '🛰️', action: 'runSar' },
    { id: 'act-mine', title: 'Trigger Forced e-GP Gateway Scan', subtitle: 'Force immediate harvest query across CPTU eprocure.gov.bd', category: 'Harvester', icon: '🔄', action: 'forceMine' },
    { id: 'act-bounty', title: 'Launch TenderBounty Scout', subtitle: 'Automated bounty scanner targeting non-responsive tenders', category: 'Harvester', icon: '🎯', action: 'openBounty' }
  ];

  let selectedIndex = 0;
  let filteredItems = [];

  function initCommandPalette() {
    const modal = document.getElementById('commandPaletteModal');
    const input = document.getElementById('cmdPaletteInput');
    const resultsContainer = document.getElementById('cmdPaletteResults');
    const triggerBtn = document.getElementById('btnOpenCmdPalette');

    if (!modal || !input || !resultsContainer) return;

    // Open palette
    function openPalette() {
      modal.classList.add('active');
      modal.style.display = 'flex';
      input.value = '';
      input.focus();
      renderResults(SEARCH_ITEMS);
    }

    // Close palette
    function closePalette() {
      modal.classList.remove('active');
      modal.style.display = 'none';
    }

    window.openCommandPalette = openPalette;
    window.closeCommandPalette = closePalette;

    // Attach to ESC pill in search input
    const escPill = modal.querySelector('.kbd-shortcut');
    if (escPill) {
      escPill.style.cursor = 'pointer';
      escPill.addEventListener('click', closePalette);
    }

    // Keyboard shortcut listeners
    window.addEventListener('keydown', (e) => {
      // Ctrl + K or Cmd + K
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (modal.classList.contains('active') || modal.style.display === 'flex') {
          closePalette();
        } else {
          openPalette();
        }
      }
      // Escape closes modal
      if (e.key === 'Escape') {
        if (modal.classList.contains('active') || modal.style.display === 'flex') {
          e.preventDefault();
          closePalette();
        }
      }
      // Up / Down arrow navigation
      if (modal.classList.contains('active')) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          selectedIndex = (selectedIndex + 1) % filteredItems.length;
          highlightSelectedItem();
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          selectedIndex = (selectedIndex - 1 + filteredItems.length) % filteredItems.length;
          highlightSelectedItem();
        } else if (e.key === 'Enter') {
          e.preventDefault();
          if (filteredItems[selectedIndex]) {
            executeItem(filteredItems[selectedIndex]);
            closePalette();
          }
        }
      }
    });

    // Button click trigger
    if (triggerBtn) {
      triggerBtn.addEventListener('click', openPalette);
    }

    // Backdrop click closes
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closePalette();
    });

    // Input filter
    input.addEventListener('input', () => {
      const q = input.value.trim().toLowerCase();
      if (!q) {
        renderResults(SEARCH_ITEMS);
      } else {
        const matches = SEARCH_ITEMS.filter(item => 
          item.title.toLowerCase().includes(q) ||
          item.subtitle.toLowerCase().includes(q) ||
          item.category.toLowerCase().includes(q)
        );
        renderResults(matches);
      }
    });
  }

  function renderResults(items) {
    const container = document.getElementById('cmdPaletteResults');
    if (!container) return;

    filteredItems = items;
    selectedIndex = 0;

    if (items.length === 0) {
      container.innerHTML = `
        <div style="padding: 2.5rem; text-align: center; color: var(--text-dim);">
          <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">🔍</div>
          <div style="font-weight: 600; font-size: 0.9rem; color: #fff;">No matching tools or tenders found</div>
          <div style="font-size: 0.78rem; margin-top: 0.25rem;">Try searching for "SMT", "SAR", "Capacity", "e-CMS", or "LGED"</div>
        </div>
      `;
      return;
    }

    let html = '';
    let currentCategory = '';

    items.forEach((item, index) => {
      if (item.category !== currentCategory) {
        currentCategory = item.category;
        html += `<div class="cmd-category-header">${currentCategory}</div>`;
      }

      html += `
        <div class="cmd-item ${index === 0 ? 'selected' : ''}" data-index="${index}">
          <div class="cmd-item-icon">${item.icon}</div>
          <div class="cmd-item-content">
            <div class="cmd-item-title">${item.title}</div>
            <div class="cmd-item-sub">${item.subtitle}</div>
          </div>
          <span class="cmd-item-badge">Jump &rarr;</span>
        </div>
      `;
    });

    container.innerHTML = html;

    // Add click listeners to items
    container.querySelectorAll('.cmd-item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.getAttribute('data-index'), 10);
        if (filteredItems[idx]) {
          executeItem(filteredItems[idx]);
          const modal = document.getElementById('commandPaletteModal');
          if (modal) modal.classList.remove('active');
        }
      });
      el.addEventListener('mouseenter', () => {
        const idx = parseInt(el.getAttribute('data-index'), 10);
        selectedIndex = idx;
        highlightSelectedItem();
      });
    });
  }

  function highlightSelectedItem() {
    const items = document.querySelectorAll('.cmd-item');
    items.forEach((el, idx) => {
      if (idx === selectedIndex) {
        el.classList.add('selected');
        el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else {
        el.classList.remove('selected');
      }
    });
  }

  function executeItem(item) {
    // If workspace is defined, switch to it without forcing first tab
    if (item.workspace && window.switchWorkspace) {
      window.switchWorkspace(item.workspace, false);
    }

    // If tab is defined, switch tab
    if (item.tab) {
      const tabBtn = document.querySelector(`.nav-tab[data-tab="${item.tab}"]`);
      if (tabBtn) tabBtn.click();
    }

    // If specific action
    if (item.action === 'runSmt') {
      const ecmsTab = document.querySelector(`.nav-tab[data-tab="ecms-view"]`);
      if (ecmsTab) ecmsTab.click();
      setTimeout(() => {
        const btn = document.getElementById('btnRunSmtProof');
        if (btn) btn.click();
      }, 300);
    } else if (item.action === 'runSar') {
      const ecmsTab = document.querySelector(`.nav-tab[data-tab="ecms-view"]`);
      if (ecmsTab) ecmsTab.click();
      setTimeout(() => {
        const btn = document.getElementById('btnRunSarAudit');
        if (btn) btn.click();
      }, 300);
    } else if (item.action === 'forceMine') {
      const btn = document.getElementById('btnTriggerMine');
      if (btn) btn.click();
    } else if (item.action === 'openBounty') {
      const btn = document.getElementById('btnOpenBountyModal');
      if (btn) btn.click();
    }
  }

  // Initialize on load
  document.addEventListener('DOMContentLoaded', initCommandPalette);
})();
