/* Post-submission outcome register that keeps the pipeline stage synchronized. */
(function () {
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c]));
  const state = { tenderId: '', canRecord: false };
  const status = () => document.getElementById('bidOutcomeStatus');
  const controls = () => document.getElementById('bidOutcomeControls');
  function field(id) { return document.getElementById(id); }
  function render(data) {
    const outcome = data.outcome || { status: 'not_recorded' }; state.canRecord = Boolean(data.can_record); controls().hidden = !state.canRecord;
    status().innerHTML = outcome.status === 'not_recorded' ? '<div class="outcome-summary outcome-pending"><strong>No outcome recorded</strong><span>Record the e-GP reference immediately after submission, then update the award result when known.</span></div>' : `<div class="outcome-summary outcome-${esc(outcome.status)}"><strong>${esc(outcome.status.toUpperCase())}</strong><span>${outcome.submission_reference ? `Reference: ${esc(outcome.submission_reference)}` : 'No submission reference recorded'}${outcome.recorded_by ? ` · recorded by ${esc(outcome.recorded_by)}` : ''}</span>${outcome.lessons_learned ? `<small>${esc(outcome.lessons_learned)}</small>` : ''}</div>`;
    if (!state.canRecord) return;
    field('bidOutcomeValue').value = outcome.status === 'not_recorded' ? 'submitted' : outcome.status;
    field('bidOutcomeReference').value = outcome.submission_reference || '';
    field('bidOutcomeSubmittedAt').value = outcome.submitted_at || '';
    field('bidOutcomeDate').value = outcome.outcome_date || '';
    field('bidOutcomeValueBdt').value = outcome.awarded_contract_value ?? '';
    field('bidOutcomeLessons').value = outcome.lessons_learned || '';
  }
  async function loadOutcome() { if (!state.tenderId || !window.TenderApiService || !localStorage.getItem('tenderpulse_access_token')) return; status().innerHTML = '<div class="corrigendum-empty">Loading bid outcome…</div>'; try { render(await window.TenderApiService.getBidOutcome(state.tenderId)); } catch (error) { status().innerHTML = `<div class="corrigendum-empty">Outcome unavailable: ${esc(error.message)}</div>`; } }
  async function loadPipeline() { const select = field('bidOutcomeTenderSelect'); if (!select || !window.TenderApiService) return; if (!localStorage.getItem('tenderpulse_access_token')) { select.innerHTML = '<option>Sign in required</option>'; return; } try { const items = (await window.TenderApiService.getBidPipeline()).items || []; if (!items.length) { select.innerHTML = '<option>No pipeline tender available</option>'; return; } if (!items.some(item => item.tender_id === state.tenderId)) state.tenderId = items[0].tender_id; select.innerHTML = items.map(item => `<option value="${esc(item.tender_id)}" ${item.tender_id === state.tenderId ? 'selected' : ''}>${esc(item.tender_id)} — ${esc(item.tender_title)}</option>`).join(''); await loadOutcome(); } catch (error) { status().innerHTML = `<div class="corrigendum-empty">Outcome unavailable: ${esc(error.message)}</div>`; } }
  async function save() { if (!state.canRecord || !state.tenderId) return; const button = field('btnSaveBidOutcome'); button.disabled = true; try { await window.TenderApiService.saveBidOutcome(state.tenderId, { status: field('bidOutcomeValue').value, submission_reference: field('bidOutcomeReference').value.trim() || null, submitted_at: field('bidOutcomeSubmittedAt').value || null, outcome_date: field('bidOutcomeDate').value || null, awarded_contract_value: field('bidOutcomeValueBdt').value === '' ? null : Number(field('bidOutcomeValueBdt').value), lessons_learned: field('bidOutcomeLessons').value.trim() || null }); await loadOutcome(); window.refreshSharedPipeline?.(); window.refreshOutcomeLearningDashboard?.(); window.refreshBidActivityTimeline?.(); } catch (error) { alert(`Could not save outcome: ${error.message}`); } finally { button.disabled = false; } }
  document.addEventListener('DOMContentLoaded', () => { field('bidOutcomeTenderSelect')?.addEventListener('change', event => { state.tenderId = event.target.value; loadOutcome(); }); field('btnSaveBidOutcome')?.addEventListener('click', save); window.tenderStore?.subscribe('authChange', loadPipeline); window.refreshBidOutcome = loadPipeline; loadPipeline(); });
}());
