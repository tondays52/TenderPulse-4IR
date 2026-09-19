/* Phase 2: explainable, published-data opportunity ranking. */
(function () {
  const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));
  function render(items) {
    const target = document.getElementById('opportunityRankingList');
    if (!target) return;
    if (!items.length) { target.innerHTML = '<div class="corrigendum-empty">No ranked live tenders are available.</div>'; return; }
    target.innerHTML = items.map(item => `<article class="opportunity-card"><div class="opportunity-card-head"><span class="opportunity-score">${item.priority_score}/100</span><span class="opportunity-tier">${escapeHtml(item.priority_tier)}</span></div><div class="opportunity-card-title">${escapeHtml(item.title)}</div><div class="opportunity-card-meta">${escapeHtml(item.agency)} · ${item.days_remaining === null ? 'deadline unknown' : `${item.days_remaining}d remaining`} · ${item.corrigendum_count} amendment(s)</div><button class="btn-secondary" type="button" data-gonogo="${escapeHtml(item.tender_id)}">Run Go/No-Go</button><button class="btn-secondary" type="button" data-pipeline='${escapeHtml(JSON.stringify({tender_id:item.tender_id,tender_title:item.title,agency:item.agency,internal_due_date:item.closing_date,stage:"review",decision:"pending"}))}'>Add to shared pipeline</button></article>`).join('');
  }
  async function load() {
    const target = document.getElementById('opportunityRankingList');
    if (!target || !window.TenderApiService) return;
    if (!localStorage.getItem('tenderpulse_access_token')) { target.innerHTML = '<div class="corrigendum-empty">Sign in to load ranked live tenders.</div>'; return; }
    target.innerHTML = '<div class="corrigendum-empty">Ranking live tenders…</div>';
    try { render((await window.TenderApiService.getRankedOpportunities(8)).opportunities || []); } catch (error) { target.innerHTML = `<div class="corrigendum-empty">Ranking unavailable: ${escapeHtml(error.message)}</div>`; }
  }
  document.addEventListener('DOMContentLoaded', () => { document.getElementById('btnRefreshOpportunities')?.addEventListener('click', load); document.getElementById('opportunityRankingList')?.addEventListener('click', async e => { const go=e.target.closest('[data-gonogo]'); const button=e.target.closest('[data-pipeline]'); const result=document.getElementById('goNoGoResult'); if(go){go.disabled=true;try{const data=await window.TenderApiService.assessGoNoGo(go.dataset.gonogo);result.hidden=false;result.innerHTML=`<strong>${escapeHtml(data.decision.replace(/_/g,' '))} · ${data.total_score}/100</strong><br>${escapeHtml(data.decision_text)}<br><small>${escapeHtml(data.tec_scorecard.categories.map(c=>c.finding).join(' '))}</small>`;}catch(error){result.hidden=false;result.textContent=error.message}finally{go.disabled=false}return;} if (!button) return; button.disabled=true; try { await window.TenderApiService.saveBidPipelineItem(JSON.parse(button.dataset.pipeline)); button.textContent='Added to shared pipeline'; window.refreshSharedPipeline?.(); window.refreshSharedPreparationTasks?.(); window.refreshBidActivityTimeline?.(); window.switchTab?.('tracker-view'); } catch (error) { button.disabled=false; button.textContent=`Could not add: ${error.message}`; } }); window.tenderStore?.subscribe('authChange', load); window.refreshOpportunityRanking = load; load(); });
}());
