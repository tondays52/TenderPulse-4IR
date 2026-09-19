/* Read-only, append-only team audit timeline for bid workflow changes. */
(function () {
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c]));
  function render(events) {
    const target = document.getElementById('bidActivityTimelineItems');
    if (!target) return;
    if (!events.length) { target.innerHTML = '<div class="corrigendum-empty">No shared workflow activity recorded yet.</div>'; return; }
    target.innerHTML = events.map(event => `<article class="bid-activity-item"><span class="bid-activity-dot"></span><div><strong>${esc(event.summary)}</strong><p>${esc(event.tender_id)} · ${esc(event.actor_email || 'System')} · ${event.created_at ? new Date(event.created_at).toLocaleString() : 'time unavailable'}</p></div></article>`).join('');
  }
  async function load() {
    const target = document.getElementById('bidActivityTimelineItems');
    if (!target || !window.TenderApiService) return;
    if (!localStorage.getItem('tenderpulse_access_token')) { target.innerHTML = '<div class="corrigendum-empty">Sign in to view team activity.</div>'; return; }
    target.innerHTML = '<div class="corrigendum-empty">Loading team activity…</div>';
    try { render((await window.TenderApiService.getBidActivity({ limit: '50' })).events || []); }
    catch (error) { target.innerHTML = `<div class="corrigendum-empty">Activity unavailable: ${esc(error.message)}</div>`; }
  }
  document.addEventListener('DOMContentLoaded', () => { document.getElementById('btnRefreshBidActivity')?.addEventListener('click', load); window.tenderStore?.subscribe('authChange', load); window.refreshBidActivityTimeline = load; load(); });
}());
