(() => {
  const LAYOUT_KEY = "promptStudio.layout";
  const SHOW_DISABLED_KEY = "promptStudio.showDisabled";
  const LIBRARY_POLL_MS = 30000;

  const state = {
    view: "all",
    tag: null,
    q: "",
    layout: localStorage.getItem(LAYOUT_KEY) === "list" ? "list" : "cards",
    showDisabled: localStorage.getItem(SHOW_DISABLED_KEY) === "true",
    prompts: [],
    suites: [],
    libraryTotal: 0,
    libraryPath: null,
    libraryHelp: "",
    lastSeenModified: null,
    activePromptId: null,
    suitePickPromptId: null,
    activeSuiteId: null,
    editMode: false,
    editDraft: null,
    modalDetail: null,
  };

  const $ = (id) => document.getElementById(id);

  function optional(id) {
    return document.getElementById(id);
  }

  function bindClick(id, handler) {
    const el = optional(id);
    if (el) el.addEventListener("click", handler);
  }

  function showError(err) {
    const message = err && err.message ? err.message : String(err);
    alert(message);
  }

  function openRunSafe(promptId, startInEdit = false) {
    return openRun(promptId, startInEdit).catch(showError);
  }

  async function api(path, options = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || res.statusText);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  function debounce(fn, ms) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }

  const OUTPUT_FORMAT_OPTIONS = [
    { value: "chat_text", label: "Text" },
    { value: "json", label: "JSON" },
    { value: "excel_download", label: "Excel download" },
  ];

  const OUTPUT_FORMAT_VALUES = new Set(OUTPUT_FORMAT_OPTIONS.map((o) => o.value));

  function normalizeOutputFormat(value) {
    const key = (value || "chat_text").toLowerCase();
    return OUTPUT_FORMAT_VALUES.has(key) ? key : "chat_text";
  }

  function formatLabel(outputFormat) {
    const key = normalizeOutputFormat(outputFormat);
    const match = OUTPUT_FORMAT_OPTIONS.find((o) => o.value === key);
    return match ? match.label : "Text";
  }

  function formatWhen(iso) {
    if (!iso) return "Never";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function escapeAttr(s) {
    return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
  }

  function chipHtml(p) {
    const tags = p.tags || [];
    const maxTags = 3;
    const shown = tags.slice(0, maxTags);
    let html = shown.map((t) => `<span class="chip">${escapeHtml(t)}</span>`).join("");
    const extra = tags.length - shown.length;
    if (extra > 0) {
      html += `<span class="chip more">+${extra}</span>`;
    }
    return html;
  }

  function cardMetaHtml(p) {
    const fmt = formatLabel(p.output_format);
    const runs = p.run_count || 0;
    return `
      <div class="card-meta-line">
        <span class="format-badge">${escapeHtml(fmt)}</span>
        <span>${runs} run${runs === 1 ? "" : "s"}</span>
        <span class="meta-sep">·</span>
        <span>${escapeHtml(formatWhen(p.last_run_at))}</span>
      </div>`;
  }

  function secondaryActionsHtml(promptId) {
    return `
      <div class="action-menu">
        <button type="button" class="action-menu-toggle" data-menu-toggle="${promptId}"
                aria-haspopup="true" aria-expanded="false" title="More actions">⋯</button>
        <div class="action-menu-panel hidden" role="menu">
          <button type="button" role="menuitem" data-edit="${promptId}">Edit</button>
          <button type="button" role="menuitem" data-suite-add="${promptId}">Add to suite…</button>
          <button type="button" role="menuitem" class="danger" data-delete="${promptId}">Remove</button>
        </div>
      </div>`;
  }

  function disabledBadgeHtml(p) {
    return p.enabled === false ? `<span class="disabled-badge">Disabled</span>` : "";
  }

  function closeAllActionMenus() {
    document.querySelectorAll(".action-menu-panel").forEach((panel) => {
      panel.classList.add("hidden");
    });
    document.querySelectorAll(".action-menu-toggle").forEach((btn) => {
      btn.setAttribute("aria-expanded", "false");
    });
  }

  function syncLayoutButtons() {
    document.querySelectorAll(".layout-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.layout === state.layout);
    });
    const grid = $("promptGrid");
    grid.classList.toggle("prompt-grid", state.layout === "cards");
    grid.classList.toggle("prompt-list", state.layout === "list");
  }

  function setLayout(layout) {
    state.layout = layout === "list" ? "list" : "cards";
    localStorage.setItem(LAYOUT_KEY, state.layout);
    syncLayoutButtons();
    renderPrompts();
  }

  async function loadTags() {
    const data = await api("/api/tags");
    const el = $("tagList");
    el.innerHTML = "";
    data.tags.forEach(({ tag, count }) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tag-chip" + (state.tag === tag ? " active" : "");
      btn.textContent = `${tag} (${count})`;
      btn.addEventListener("click", () => {
        state.tag = state.tag === tag ? null : tag;
        state.view = "all";
        syncNav();
        loadPrompts();
        loadTags();
      });
      el.appendChild(btn);
    });
  }

  async function loadPrompts() {
    const params = new URLSearchParams();
    if (state.q) params.set("q", state.q);
    if (state.tag) params.set("tag", state.tag);
    if (state.view === "favorites") params.set("favorites_only", "true");
    if (state.showDisabled) params.set("include_disabled", "true");
    params.set("sort", "recent");
    const data = await api(`/api/prompts?${params}`);
    state.prompts = data.prompts || [];
    renderPrompts();
  }

  function updateResultCount() {
    const el = $("resultCount");
    const n = state.prompts.length;
    const filtered = Boolean(state.q || state.tag || state.view === "favorites");
    if (!filtered) {
      el.textContent = "";
      el.classList.add("hidden");
      return;
    }
    el.classList.remove("hidden");
    el.textContent = `${n} matching`;
  }

  function renderPrompts() {
    const grid = $("promptGrid");
    const empty = $("emptyState");
    updateResultCount();
    syncLayoutButtons();
    closeAllActionMenus();
    grid.innerHTML = "";
    if (!state.prompts.length) {
      empty.classList.remove("hidden");
      return;
    }
    empty.classList.add("hidden");

    if (state.layout === "list") {
      const head = document.createElement("div");
      head.className = "prompt-list-head";
      head.innerHTML = `
        <span>Title</span>
        <span>Format</span>
        <span>Runs</span>
        <span>Last run</span>
        <span>Actions</span>`;
      grid.appendChild(head);
    }

    state.prompts.forEach((p) => {
      if (state.layout === "list") {
        const row = document.createElement("article");
        row.className = "prompt-list-row" + (p.enabled === false ? " is-disabled" : "");
        row.innerHTML = `
          <div class="list-title-cell">
            <strong>${escapeHtml(p.title)}</strong>
            ${disabledBadgeHtml(p)}
            <div class="original-preview muted">${escapeHtml(p.original_preview || p.original_user_prompt || "(no original prompt recorded)")}</div>
            <div class="chip-row compact">${chipHtml(p)}</div>
          </div>
          <span class="format-badge">${escapeHtml(formatLabel(p.output_format))}</span>
          <span>${p.run_count || 0}</span>
          <span class="muted">${escapeHtml(formatWhen(p.last_run_at))}</span>
          <div class="list-actions">
            <button type="button" class="icon-btn ${p.favorite ? "starred" : ""}" data-fav="${p.id}" title="Favorite">★</button>
            <button type="button" class="btn-secondary" data-edit="${p.id}">Edit</button>
            <button type="button" class="btn-primary" data-run="${p.id}">Run</button>
            ${secondaryActionsHtml(p.id)}
          </div>`;
        grid.appendChild(row);
        return;
      }

      const card = document.createElement("article");
      card.className = "prompt-card" + (p.enabled === false ? " is-disabled" : "");
      card.innerHTML = `
        <div class="card-top">
          <h3 class="card-title">${escapeHtml(p.title)}</h3>
          <div class="card-top-actions">
            ${disabledBadgeHtml(p)}
            <button type="button" class="icon-btn ${p.favorite ? "starred" : ""}" data-fav="${p.id}" title="Favorite">★</button>
          </div>
        </div>
        <p class="original-preview">${escapeHtml(p.original_preview || p.original_user_prompt || "(no original prompt recorded)")}</p>
        <div class="chip-row">${chipHtml(p)}</div>
        ${cardMetaHtml(p)}
        <div class="card-actions">
          <button type="button" class="btn-secondary" data-edit="${p.id}">Edit</button>
          <button type="button" class="btn-primary" data-run="${p.id}">Run</button>
          ${secondaryActionsHtml(p.id)}
        </div>`;
      grid.appendChild(card);
    });
  }

  function syncNav() {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === state.view);
    });
    const titles = { all: "All prompts", favorites: "Favorites", suites: "Suites" };
    $("viewTitle").textContent = state.tag ? `Tag: ${state.tag}` : titles[state.view] || "All prompts";
    $("libraryView").classList.toggle("hidden", state.view === "suites");
    $("suitesView").classList.toggle("hidden", state.view !== "suites");
  }

  function stampUpdated(info) {
    const el = $("statusLine");
    const t = new Date().toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
    const enabled =
      info && typeof info.enabled_count === "number" ? info.enabled_count : state.libraryTotal;
    const total = info && typeof info.total_count === "number" ? info.total_count : enabled;
    const disabled = info && typeof info.disabled_count === "number" ? info.disabled_count : 0;
    let label = total === 1 ? "1 prompt" : `${total} prompts`;
    if (disabled > 0) {
      label += ` (${disabled} disabled)`;
    }
    el.textContent = `Updated ${t} · ${label}`;
    const path = (info && info.path) || state.libraryPath;
    const mtime = info && info.last_modified;
    const help = (info && info.help) || state.libraryHelp;
    const lines = [];
    if (path) lines.push(path);
    if (mtime) lines.push(`Last write: ${mtime}`);
    if (help) lines.push(help);
    if (!info || info.exists === false) {
      lines.push("Library file missing — save a prompt via MCP first.");
    }
    el.title = lines.join("\n");
    if (info && info.path) state.libraryPath = info.path;
    if (info && info.help) state.libraryHelp = info.help;
    if (mtime) {
      if (state.lastSeenModified && mtime > state.lastSeenModified && !state.editMode) {
        showLibraryBanner();
      }
      state.lastSeenModified = mtime;
    }
  }

  function showLibraryBanner() {
    const banner = $("libraryBanner");
    if (!banner) return;
    banner.classList.remove("hidden");
    $("libraryBannerText").textContent =
      "Library updated on disk — reload to see new prompts from MCP.";
  }

  function hideLibraryBanner() {
    $("libraryBanner")?.classList.add("hidden");
  }

  async function pollLibraryInfo() {
    if (state.editMode) return;
    try {
      const info = await api("/api/library_info");
      if (info.last_modified && state.lastSeenModified && info.last_modified > state.lastSeenModified) {
        showLibraryBanner();
      }
    } catch {
      /* ignore background poll errors */
    }
  }

  function updateSidebarTotal(info) {
    const el = $("sidebarTotalCount");
    if (!el) return;
    const n = info && typeof info.total_count === "number" ? info.total_count : 0;
    el.textContent = String(n);
    state.libraryTotal = n;
    if (info && info.path) state.libraryPath = info.path;
  }

  async function refreshLibrary() {
    const [, , info] = await Promise.all([
      loadTags(),
      loadPrompts(),
      api("/api/library_info").catch(() => null),
    ]);
    updateSidebarTotal(info);
    stampUpdated(info);
    hideLibraryBanner();
  }

  async function refreshSuites() {
    await loadSuites();
    if (state.activeSuiteId) {
      await openSuite(state.activeSuiteId);
    }
    stampUpdated(null);
  }

  function setBlockExpanded(pre, btn, expanded) {
    pre.classList.toggle("is-collapsed", !expanded);
    btn.textContent = expanded ? "Show less" : "Show more";
    btn.setAttribute("aria-expanded", expanded ? "true" : "false");
  }

  function syncBlockToggle(preId, btnId) {
    const pre = optional(preId);
    const btn = optional(btnId);
    if (!pre || !btn) return;
    setBlockExpanded(pre, btn, false);
    btn.classList.toggle("hidden", pre.scrollHeight <= pre.clientHeight);
  }

  function renderVarFields(detail, editable) {
    const fields = $("varFields");
    fields.innerHTML = "";
    const placeholders = extractPlaceholdersFromDetail(detail);
    placeholders.forEach((name) => {
      const wrap = document.createElement("div");
      wrap.className = "var-field";

      if (name === "output_format") {
        const selected = normalizeOutputFormat(
          (detail.variables && detail.variables.output_format) || detail.output_format
        );
        wrap.innerHTML = `<label for="var_output_format">{{output_format}}</label>`;
        const select = document.createElement("select");
        select.id = "var_output_format";
        select.name = "output_format";
        select.disabled = editable;
        OUTPUT_FORMAT_OPTIONS.forEach(({ value, label }) => {
          const opt = document.createElement("option");
          opt.value = value;
          opt.textContent = label;
          opt.selected = value === selected;
          select.appendChild(opt);
        });
        if (!editable) {
          select.addEventListener("change", () => {
            $("modalFormatLabel").textContent = formatLabel(select.value);
          });
        }
        wrap.appendChild(select);
        fields.appendChild(wrap);
        return;
      }

      const hint = detail.variables && detail.variables[name] != null ? String(detail.variables[name]) : "";
      const recent = (detail.recent_values && detail.recent_values[name]) || [];
      wrap.innerHTML = `<label for="var_${name}">{{${name}}}</label>
        <input id="var_${name}" name="${name}" value="${escapeAttr(hint)}" list="dl_${name}" ${editable ? "readonly" : ""} />
        <datalist id="dl_${name}">${recent.map((v) => `<option value="${escapeAttr(v)}"></option>`).join("")}</datalist>`;
      if (recent.length && !editable) {
        const hints = document.createElement("div");
        hints.className = "recent-hints";
        recent.slice(0, 5).forEach((v) => {
          const b = document.createElement("button");
          b.type = "button";
          b.textContent = v.length > 40 ? v.slice(0, 40) + "…" : v;
          b.title = v;
          b.addEventListener("click", () => {
            wrap.querySelector("input").value = v;
          });
          hints.appendChild(b);
        });
        wrap.appendChild(hints);
      }
      fields.appendChild(wrap);
    });
  }

  function extractPlaceholdersFromDetail(detail) {
    if (detail.placeholders && detail.placeholders.length) {
      return detail.placeholders;
    }
    const text = detail.refined_prompt || "";
    const seen = new Set();
    const ordered = [];
    const re = /\{\{([a-z][a-z0-9_]*)\}\}/g;
    let match;
    while ((match = re.exec(text)) !== null) {
      if (!seen.has(match[1])) {
        seen.add(match[1]);
        ordered.push(match[1]);
      }
    }
    return ordered;
  }

  function setEditMode(enabled) {
    state.editMode = enabled;
    optional("modalTitleDisplay")?.classList.toggle("hidden", enabled);
    optional("modalTitleInput")?.classList.toggle("hidden", !enabled);
    optional("modalOriginal")?.classList.toggle("hidden", enabled);
    optional("modalOriginalEdit")?.classList.toggle("hidden", !enabled);
    optional("modalTemplate")?.classList.toggle("hidden", enabled);
    optional("modalTemplateEdit")?.classList.toggle("hidden", !enabled);
    optional("toggleOriginal")?.classList.toggle("hidden", enabled);
    optional("toggleTemplate")?.classList.toggle("hidden", enabled);
    optional("makeVarOriginalBtn")?.classList.toggle("hidden", !enabled);
    optional("makeVarTemplateBtn")?.classList.toggle("hidden", !enabled);
    optional("enabledToggleWrap")?.classList.toggle("hidden", !enabled);
    document.querySelectorAll(".run-only-block").forEach((el) => {
      el.classList.toggle("hidden", enabled);
    });
    document.querySelectorAll(".edit-only-block").forEach((el) => {
      el.classList.toggle("hidden", !enabled);
    });
    if (enabled && state.editDraft) {
      const titleInput = optional("modalTitleInput");
      const originalEdit = optional("modalOriginalEdit");
      const templateEdit = optional("modalTemplateEdit");
      const enabledToggle = optional("modalEnabledToggle");
      if (titleInput) titleInput.value = state.editDraft.title || "";
      if (originalEdit) originalEdit.value = state.editDraft.original_user_prompt || "";
      if (templateEdit) templateEdit.value = state.editDraft.refined_prompt || "";
      if (enabledToggle) enabledToggle.checked = state.editDraft.enabled !== false;
      renderVarFields(state.editDraft, true);
    }
  }

  function populateRunModal(detail) {
    state.modalDetail = detail;
    const titleDisplay = optional("modalTitleDisplay");
    const titleInput = optional("modalTitleInput");
    const originalPre = optional("modalOriginal");
    const originalEdit = optional("modalOriginalEdit");
    const templatePre = optional("modalTemplate");
    const templateEdit = optional("modalTemplateEdit");
    const generatedOut = optional("generatedOut");
    const formatLabelEl = optional("modalFormatLabel");
    const enabledToggle = optional("modalEnabledToggle");

    if (titleDisplay) titleDisplay.textContent = detail.title;
    if (titleInput) titleInput.value = detail.title || "";
    const originalText =
      detail.original_user_prompt && String(detail.original_user_prompt).trim()
        ? detail.original_user_prompt
        : "(not recorded)";
    if (originalPre) originalPre.textContent = originalText;
    if (originalEdit) originalEdit.value = detail.original_user_prompt || "";
    if (templatePre) templatePre.textContent = detail.refined_prompt;
    if (templateEdit) templateEdit.value = detail.refined_prompt || "";
    if (generatedOut) generatedOut.value = "";
    if (formatLabelEl) formatLabelEl.textContent = formatLabel(detail.output_format);
    if (enabledToggle) enabledToggle.checked = detail.enabled !== false;

    const meta = $("modalMeta");
    meta.innerHTML = "";
    (detail.tags || []).forEach((t) => {
      const span = document.createElement("span");
      span.className = "chip";
      span.textContent = t;
      meta.appendChild(span);
    });
    (detail.tools || []).forEach((t) => {
      const span = document.createElement("span");
      span.className = "chip tool";
      span.textContent = t;
      meta.appendChild(span);
    });

    $("modalStats").innerHTML = `
      <span><strong>Runs:</strong> ${detail.run_count || 0}</span>
      <span><strong>Last run:</strong> ${escapeHtml(formatWhen(detail.last_run_at))}</span>
      <span><strong>Created:</strong> ${escapeHtml(formatWhen(detail.created_at))}</span>
      <span><strong>Placeholders:</strong> ${extractPlaceholdersFromDetail(detail).length}</span>`;

    renderVarFields(detail, false);
  }

  async function openRun(promptId, startInEdit = false) {
    const detail = await api(`/api/prompts/${promptId}?include_disabled=true`);
    state.activePromptId = promptId;
    state.editDraft = {
      title: detail.title,
      original_user_prompt: detail.original_user_prompt || "",
      refined_prompt: detail.refined_prompt || "",
      variables: { ...(detail.variables || {}) },
      enabled: detail.enabled !== false,
      output_format: detail.output_format,
      placeholders: detail.placeholders || [],
      recent_values: detail.recent_values || {},
      tags: detail.tags || [],
      tools: detail.tools || [],
    };
    populateRunModal(detail);
    setEditMode(startInEdit);
    optional("runModal")?.showModal();
    if (!startInEdit) {
      syncBlockToggle("modalOriginal", "toggleOriginal");
      syncBlockToggle("modalTemplate", "toggleTemplate");
    }
  }

  function resetRunModalState() {
    if (state.editMode) {
      cancelEdit();
    } else {
      setEditMode(false);
    }
  }

  async function saveEdit() {
    if (!state.activePromptId || !state.editDraft) return;
    const variables = { ...(state.editDraft.variables || {}) };
    optional("varFields")?.querySelectorAll("input[name]").forEach((field) => {
      variables[field.name] = field.value;
    });
    const titleInput = optional("modalTitleInput");
    const originalEdit = optional("modalOriginalEdit");
    const templateEdit = optional("modalTemplateEdit");
    const enabledToggle = optional("modalEnabledToggle");
    const payload = {
      title: titleInput ? titleInput.value.trim() : state.editDraft.title,
      original_user_prompt: originalEdit
        ? originalEdit.value
        : state.editDraft.original_user_prompt,
      refined_prompt: templateEdit ? templateEdit.value : state.editDraft.refined_prompt,
      variables,
      enabled: enabledToggle ? enabledToggle.checked : state.editDraft.enabled !== false,
    };
    const updated = await api(`/api/prompts/${state.activePromptId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    state.editDraft = {
      title: updated.title,
      original_user_prompt: updated.original_user_prompt || "",
      refined_prompt: updated.refined_prompt || "",
      variables: { ...(updated.variables || {}) },
      enabled: updated.enabled !== false,
      output_format: updated.output_format,
      placeholders: updated.placeholders || [],
      recent_values: updated.recent_values || {},
      tags: updated.tags || [],
      tools: updated.tools || [],
    };
    populateRunModal(updated);
    setEditMode(false);
    await refreshLibrary();
  }

  function cancelEdit() {
    if (state.modalDetail) {
      populateRunModal(state.modalDetail);
    }
    setEditMode(false);
  }

  async function makeVariableFromField(field) {
    if (!state.activePromptId || !state.editDraft) return;
    const textarea =
      field === "original_user_prompt" ? optional("modalOriginalEdit") : optional("modalTemplateEdit");
    if (!textarea) {
      showError(new Error("Edit field not available — hard-refresh the page (Ctrl+F5)."));
      return;
    }
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    if (end <= start) {
      alert("Select text in the prompt first.");
      return;
    }
    const selected = textarea.value.slice(start, end);
    const suggested = selected.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "token_a";
    const varName = prompt("Variable name (snake_case):", suggested);
    if (!varName || !varName.trim()) return;

    const result = await api(`/api/prompts/${state.activePromptId}/make-variable`, {
      method: "POST",
      body: JSON.stringify({
        field,
        start,
        end,
        var_name: varName.trim(),
        text: textarea.value,
        variables: state.editDraft.variables || {},
      }),
    });

    if (field === "original_user_prompt") {
      if (optional("modalOriginalEdit")) optional("modalOriginalEdit").value = result.original_user_prompt;
      state.editDraft.original_user_prompt = result.original_user_prompt;
    } else {
      if (optional("modalTemplateEdit")) optional("modalTemplateEdit").value = result.refined_prompt;
      state.editDraft.refined_prompt = result.refined_prompt;
    }
    state.editDraft.variables = result.variables || {};
    state.editDraft.placeholders = result.placeholders || [];
    renderVarFields(state.editDraft, true);
  }

  async function generate() {
    if (!state.activePromptId) return;
    const values = {};
    $("varFields").querySelectorAll("input, select").forEach((field) => {
      values[field.name] = field.value;
    });
    const data = await api("/api/generate", {
      method: "POST",
      body: JSON.stringify({ prompt_id: state.activePromptId, values }),
    });
    $("generatedOut").value = data.filled_text || "";
  }

  async function copyGenerated() {
    const text = $("generatedOut").value;
    if (!text) return;
    await navigator.clipboard.writeText(text);
    $("copyBtn").textContent = "Copied";
    setTimeout(() => {
      $("copyBtn").textContent = "Copy";
    }, 1200);
  }

  async function toggleFavorite(promptId) {
    await api(`/api/prompts/${promptId}/favorite`, { method: "POST" });
    await loadPrompts();
  }

  async function deletePrompt(promptId) {
    if (!confirm("Remove this prompt from the library?")) return;
    if (!confirm("This permanently deletes the prompt. Continue?")) return;
    await api(`/api/prompts/${promptId}`, { method: "DELETE" });
    if (state.activePromptId === promptId) {
      state.activePromptId = null;
      const modal = $("runModal");
      if (modal.open) modal.close();
    }
    await refreshLibrary();
  }

  async function loadSuites() {
    const data = await api("/api/suites");
    state.suites = data.suites || [];
    renderSuiteList();
  }

  function renderSuiteList() {
    const el = $("suiteList");
    el.innerHTML = "";
    if (!state.suites.length) {
      el.innerHTML = `<p class="muted">No suites yet. Create one or add a prompt from the library.</p>`;
      return;
    }
    state.suites.forEach((s) => {
      const row = document.createElement("div");
      row.className = "suite-row";
      row.innerHTML = `<strong>${escapeHtml(s.name)}</strong>
        <span class="muted">${(s.prompt_ids || []).length} prompts</span>
        <button type="button" class="btn-secondary" data-suite-open="${s.id}">Open</button>
        <button type="button" class="btn-secondary" data-suite-del="${s.id}">Delete</button>`;
      el.appendChild(row);
    });
  }

  async function openSuite(suiteId) {
    state.activeSuiteId = suiteId;
    const data = await api(`/api/suites/${suiteId}`);
    const detail = $("suiteDetail");
    detail.classList.remove("hidden");
    const prompts = data.prompts || [];
    detail.innerHTML = `<h2>${escapeHtml(data.name)}</h2>
      <p class="muted">${prompts.length} prompt${prompts.length === 1 ? "" : "s"} — open one at a time (Run all later)</p>
      <div class="prompt-grid" id="suitePromptGrid"></div>`;
    const grid = detail.querySelector("#suitePromptGrid");
    prompts.forEach((p) => {
      const card = document.createElement("article");
      card.className = "prompt-card";
      card.innerHTML = `
        <h3 class="card-title">${escapeHtml(p.title)}</h3>
        ${cardMetaHtml(p)}
        <div class="card-actions"><button type="button" class="btn-primary" data-run="${p.id}">Run</button></div>`;
      grid.appendChild(card);
    });
  }

  async function createSuite(name) {
    const suite = await api("/api/suites", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    await loadSuites();
    return suite;
  }

  async function openSuitePicker(promptId) {
    state.suitePickPromptId = promptId;
    await loadSuites();
    const list = $("suitePickList");
    list.innerHTML = "";
    state.suites.forEach((s) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = s.name;
      btn.addEventListener("click", async () => {
        await api(`/api/suites/${s.id}/prompts`, {
          method: "POST",
          body: JSON.stringify({ prompt_id: promptId }),
        });
        $("suitePickModal").close();
        $("statusLine").textContent = `Added to ${s.name}`;
      });
      list.appendChild(btn);
    });
    $("newSuiteName").value = "";
    $("suitePickModal").showModal();
  }

  function bindEvents() {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", async () => {
        state.view = btn.dataset.view;
        state.tag = null;
        syncNav();
        if (state.view === "suites") {
          await loadSuites();
          $("suiteDetail").classList.add("hidden");
        } else {
          await loadPrompts();
          await loadTags();
        }
      });
    });

    $("searchInput").addEventListener(
      "input",
      debounce(() => {
        state.q = $("searchInput").value.trim();
        if (state.view === "suites") return;
        loadPrompts();
      }, 200)
    );

    $("promptGrid").addEventListener("click", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      const menuToggle = t.closest("[data-menu-toggle]");
      if (menuToggle instanceof HTMLElement && menuToggle.dataset.menuToggle) {
        e.stopPropagation();
        const menu = menuToggle.closest(".action-menu");
        const panel = menu && menu.querySelector(".action-menu-panel");
        const wasOpen = panel && !panel.classList.contains("hidden");
        closeAllActionMenus();
        if (panel && !wasOpen) {
          panel.classList.remove("hidden");
          menuToggle.setAttribute("aria-expanded", "true");
        }
        return;
      }
      const runBtn = t.closest("[data-run]");
      const editBtn = t.closest("[data-edit]");
      if (runBtn instanceof HTMLElement && runBtn.dataset.run) {
        openRunSafe(runBtn.dataset.run);
        return;
      }
      if (editBtn instanceof HTMLElement && editBtn.dataset.edit) {
        openRunSafe(editBtn.dataset.edit, true);
        return;
      }
      if (t.dataset.fav) toggleFavorite(t.dataset.fav);
      if (t.dataset.suiteAdd) {
        closeAllActionMenus();
        openSuitePicker(t.dataset.suiteAdd);
      }
      if (t.dataset.delete) {
        closeAllActionMenus();
        deletePrompt(t.dataset.delete).catch(alert);
      }
    });

    document.addEventListener("click", (e) => {
      const t = e.target;
      if (t instanceof HTMLElement && t.closest(".action-menu")) return;
      closeAllActionMenus();
    });

    $("layoutCards").addEventListener("click", () => setLayout("cards"));
    $("layoutList").addEventListener("click", () => setLayout("list"));
    $("downloadAllBtn").addEventListener("click", () => {
      window.location.href = "/api/prompts/download";
    });
    $("refreshBtn").addEventListener("click", () => refreshLibrary().catch(showError));
    bindClick("libraryBannerReload", () => refreshLibrary().catch(showError));
    $("refreshSuitesBtn").addEventListener("click", () => refreshSuites().catch(showError));
    const showDisabledToggle = optional("showDisabledToggle");
    if (showDisabledToggle) {
      showDisabledToggle.checked = state.showDisabled;
      showDisabledToggle.addEventListener("change", () => {
        state.showDisabled = showDisabledToggle.checked;
        localStorage.setItem(SHOW_DISABLED_KEY, state.showDisabled ? "true" : "false");
        loadPrompts().catch(showError);
      });
    }

    $("suiteList").addEventListener("click", async (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      if (t.dataset.suiteOpen) openSuite(t.dataset.suiteOpen);
      if (t.dataset.suiteDel) {
        if (!confirm("Delete this suite?")) return;
        await api(`/api/suites/${t.dataset.suiteDel}`, { method: "DELETE" });
        $("suiteDetail").classList.add("hidden");
        state.activeSuiteId = null;
        await loadSuites();
      }
    });

    $("suiteDetail").addEventListener("click", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      const runBtn = t.closest("[data-run]");
      if (runBtn instanceof HTMLElement && runBtn.dataset.run) {
        openRunSafe(runBtn.dataset.run);
      }
    });

    $("newSuiteBtn").addEventListener("click", async () => {
      const name = prompt("Suite name");
      if (!name || !name.trim()) return;
      await createSuite(name.trim());
    });

    bindClick("closeModal", () => {
      resetRunModalState();
      optional("runModal")?.close();
    });
    const runModal = optional("runModal");
    if (runModal) {
      runModal.addEventListener("close", () => {
        resetRunModalState();
      });
    }
    bindClick("editBtn", () => setEditMode(true));
    bindClick("cancelEditBtn", () => cancelEdit());
    bindClick("saveEditBtn", () => saveEdit().catch(showError));
    bindClick("makeVarOriginalBtn", () =>
      makeVariableFromField("original_user_prompt").catch(showError)
    );
    bindClick("makeVarTemplateBtn", () =>
      makeVariableFromField("refined_prompt").catch(showError)
    );
    $("toggleOriginal").addEventListener("click", () => {
      const pre = $("modalOriginal");
      const btn = $("toggleOriginal");
      setBlockExpanded(pre, btn, pre.classList.contains("is-collapsed"));
    });
    $("toggleTemplate").addEventListener("click", () => {
      const pre = $("modalTemplate");
      const btn = $("toggleTemplate");
      setBlockExpanded(pre, btn, pre.classList.contains("is-collapsed"));
    });
    bindClick("generateBtn", () => generate().catch(showError));
    bindClick("copyBtn", () => copyGenerated().catch(showError));
    $("closeSuitePick").addEventListener("click", () => $("suitePickModal").close());
    $("createAndAddBtn").addEventListener("click", async () => {
      const name = $("newSuiteName").value.trim();
      if (!name || !state.suitePickPromptId) return;
      const suite = await createSuite(name);
      await api(`/api/suites/${suite.id}/prompts`, {
        method: "POST",
        body: JSON.stringify({ prompt_id: state.suitePickPromptId }),
      });
      $("suitePickModal").close();
    });

    const params = new URLSearchParams(location.search);
    const deepPrompt = params.get("prompt_id");
    const deepSuite = params.get("suite");
    if (deepPrompt) openRunSafe(deepPrompt);
    if (deepSuite) {
      state.view = "suites";
      syncNav();
      loadSuites().then(() => openSuite(deepSuite)).catch(() => {});
    }
  }

  async function init() {
    bindEvents();
    syncNav();
    syncLayoutButtons();
    await refreshLibrary();
    window.addEventListener("focus", () => pollLibraryInfo());
    setInterval(() => pollLibraryInfo(), LIBRARY_POLL_MS);
  }

  init().catch((err) => {
    console.error(err);
    $("statusLine").textContent = "Error loading library";
  });
})();
