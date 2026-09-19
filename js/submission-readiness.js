/* Presentation for the server-enforced bid submission gate. */
(function () {
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c]));
  const state = { tenderId: '' };
  function render(readiness) {
    const target = document.getElementById('submissionReadinessChecks');
    if (!target) return;
    target.innerHTML = `<div class="submission-readiness-result ${readiness.ready ? 'submission-ready' : 'submission-blocked'}"><strong>${readiness.ready ? 'Ready to submit' : 'Submission blocked'}</strong><span>${readiness.ready ? 'All release controls have passed.' : 'Complete the failed checks before setting the pipeline stage to Submitted.'}</span></div>` + readiness.checks.map(check => `<div class="submission-check ${check.passed ? 'check-passed' : 'check-failed'}"><span>${check.passed ? '✓' : '!'}</span><div><strong>${esc(check.label)}</strong>${check.items?.length ? `<small>${esc(check.items.join(', '))}</small>` : ''}</div></div>`).join('');
  }
  async function load() {
    const target = document.getElementById('submissionReadinessChecks');
    if (!target || !state.tenderId || !window.TenderApiService) return;
    if (!localStorage.getItem('tenderpulse_access_token')) { target.innerHTML = '<div class="corrigendum-empty">Sign in to check submission readiness.</div>'; return; }
    target.innerHTML = '<div class="corrigendum-empty">Checking server-side submission controls…</div>';
    try { render((await window.TenderApiService.getSubmissionReadiness(state.tenderId)).readiness); }
    catch (error) { target.innerHTML = `<div class="corrigendum-empty">Submission check unavailable: ${esc(error.message)}</div>`; }
  }
  async function loadPipeline() {
    const select = document.getElementById('submissionReadinessTenderSelect'), target = document.getElementById('submissionReadinessChecks');
    if (!select || !target || !window.TenderApiService) return;
    if (!localStorage.getItem('tenderpulse_access_token')) { select.innerHTML = '<option>Sign in required</option>'; target.innerHTML = '<div class="corrigendum-empty">Sign in to check submission readiness.</div>'; return; }
    try { const items = (await window.TenderApiService.getBidPipeline()).items || []; if (!items.length) { select.innerHTML = '<option>No pipeline tender available</option>'; target.innerHTML = '<div class="corrigendum-empty">Add a tender to the shared pipeline first.</div>'; return; } if (!items.some(item => item.tender_id === state.tenderId)) state.tenderId = items[0].tender_id; select.innerHTML = items.map(item => `<option value="${esc(item.tender_id)}" ${item.tender_id === state.tenderId ? 'selected' : ''}>${esc(item.tender_id)} — ${esc(item.tender_title)}</option>`).join(''); await load(); }
    catch (error) { target.innerHTML = `<div class="corrigendum-empty">Submission check unavailable: ${esc(error.message)}</div>`; }
  }
  document.addEventListener('DOMContentLoaded', () => { document.getElementById('submissionReadinessTenderSelect')?.addEventListener('change', event => { state.tenderId = event.target.value; load(); }); document.getElementById('btnRefreshSubmissionReadiness')?.addEventListener('click', load); window.tenderStore?.subscribe('authChange', loadPipeline); window.refreshSubmissionReadiness = loadPipeline; loadPipeline(); });
}());
