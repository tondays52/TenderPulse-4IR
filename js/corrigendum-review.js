/* TenderPulse corrigendum review queue — authenticated operator workflow. */
(function () {
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));

  const prettyField = (field) => ({
    closing_date: 'Submission deadline changed',
    tender_security: 'Tender security changed'
  }[field] || String(field || 'Tender detail changed').replace(/_/g, ' '));

  const formatDate = (value) => {
    if (!value) return 'Time unavailable';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  };

  const deadlineHint = (alert) => {
    if (alert.field_changed !== 'closing_date') return '';
    const deadline = new Date(alert.new_value);
    if (Number.isNaN(deadline.getTime())) return `New deadline: ${alert.new_value || 'not provided'}`;
    const hours = Math.round((deadline.getTime() - Date.now()) / 3600000);
    if (hours < 0) return 'Deadline has passed';
    return hours <= 72 ? `Deadline in ${hours < 24 ? `${hours}h` : `${Math.ceil(hours / 24)} days`}` : `New deadline: ${deadline.toLocaleDateString()}`;
  };

  function elements() {
    return {
      queue: document.getElementById('corrigendumReviewQueue'),
      summary: document.getElementById('corrigendumQueueSummary'),
      status: document.getElementById('corrigendumStatusFilter'),
      severity: document.getElementById('corrigendumSeverityFilter'),
      agency: document.getElementById('corrigendumAgencyFilter'),
      refresh: document.getElementById('btnRefreshCorrigendumQueue')
    };
  }

  function render(alerts) {
    const { queue, summary } = elements();
    if (!queue) return;
    if (summary) summary.textContent = `${alerts.length} actionable alert${alerts.length === 1 ? '' : 's'}`;
    if (!alerts.length) {
      queue.innerHTML = '<div class="corrigendum-empty">No alerts match this queue. Try “All alerts” to view completed reviews.</div>';
      return;
    }
    queue.innerHTML = alerts.map(alert => {
      const reviewed = alert.review_status === 'reviewed';
      const statusLabel = alert.review_status === 'open' ? 'OPEN' : alert.review_status.toUpperCase();
      return `<article class="corrigendum-alert" data-alert-id="${Number(alert.id)}">
        <div class="corrigendum-alert-head">
          <div>
            <div class="corrigendum-alert-title">${escapeHtml(prettyField(alert.field_changed))} · Tender ${escapeHtml(alert.tender_id)}</div>
            <div class="corrigendum-alert-meta">${escapeHtml(alert.agency)} · detected ${escapeHtml(formatDate(alert.detected_at))}${deadlineHint(alert) ? ` · <strong>${escapeHtml(deadlineHint(alert))}</strong>` : ''}</div>
          </div>
          <div style="display:flex; gap:.35rem; flex-wrap:wrap; justify-content:flex-end;">
            <span class="severity-badge severity-${String(alert.severity).toLowerCase()}">${escapeHtml(alert.severity)} PRIORITY</span>
            <span class="review-status-badge ${reviewed ? 'reviewed-badge' : ''}">${escapeHtml(statusLabel)}</span>
          </div>
        </div>
        <div class="corrigendum-change"><span class="corrigendum-old">${escapeHtml(alert.old_value || 'Not recorded')}</span><span class="corrigendum-arrow">→</span><span class="corrigendum-new">${escapeHtml(alert.new_value || 'Not recorded')}</span></div>
        <p class="corrigendum-alert-reason">${escapeHtml(alert.reason || alert.tender_title || 'Official procurement amendment detected.')}</p>
        <div class="corrigendum-alert-actions">
          <input class="corrigendum-review-note" maxlength="1000" aria-label="Review note for tender ${escapeHtml(alert.tender_id)}" placeholder="Optional operator note" value="${escapeHtml(alert.review_note || '')}">
          ${reviewed ? '' : '<button class="btn-secondary" type="button" data-review-action="acknowledged">Acknowledge</button>'}
          <button class="btn-primary" type="button" data-review-action="reviewed">${reviewed ? 'Update review' : 'Mark reviewed'}</button>
        </div>
      </article>`;
    }).join('');
  }

  async function loadQueue() {
    const { queue, summary, status, severity, agency, refresh } = elements();
    if (!queue || !window.TenderApiService) return;
    const token = localStorage.getItem('tenderpulse_access_token');
    if (!token) {
      queue.innerHTML = '<div class="corrigendum-empty">Sign in with an Analyst, Executive, Auditor, or Administrator account to review alerts.</div>';
      if (summary) summary.textContent = 'Authentication required';
      return;
    }
    if (refresh) refresh.disabled = true;
    queue.innerHTML = '<div class="corrigendum-empty">Loading corrigendum review queue…</div>';
    try {
      const data = await window.TenderApiService.getCorrigendumReviewQueue({
        status: status?.value || 'open', severity: severity?.value || '', agency: agency?.value.trim() || '', limit: '100'
      });
      render(data.alerts || []);
    } catch (error) {
      queue.innerHTML = `<div class="corrigendum-empty">Unable to load the review queue: ${escapeHtml(error.message)}.</div>`;
      if (summary) summary.textContent = 'Queue unavailable';
    } finally {
      if (refresh) refresh.disabled = false;
    }
  }

  async function saveReview(event) {
    const button = event.target.closest('[data-review-action]');
    if (!button) return;
    const card = button.closest('[data-alert-id]');
    const note = card.querySelector('.corrigendum-review-note')?.value || '';
    button.disabled = true;
    try {
      await window.TenderApiService.reviewCorrigendum(card.dataset.alertId, button.dataset.reviewAction, note);
      await loadQueue();
    } catch (error) {
      button.disabled = false;
      window.alert(`Review update failed: ${error.message}`);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const { queue, status, severity, agency, refresh } = elements();
    refresh?.addEventListener('click', loadQueue);
    status?.addEventListener('change', loadQueue);
    severity?.addEventListener('change', loadQueue);
    agency?.addEventListener('search', loadQueue);
    agency?.addEventListener('change', loadQueue);
    queue?.addEventListener('click', saveReview);
    window.refreshCorrigendumReviewQueue = loadQueue;
    loadQueue();
    window.tenderStore?.subscribe('authChange', loadQueue);
  });
}());
