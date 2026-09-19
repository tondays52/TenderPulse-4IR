/* Durable, team-visible preparation tasks for a pipeline tender. */
(function () {
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' }[c]));
  const statuses = ['open', 'in_progress', 'blocked', 'done'];
  const state = { pipeline: [], tenderId: '' };
  const list = () => document.getElementById('sharedPreparationTaskList');
  const tenderSelect = () => document.getElementById('preparationTaskTenderSelect');
  const hasSession = () => Boolean(localStorage.getItem('tenderpulse_access_token'));

  function renderTasks(items) {
    const target = list();
    if (!target) return;
    if (!items.length) { target.innerHTML = '<div class="corrigendum-empty">No shared preparation tasks yet. Assign the first concrete task above.</div>'; return; }
    target.innerHTML = items.map(task => `<article class="shared-preparation-task" data-task-id="${task.id}">
      <div class="shared-preparation-task-title"><strong>${esc(task.title)}</strong><span class="preparation-status status-${esc(task.status)}">${esc(task.status.replace(/_/g, ' '))}</span></div>
      <div class="shared-preparation-fields">
        <label>Status<select data-field="status">${statuses.map(s => `<option value="${s}" ${s === task.status ? 'selected' : ''}>${s.replace(/_/g, ' ')}</option>`).join('')}</select></label>
        <label>Owner email<input data-field="owner_email" type="email" maxlength="256" value="${esc(task.owner_email || '')}" placeholder="owner@company.com"></label>
        <label>Task due<input data-field="due_date" type="datetime-local" value="${esc(task.due_date || '')}"></label>
        <label class="task-required-toggle"><input data-field="is_required" type="checkbox" ${task.is_required ? 'checked' : ''}> Required for submission</label>
        <label class="shared-wide">Blocker<input data-field="blocker" maxlength="4000" value="${esc(task.blocker || '')}" placeholder="Describe what is blocking this task, if anything"></label>
      </div>
      <div class="task-evidence"><label>Evidence<input data-attachment-file type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"></label><button class="btn-secondary task-evidence-upload" type="button">Upload evidence</button><div class="task-evidence-list">${(task.attachments || []).length ? task.attachments.map(attachment => `<button class="task-evidence-download" type="button" data-attachment-id="${attachment.id}" title="Download evidence">${esc(attachment.original_name)} <small>(${Math.max(1, Math.round(attachment.size_bytes / 1024))} KB)</small></button>`).join('') : '<span>No evidence attached</span>'}</div></div>
      <button class="btn-secondary shared-preparation-save" type="button">Save task</button>
    </article>`).join('');
  }

  async function loadTasks() {
    const target = list();
    if (!target || !state.tenderId) return;
    target.innerHTML = '<div class="corrigendum-empty">Loading preparation tasks…</div>';
    try { renderTasks((await window.TenderApiService.getBidPreparationTasks(state.tenderId)).items || []); }
    catch (error) { target.innerHTML = `<div class="corrigendum-empty">Preparation tasks unavailable: ${esc(error.message)}</div>`; }
  }

  async function loadPipeline() {
    const select = tenderSelect(), target = list();
    if (!select || !target || !window.TenderApiService) return;
    if (!hasSession()) { select.innerHTML = '<option>Sign in required</option>'; target.innerHTML = '<div class="corrigendum-empty">Sign in to manage shared preparation tasks.</div>'; return; }
    try {
      state.pipeline = (await window.TenderApiService.getBidPipeline()).items || [];
      if (!state.pipeline.length) { select.innerHTML = '<option value="">No pipeline tender available</option>'; target.innerHTML = '<div class="corrigendum-empty">Add an opportunity to the team bid pipeline first.</div>'; return; }
      if (!state.pipeline.some(item => item.tender_id === state.tenderId)) state.tenderId = state.pipeline[0].tender_id;
      select.innerHTML = state.pipeline.map(item => `<option value="${esc(item.tender_id)}" ${item.tender_id === state.tenderId ? 'selected' : ''}>${esc(item.tender_id)} — ${esc(item.tender_title)}</option>`).join('');
      await loadTasks();
    } catch (error) { target.innerHTML = `<div class="corrigendum-empty">Shared workflow unavailable: ${esc(error.message)}</div>`; }
  }

  document.addEventListener('DOMContentLoaded', () => {
    tenderSelect()?.addEventListener('change', event => { state.tenderId = event.target.value; loadTasks(); });
    document.getElementById('btnAddPreparationTask')?.addEventListener('click', async () => {
      const title = document.getElementById('preparationTaskTitle'), owner = document.getElementById('preparationTaskOwner'), dueDate = document.getElementById('preparationTaskDueDate'), required = document.getElementById('preparationTaskRequired');
      if (!state.tenderId || !title?.value.trim()) { title?.focus(); return; }
      try { await window.TenderApiService.addBidPreparationTask(state.tenderId, { title: title.value.trim(), owner_email: owner.value.trim() || null, due_date: dueDate.value || null, is_required: required.checked }); title.value = ''; owner.value = ''; dueDate.value = ''; required.checked = true; await loadTasks(); window.refreshCorrigendumNotifications?.(); window.refreshBidActivityTimeline?.(); window.refreshSubmissionReadiness?.(); window.refreshSubmissionApproval?.(); }
      catch (error) { alert(`Could not add task: ${error.message}`); }
    });
    list()?.addEventListener('click', async event => {
      const download = event.target.closest('.task-evidence-download');
      if (download) { try { await window.TenderApiService.downloadBidTaskAttachment(download.dataset.attachmentId); } catch (error) { alert(error.message); } return; }
      const upload = event.target.closest('.task-evidence-upload');
      if (upload) {
        const task = upload.closest('[data-task-id]'), file = task.querySelector('[data-attachment-file]').files[0];
        if (!file) { task.querySelector('[data-attachment-file]').focus(); return; }
        upload.disabled = true; upload.textContent = 'Uploading…';
        try { await window.TenderApiService.uploadBidTaskAttachment(task.dataset.taskId, file); await loadTasks(); window.refreshBidActivityTimeline?.(); window.refreshSubmissionReadiness?.(); window.refreshSubmissionApproval?.(); }
        catch (error) { alert(`Could not upload evidence: ${error.message}`); upload.disabled = false; upload.textContent = 'Upload evidence'; }
        return;
      }
      const button = event.target.closest('.shared-preparation-save'); if (!button) return;
      const task = button.closest('[data-task-id]'); const field = name => task.querySelector(`[data-field="${name}"]`).value;
      button.disabled = true;
      try { await window.TenderApiService.updateBidPreparationTask(task.dataset.taskId, { status: field('status'), owner_email: field('owner_email'), due_date: field('due_date'), is_required: task.querySelector('[data-field="is_required"]').checked, blocker: field('blocker') }); button.textContent = 'Saved'; setTimeout(() => { button.textContent = 'Save task'; button.disabled = false; }, 1000); await loadTasks(); window.refreshCorrigendumNotifications?.(); window.refreshBidActivityTimeline?.(); window.refreshSubmissionReadiness?.(); window.refreshSubmissionApproval?.(); }
      catch (error) { button.disabled = false; button.textContent = 'Save failed'; }
    });
    window.tenderStore?.subscribe('authChange', loadPipeline);
    window.refreshSharedPreparationTasks = loadPipeline;
    loadPipeline();
  });
}());
