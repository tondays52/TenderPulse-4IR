/* Win/loss dashboard: reports only outcomes deliberately recorded by the team. */
(function () {
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c]));
  const money = value => Number(value || 0).toLocaleString('en-BD', { maximumFractionDigits: 2 });
  const kpis = () => document.getElementById('outcomeLearningKpis');
  const agencies = () => document.getElementById('outcomeLearningAgencies');
  const lessons = () => document.getElementById('outcomeLearningLessons');
  const exportButton = () => document.getElementById('btnExportOutcomeLearning');
  function empty(node, message) { node.innerHTML = `<div class="corrigendum-empty">${esc(message)}</div>`; }
  function render(data) {
    const totals = data.totals || {};
    if (!totals.recorded_outcomes) { empty(kpis(), 'No bid outcomes have been recorded yet. Record submission results to begin learning from them.'); empty(agencies(), 'No agency performance data yet.'); empty(lessons(), 'No lessons recorded yet.'); return; }
    const rate = totals.win_rate_pct == null ? '—' : `${totals.win_rate_pct}%`;
    kpis().innerHTML = [
      ['Recorded outcomes', totals.recorded_outcomes, `${totals.submitted || 0} awaiting a decision`],
      ['Decisioned bids', totals.decisioned || 0, `${totals.won || 0} won · ${totals.lost || 0} lost`],
      ['Win rate', rate, 'Won ÷ won + lost'],
      ['Awarded value', `৳${money(totals.awarded_contract_value)}`, 'Recorded winning contract value'],
    ].map(([label, value, note]) => `<article class="outcome-learning-kpi"><small>${esc(label)}</small><strong>${esc(value)}</strong><span>${esc(note)}</span></article>`).join('');
    const byAgency = data.by_agency || [];
    agencies().innerHTML = byAgency.length ? byAgency.map(item => {
      const rateText = item.win_rate_pct == null ? 'No decisions yet' : `${item.win_rate_pct}% win rate`;
      const width = item.win_rate_pct == null ? 0 : Math.max(2, Math.min(100, item.win_rate_pct));
      return `<article class="outcome-learning-agency"><div class="outcome-learning-agency-head"><strong>${esc(item.agency)}</strong><span>${esc(rateText)}</span></div><small>${item.won} won · ${item.lost} lost · ${item.submitted} awaiting decision · ৳${money(item.awarded_contract_value)}</small><div class="outcome-learning-bar" aria-label="${esc(rateText)}"><i style="width:${width}%"></i></div></article>`;
    }).join('') : '<div class="corrigendum-empty">No agency performance data yet.</div>';
    const records = data.lessons || [];
    lessons().innerHTML = records.length ? records.slice(0, 6).map(item => `<article class="outcome-learning-lesson"><strong>${esc(item.tender_title || item.tender_id)} · ${esc(item.status)}</strong><br>${esc(item.lessons_learned)}<small>${esc(item.agency)}${item.outcome_date ? ` · ${esc(item.outcome_date)}` : ''}</small></article>`).join('') : '<div class="corrigendum-empty">No lessons recorded yet. Capture a short lesson with each win or loss.</div>';
  }
  async function load() {
    const signedIn = Boolean(localStorage.getItem('tenderpulse_access_token')); exportButton().disabled = !signedIn;
    if (!window.TenderApiService || !signedIn) { empty(kpis(), 'Sign in to view recorded outcomes.'); empty(agencies(), 'Sign in required.'); empty(lessons(), 'Sign in required.'); return; }
    empty(kpis(), 'Loading win/loss learning data…');
    try { render(await window.TenderApiService.getBidOutcomeLearningDashboard()); }
    catch (error) { empty(kpis(), `Learning dashboard unavailable: ${error.message}`); empty(agencies(), 'No agency performance data available.'); empty(lessons(), 'No lessons available.'); }
  }
  async function exportReport() { const button = exportButton(); if (button.disabled) return; button.disabled = true; try { await window.TenderApiService.downloadBidOutcomeLearningReport(); } catch (error) { alert(`Could not export report: ${error.message}`); } finally { button.disabled = false; } }
  document.addEventListener('DOMContentLoaded', () => { document.getElementById('btnRefreshOutcomeLearning')?.addEventListener('click', load); exportButton()?.addEventListener('click', exportReport); window.tenderStore?.subscribe('authChange', load); window.refreshOutcomeLearningDashboard = load; load(); });
}());
