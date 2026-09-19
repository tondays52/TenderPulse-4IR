(function () {
  const byId = (id) => document.getElementById(id);
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[character]));

  function renderRequirements(requirements) {
    const container = byId("documentRequirementResults");
    if (!container) return;
    if (!requirements.length) {
      container.innerHTML = "<p>No explicit clauses were found. Review the document text and try again.</p>";
      return;
    }
    container.innerHTML = requirements.map((item) => {
      const page = item.source_page ? ` · PDF page ${item.source_page}` : "";
      const reviewControls = item.status === "unreviewed"
        ? `<button class="btn-secondary" data-review="approved" data-id="${item.id}">Approve</button><button class="btn-secondary" data-review="rejected" data-id="${item.id}">Reject</button>`
        : "";
      const taskControl = item.status === "approved"
        ? `<button class="btn-primary" data-task="true" data-id="${item.id}">Create required task</button>`
        : "";
      return `<article class="outcome-learning-lesson" data-requirement-id="${item.id}"><strong>${escapeHtml(item.key.replace(/_/g, " "))}</strong><span class="requirement-status">${escapeHtml(item.status)}</span><small>Source${page}</small><p>${escapeHtml(item.source_excerpt)}</p><div class="document-requirement-actions">${reviewControls}${taskControl}</div></article>`;
    }).join("");
  }

  async function extractRequirements() {
    const tenderId = byId("documentRequirementTender")?.value;
    const text = byId("documentRequirementText")?.value.trim() || "";
    const file = byId("documentRequirementPdf")?.files?.[0] || null;
    if (!tenderId) throw new Error("Select a pipeline tender first.");
    if (!file && !text) throw new Error("Upload a PDF or paste tender text.");
    const result = await TenderApiService.extractDocumentRequirements(tenderId, text, file);
    renderRequirements(result.requirements || []);
  }

  async function handleActions(event) {
    const button = event.target.closest("button[data-review], button[data-task]");
    if (!button) return;
    const tenderId = byId("documentRequirementTender")?.value;
    const card = button.closest("[data-requirement-id]");
    if (!tenderId || !card) return;
    button.disabled = true;
    try {
      if (button.dataset.review) {
        await TenderApiService.reviewDocumentRequirement(button.dataset.id, button.dataset.review);
      } else {
        const excerpt = card.querySelector("p")?.textContent || "";
        const key = card.querySelector("strong")?.textContent || "Document requirement";
        await TenderApiService.createDocumentRequirementTask(tenderId, { title: `Document requirement: ${key}`, source_excerpt: excerpt });
        button.textContent = "Task created";
        return;
      }
      const response = await fetch(`/api/bid-pipeline/${encodeURIComponent(tenderId)}/document-requirements`, { headers: { Authorization: `Bearer ${localStorage.getItem("tenderpulse_access_token") || ""}` } });
      if (!response.ok) throw new Error("Unable to refresh document reviews.");
      const data = await response.json();
      renderRequirements(data.requirements || []);
    } finally {
      button.disabled = false;
    }
  }

  async function populateTenderSelector() {
    if (!localStorage.getItem("tenderpulse_access_token")) return;
    const response = await TenderApiService.getBidPipeline();
    const selector = byId("documentRequirementTender");
    if (selector) selector.innerHTML = (response.items || []).map((item) => `<option value="${escapeHtml(item.tender_id)}">${escapeHtml(item.tender_title)}</option>`).join("");
  }

  document.addEventListener("DOMContentLoaded", async () => {
    byId("btnExtractDocumentRequirements")?.addEventListener("click", () => extractRequirements().catch((error) => alert(error.message)));
    byId("documentRequirementResults")?.addEventListener("click", (event) => handleActions(event).catch((error) => alert(error.message)));
    try { await populateTenderSelector(); } catch (error) { console.warn("Document requirement selector could not be loaded", error); }
  });
}());
