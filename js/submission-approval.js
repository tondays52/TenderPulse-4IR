/* Authorized bid submission sign-off, independently enforced by the server. */
(function () {
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c]));
  const state = { tenderId: '', canSign: false };
  const target = () => document.getElementById('submissionApprovalStatus');
  function render(data) {
    const approval = data.approval || { status: 'pending', valid: false };
    const status = approval.valid ? 'approval-valid' : approval.status === 'rejected' ? 'approval-rejected' : 'approval-pending';
    target().innerHTML = `<div class="approval-result ${status}"><strong>${approval.valid ? 'Approved and current' : approval.status === 'rejected' ? 'Rejected' : approval.status === 'approved' ? 'Approval stale — re-approval required' : 'Awaiting approval'}</strong><span>${approval.signed_by ? `Signed by ${esc(approval.signed_by)}${approval.signed_at ? ` · ${new Date(approval.signed_at).toLocaleString()}` : ''}` : data.base_ready ? 'Ready for Executive or Admin sign-off.' : 'Resolve readiness checks before approval.'}</span>${approval.note ? `<small>${esc(approval.note)}</small>` : ''}</div>`;
    const controls = document.getElementById('submissionApprovalControls'); controls.hidden = !data.can_sign; state.canSign = Boolean(data.can_sign);
    document.getElementById('submissionApprovalNote').value = approval.note || '';
    const download = document.getElementById('btnDownloadSubmissionPack'); download.disabled = !approval.valid;
  }
  async function loadApproval() {
    if (!state.tenderId || !window.TenderApiService || !localStorage.getItem('tenderpulse_access_token')) return;
    target().innerHTML = '<div class="corrigendum-empty">Loading submission approval…</div>';
    try { render(await window.TenderApiService.getSubmissionApproval(state.tenderId)); }
    catch (error) { target().innerHTML = `<div class="corrigendum-empty">Approval unavailable: ${esc(error.message)}</div>`; }
  }
  async function loadPipeline() {
    const select = document.getElementById('submissionApprovalTenderSelect'); if (!select || !window.TenderApiService) return;
    if (!localStorage.getItem('tenderpulse_access_token')) { select.innerHTML = '<option>Sign in required</option>'; return; }
    try { const items = (await window.TenderApiService.getBidPipeline()).items || []; if (!items.length) { select.innerHTML = '<option>No pipeline tender available</option>'; target().innerHTML = '<div class="corrigendum-empty">Add a tender to the shared pipeline first.</div>'; return; } if (!items.some(item => item.tender_id === state.tenderId)) state.tenderId = items[0].tender_id; select.innerHTML = items.map(item => `<option value="${esc(item.tender_id)}" ${item.tender_id === state.tenderId ? 'selected' : ''}>${esc(item.tender_id)} — ${esc(item.tender_title)}</option>`).join(''); await loadApproval(); }
    catch (error) { target().innerHTML = `<div class="corrigendum-empty">Approval unavailable: ${esc(error.message)}</div>`; }
  }
  async function sign(status) {
    const button = status === 'approved' ? document.getElementById('btnApproveSubmission') : document.getElementById('btnRejectSubmission'); if (!state.canSign || !state.tenderId) return;
    button.disabled = true;
    try { await window.TenderApiService.saveSubmissionApproval(state.tenderId, { status, note: document.getElementById('submissionApprovalNote').value.trim() || null }); await loadApproval(); window.refreshSubmissionReadiness?.(); window.refreshBidActivityTimeline?.(); window.refreshSharedPipeline?.(); }
    catch (error) { alert(`Could not ${status === 'approved' ? 'approve' : 'reject'} submission: ${error.message}`); }
    finally { button.disabled = false; }
  }
  async function downloadPack() { const button = document.getElementById('btnDownloadSubmissionPack'); if (!state.tenderId || button.disabled) return; button.disabled = true; button.textContent = 'Preparing…'; try { await window.TenderApiService.downloadSubmissionPack(state.tenderId); window.refreshBidActivityTimeline?.(); } catch (error) { alert(error.message); } finally { button.textContent = 'Download final pack'; await loadApproval(); } }
  document.addEventListener('DOMContentLoaded', () => { document.getElementById('submissionApprovalTenderSelect')?.addEventListener('change', event => { state.tenderId = event.target.value; loadApproval(); }); document.getElementById('btnApproveSubmission')?.addEventListener('click', () => sign('approved')); document.getElementById('btnRejectSubmission')?.addEventListener('click', () => sign('rejected')); document.getElementById('btnDownloadSubmissionPack')?.addEventListener('click', downloadPack); window.tenderStore?.subscribe('authChange', loadPipeline); window.refreshSubmissionApproval = loadPipeline; loadPipeline(); });
}());
