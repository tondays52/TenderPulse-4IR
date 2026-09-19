/* In-app alerts for unreviewed procurement amendments. No external delivery is attempted. */
(function () {
  const MAX_ITEMS = 5;
  let alerts = [];
  let preferences = { agencies: [], alert_types: ['closing_date', 'tender_security'], deadline_window_hours: 72, requested_external_channel: 'in_app' };
  let teamPolicy = null;

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));

  function parseDeadline(value) {
    if (!value) return null;
    const direct = new Date(value);
    if (!Number.isNaN(direct.getTime())) return direct;
    const match = String(value).match(/(\d{1,2})[-/ ]([A-Za-z]{3,9})[-/ ](\d{4})(?:\s+(\d{1,2}):(\d{2}))?/);
    if (!match) return null;
    const months = { jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5, jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11 };
    const month = months[match[2].slice(0, 3).toLowerCase()];
    if (month === undefined) return null;
    return new Date(Number(match[3]), month, Number(match[1]), Number(match[4] || 23), Number(match[5] || 59));
  }

  function deadlineLabel(alert) {
    if (alert.field_changed !== 'closing_date') return 'Security amendment needs review';
    const deadline = parseDeadline(alert.new_value);
    if (!deadline) return 'Deadline amendment needs review';
    const hours = Math.round((deadline.getTime() - Date.now()) / 3600000);
    if (hours < 0) return 'Deadline has passed';
    if (hours <= 72) return `Deadline in ${hours < 24 ? `${hours}h` : `${Math.ceil(hours / 24)} days`}`;
    return `New deadline: ${deadline.toLocaleDateString()}`;
  }

  function taskReminderLabel(alert) {
    return `${(alert.reasons || []).join(' · ')}${alert.due_date ? ` · due ${new Date(alert.due_date).toLocaleString()}` : ''}`;
  }

  function isAlertEnabled(alert) {
    if (!preferences.alert_types.includes(alert.field_changed)) return false;
    if (preferences.agencies.length) {
      const agency = String(alert.agency || '').toUpperCase();
      const matchesAgency = preferences.agencies.some(selected => agency.includes(selected.toUpperCase()) || selected.toUpperCase().includes(agency));
      if (!matchesAgency) return false;
    }
    if (alert.field_changed !== 'closing_date') return true;
    const deadline = parseDeadline(alert.new_value);
    if (!deadline) return true;
    const hours = (deadline.getTime() - Date.now()) / 3600000;
    return hours >= 0 && hours <= preferences.deadline_window_hours;
  }

  function syncPreferenceControls() {
    document.querySelectorAll('input[name="alertAgency"]').forEach(input => { input.checked = preferences.agencies.includes(input.value); });
    document.querySelectorAll('input[name="alertType"]').forEach(input => { input.checked = preferences.alert_types.includes(input.value); });
    const deadline = document.getElementById('alertDeadlineWindow');
    if (deadline) deadline.value = String(preferences.deadline_window_hours);
    const channel = document.querySelector(`input[name="alertDelivery"][value="${preferences.requested_external_channel}"]`);
    if (channel) channel.checked = true;
    const status = document.getElementById('alertPreferenceStatus');
    if (status) {
      if (preferences.source === 'team_default') status.textContent = 'Using team defaults';
      else status.textContent = preferences.external_delivery_active ? 'External delivery active' : 'Personal in-app settings';
    }
  }

  function readPreferenceControls() {
    return {
      agencies: [...document.querySelectorAll('input[name="alertAgency"]:checked')].map(input => input.value),
      alert_types: [...document.querySelectorAll('input[name="alertType"]:checked')].map(input => input.value),
      deadline_window_hours: Number(document.getElementById('alertDeadlineWindow')?.value || 72),
      requested_external_channel: document.querySelector('input[name="alertDelivery"]:checked')?.value || 'in_app'
    };
  }

  async function loadPreferences() {
    if (!localStorage.getItem('tenderpulse_access_token') || !window.TenderApiService) return;
    try {
      const data = await window.TenderApiService.getAlertPreferences();
      preferences = { ...preferences, ...(data.preferences || {}) };
      syncPreferenceControls();
    } catch (_) {
      // The notification tray will remain on safe defaults until the next authenticated refresh.
    }
  }

  async function savePreferences() {
    const message = document.getElementById('alertPreferenceSaveMessage');
    const button = document.getElementById('btnSaveAlertPreferences');
    const next = readPreferenceControls();
    if (!next.alert_types.length) {
      if (message) message.textContent = 'Select at least one amendment type.';
      return;
    }
    button.disabled = true;
    if (message) message.textContent = 'Saving…';
    try {
      const data = await window.TenderApiService.saveAlertPreferences(next);
      preferences = { ...preferences, ...data.preferences };
      syncPreferenceControls();
      if (message) message.textContent = data.message || 'Preferences saved.';
      await refreshNotifications();
    } catch (error) {
      if (message) message.textContent = `Could not save: ${error.message}`;
    } finally {
      button.disabled = false;
    }
  }

  function syncTeamPolicyControls() {
    if (!teamPolicy) return;
    document.querySelectorAll('input[name="teamAlertAgency"]').forEach(input => { input.checked = teamPolicy.agencies.includes(input.value); });
    document.querySelectorAll('input[name="teamAlertType"]').forEach(input => { input.checked = teamPolicy.alert_types.includes(input.value); });
    const deadline = document.getElementById('teamAlertDeadlineWindow');
    if (deadline) deadline.value = String(teamPolicy.deadline_window_hours);
    const channel = document.querySelector(`input[name="teamAlertDelivery"][value="${teamPolicy.requested_external_channel}"]`);
    if (channel) channel.checked = true;
  }

  function readTeamPolicyControls() {
    return {
      agencies: [...document.querySelectorAll('input[name="teamAlertAgency"]:checked')].map(input => input.value),
      alert_types: [...document.querySelectorAll('input[name="teamAlertType"]:checked')].map(input => input.value),
      deadline_window_hours: Number(document.getElementById('teamAlertDeadlineWindow')?.value || 72),
      requested_external_channel: document.querySelector('input[name="teamAlertDelivery"]:checked')?.value || 'in_app'
    };
  }

  async function loadTeamPolicy() {
    const panel = document.getElementById('teamAlertPolicyPanel');
    if (!localStorage.getItem('tenderpulse_access_token') || !window.TenderApiService) {
      if (panel) panel.hidden = true;
      return;
    }
    try {
      const data = await window.TenderApiService.getTeamAlertPolicy();
      if (panel) panel.hidden = !data.can_manage;
      if (!data.can_manage) return;
      teamPolicy = data.policy;
      syncTeamPolicyControls();
      const status = document.getElementById('teamAlertPolicyStatus');
      if (status) status.textContent = data.updated_at ? `Last updated ${new Date(data.updated_at).toLocaleString()}` : 'Default policy';
    } catch (_) {
      if (panel) panel.hidden = true;
    }
  }

  async function saveTeamPolicy() {
    const message = document.getElementById('teamAlertPolicySaveMessage');
    const button = document.getElementById('btnSaveTeamAlertPolicy');
    const next = readTeamPolicyControls();
    if (!next.alert_types.length) {
      if (message) message.textContent = 'Select at least one amendment type.';
      return;
    }
    button.disabled = true;
    if (message) message.textContent = 'Saving team defaults…';
    try {
      const data = await window.TenderApiService.saveTeamAlertPolicy(next);
      teamPolicy = data.policy;
      syncTeamPolicyControls();
      if (message) message.textContent = data.message || 'Team defaults saved.';
      await loadPreferences();
      await refreshNotifications();
    } catch (error) {
      if (message) message.textContent = `Could not save: ${error.message}`;
    } finally {
      button.disabled = false;
    }
  }

  function render() {
    const badge = document.getElementById('corrigendumUnreadBadge');
    const items = document.getElementById('corrigendumNotificationItems');
    const summary = document.getElementById('corrigendumNotificationSummary');
    if (!badge || !items || !summary) return;
    badge.hidden = alerts.length === 0;
    badge.textContent = alerts.length > 99 ? '99+' : String(alerts.length);
    const taskAlerts = alerts.filter(a => a.kind === 'preparation_task');
    const urgent = alerts.filter(a => a.field_changed === 'closing_date' && /^Deadline in/.test(deadlineLabel(a))).length;
    summary.textContent = alerts.length ? `${alerts.length} action item${alerts.length === 1 ? '' : 's'} · ${taskAlerts.length} shared task${taskAlerts.length === 1 ? '' : 's'} need attention` : 'No unread team alerts';
    if (!alerts.length) {
      items.innerHTML = '<div class="notification-tray-empty">No unread team alerts.</div>';
      return;
    }
    items.innerHTML = alerts.slice(0, MAX_ITEMS).map(alert => alert.kind === 'preparation_task'
      ? `<button type="button" class="notification-tray-item" data-task-tender="${escapeHtml(alert.tender_id)}"><strong>Task: ${escapeHtml(alert.task_title)} · Tender ${escapeHtml(alert.tender_id)}</strong><small>${escapeHtml(taskReminderLabel(alert))}</small></button>`
      : `<button type="button" class="notification-tray-item" data-alert-id="${Number(alert.id)}"><strong>${escapeHtml(alert.agency)} · Tender ${escapeHtml(alert.tender_id)}</strong><small>${escapeHtml(deadlineLabel(alert))}</small></button>`).join('');
  }

  async function refreshNotifications() {
    const token = localStorage.getItem('tenderpulse_access_token');
    if (!token || !window.TenderApiService) {
      alerts = [];
      render();
      return;
    }
    try {
      const [corrigenda, tasks] = await Promise.all([
        window.TenderApiService.getCorrigendumReviewQueue({ status: 'open', limit: '200' }),
        window.TenderApiService.getBidPreparationTaskReminders()
      ]);
      alerts = [...(corrigenda.alerts || []).filter(isAlertEnabled), ...(tasks.reminders || [])];
      render();
    } catch (_) {
      alerts = [];
      render();
    }
  }

  function openReviewQueue(alertId) {
    window.switchTab?.('mining-view');
    const status = document.getElementById('corrigendumStatusFilter');
    if (status) status.value = 'open';
    document.getElementById('corrigendumNotificationTray').hidden = true;
    document.getElementById('btnCorrigendumNotifications').setAttribute('aria-expanded', 'false');
    window.refreshCorrigendumReviewQueue?.();
    window.setTimeout(() => document.querySelector(`[data-alert-id="${alertId}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 200);
  }

  function openTaskBoard(tenderId) {
    window.switchTab?.('tracker-view');
    document.getElementById('corrigendumNotificationTray').hidden = true;
    document.getElementById('btnCorrigendumNotifications').setAttribute('aria-expanded', 'false');
    window.refreshSharedPreparationTasks?.();
    window.setTimeout(() => document.querySelector('#sharedPreparationTitle')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 200);
  }

  document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('btnCorrigendumNotifications');
    const tray = document.getElementById('corrigendumNotificationTray');
    const items = document.getElementById('corrigendumNotificationItems');
    button?.addEventListener('click', () => {
      tray.hidden = !tray.hidden;
      button.setAttribute('aria-expanded', String(!tray.hidden));
      if (!tray.hidden) refreshNotifications();
    });
    document.getElementById('btnOpenCorrigendumQueue')?.addEventListener('click', () => openReviewQueue(''));
    document.getElementById('btnSaveAlertPreferences')?.addEventListener('click', savePreferences);
    document.getElementById('btnSaveTeamAlertPolicy')?.addEventListener('click', saveTeamPolicy);
    items?.addEventListener('click', event => {
      const item = event.target.closest('[data-alert-id]');
      if (item) openReviewQueue(item.dataset.alertId);
      const task = event.target.closest('[data-task-tender]');
      if (task) openTaskBoard(task.dataset.taskTender);
    });
    window.tenderStore?.subscribe('authChange', async () => { await loadTeamPolicy(); await loadPreferences(); await refreshNotifications(); });
    window.refreshCorrigendumNotifications = refreshNotifications;
    loadTeamPolicy().then(loadPreferences).then(refreshNotifications);
    window.setInterval(refreshNotifications, 60000);
  });
}());
