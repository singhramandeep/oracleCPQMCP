(() => {
  const LAYOUT_KEY = "promptStudio.layout";
  const SHOW_DISABLED_KEY = "promptStudio.showDisabled";
  const PROFILE_FILTER_KEY = "promptStudio.profileFilter";
  const LIBRARY_POLL_MS = 30000;
  const UNSCOPED_PROFILE = "__unscoped__";

  const state = {
    view: "all",
    tag: null,
    q: "",
    profile: localStorage.getItem(PROFILE_FILTER_KEY) || "",
    layout: localStorage.getItem(LAYOUT_KEY) === "list" ? "list" : "cards",
    showDisabled: localStorage.getItem(SHOW_DISABLED_KEY) === "true",
    prompts: [],
    suites: [],
    selectedIds: new Set(),
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
    importPrompts: [],
    importCandidates: [],
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

  function profileBadgeHtml(p) {
    if (!p.profile) return "";
    return `<span class="profile-badge" title="CPQ profile">${escapeHtml(p.profile)}</span>`;
  }

  function cardMetaHtml(p) {
    const fmt = formatLabel(p.output_format);
    const runs = p.run_count || 0;
    const profileBit = p.profile
      ? `<span class="profile-badge">${escapeHtml(p.profile)}</span>`
      : "";
    return `
      <div class="card-meta-line">
        ${profileBit}
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
    if (state.profile) params.set("profile", state.profile);
    if (state.view === "favorites") params.set("favorites_only", "true");
    if (state.showDisabled) params.set("include_disabled", "true");
    params.set("sort", "recent");
    const data = await api(`/api/prompts?${params}`);
    state.prompts = data.prompts || [];
    const keep = new Set(state.prompts.map((p) => p.id));
    state.selectedIds = new Set(
      [...state.selectedIds].filter((id) => keep.has(id))
    );
    renderPrompts();
  }

  async function loadProfiles() {
    const select = optional("profileFilter");
    if (!select) return;
    const data = await api("/api/profiles").catch(() => ({
      profiles: [],
      unscoped_count: 0,
    }));
    const profiles = data.profiles || [];
    const unscoped = data.unscoped_count || 0;
    const current = state.profile || "";
    select.innerHTML = "";
    const allOpt = document.createElement("option");
    allOpt.value = "";
    allOpt.textContent = "All profiles";
    select.appendChild(allOpt);
    const unscopedOpt = document.createElement("option");
    unscopedOpt.value = UNSCOPED_PROFILE;
    unscopedOpt.textContent =
      unscoped > 0 ? `Unscoped (${unscoped})` : "Unscoped";
    select.appendChild(unscopedOpt);
    profiles.forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      select.appendChild(opt);
    });
    if (
      current &&
      current !== UNSCOPED_PROFILE &&
      !profiles.includes(current)
    ) {
      const orphan = document.createElement("option");
      orphan.value = current;
      orphan.textContent = `${current} (none)`;
      select.appendChild(orphan);
    }
    select.value = current;
  }

  function updateResultCount() {
    const el = $("resultCount");
    const n = state.prompts.length;
    const filtered = Boolean(
      state.q || state.tag || state.profile || state.view === "favorites"
    );
    if (!filtered) {
      el.textContent = "";
      el.classList.add("hidden");
      return;
    }
    el.classList.remove("hidden");
    el.textContent = `${n} matching`;
  }

  function syncExportSelectedBtn() {
    const btn = optional("exportSelectedBtn");
    if (!btn) return;
    const n = state.selectedIds.size;
    btn.disabled = n === 0;
    btn.textContent = n ? `Export selected (${n})` : "Export selected";
  }

  function toggleSelected(id, checked) {
    if (checked) state.selectedIds.add(id);
    else state.selectedIds.delete(id);
    syncExportSelectedBtn();
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
      syncExportSelectedBtn();
      return;
    }
    empty.classList.add("hidden");

    if (state.layout === "list") {
      const head = document.createElement("div");
      head.className = "prompt-list-head";
      head.innerHTML = `
        <span></span>
        <span>Title</span>
        <span>Format</span>
        <span>Runs</span>
        <span>Last run</span>
        <span>Actions</span>`;
      grid.appendChild(head);
    }

    state.prompts.forEach((p) => {
      const checked = state.selectedIds.has(p.id) ? "checked" : "";
      const selectHtml = `<label class="select-box" title="Select for export"><input type="checkbox" data-select="${p.id}" ${checked} /></label>`;
      if (state.layout === "list") {
        const row = document.createElement("article");
        row.className = "prompt-list-row" + (p.enabled === false ? " is-disabled" : "");
        row.innerHTML = `
          ${selectHtml}
          <div class="list-title-cell">
            <strong>${escapeHtml(p.title)}</strong>
            ${disabledBadgeHtml(p)}
            ${profileBadgeHtml(p)}
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
          ${selectHtml}
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
    syncExportSelectedBtn();
  }

  function syncNav() {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === state.view);
    });
    const titles = {
      all: "All prompts",
      favorites: "Favorites",
      suites: "Suites",
      help: "Help",
    };
    const viewTitle = optional("viewTitle");
    if (viewTitle) {
      viewTitle.textContent = state.tag ? `Tag: ${state.tag}` : titles[state.view] || "All prompts";
    }
    const isLibrary = state.view === "all" || state.view === "favorites";
    $("libraryView").classList.toggle("hidden", !isLibrary);
    $("suitesView").classList.toggle("hidden", state.view !== "suites");
    optional("helpView")?.classList.toggle("hidden", state.view !== "help");
  }

  function updateLibraryPathDisplay(path) {
    const text = optional("libraryPathText");
    const btn = optional("libraryPathBtn");
    if (!text || !btn) return;
    if (!path) {
      text.textContent = "Library path unknown";
      btn.title = "";
      return;
    }
    text.textContent = path;
    btn.title = "Click to copy: " + path;
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
      lines.push("Library file missing — save a prompt via MCP or New / Import.");
    }
    el.title = lines.join("\n");
    if (info && info.path) state.libraryPath = info.path;
    if (info && info.help) state.libraryHelp = info.help;
    updateLibraryPathDisplay(path);
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
    const [, , , info] = await Promise.all([
      loadTags(),
      loadProfiles(),
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
        } else if (state.view === "help") {
          await loadHelp().catch(showError);
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
        if (state.view === "suites" || state.view === "help") return;
        loadPrompts();
      }, 200)
    );

    $("promptGrid").addEventListener("change", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLInputElement) || !t.dataset.select) return;
      toggleSelected(t.dataset.select, t.checked);
    });

    $("promptGrid").addEventListener("click", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      if (t.closest("[data-select]") || (t instanceof HTMLInputElement && t.dataset.select)) {
        return;
      }
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

    bindClick("layoutCards", () => setLayout("cards"));
    bindClick("layoutList", () => setLayout("list"));
    bindClick("downloadAllBtn", () => {
      window.location.href = "/api/prompts/download";
    });
    bindClick("exportSelectedBtn", () => exportSelected().catch(showError));
    bindClick("newPromptBtn", () => openNewPromptModal());
    bindClick("importBtn", () => openImportModal());
    bindClick("libraryPathBtn", () => copyLibraryPath().catch(showError));
    bindClick("refreshBtn", () => refreshLibrary().catch(showError));
    bindClick("libraryBannerReload", () => refreshLibrary().catch(showError));
    bindClick("refreshSuitesBtn", () => refreshSuites().catch(showError));
    const profileFilter = optional("profileFilter");
    if (profileFilter) {
      profileFilter.value = state.profile || "";
      profileFilter.addEventListener("change", () => {
        state.profile = profileFilter.value || "";
        localStorage.setItem(PROFILE_FILTER_KEY, state.profile);
        loadPrompts().catch(showError);
      });
    }
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

    bindClick("closeNewPrompt", () => optional("newPromptModal")?.close());
    bindClick("cancelNewPrompt", () => optional("newPromptModal")?.close());
    bindClick("saveNewPrompt", () => saveNewPrompt().catch(showError));

    bindClick("closeImport", () => optional("importModal")?.close());
    bindClick("cancelImport", () => optional("importModal")?.close());
    bindClick("applyImport", () => applyImport().catch(showError));
    bindClick("importSelectAll", () => setImportSelection(true));
    bindClick("importSelectNone", () => setImportSelection(false));
    const importFile = optional("importFile");
    if (importFile) {
      importFile.addEventListener("change", () => previewImportFile().catch(showError));
    }

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

  async function copyLibraryPath() {
    const path = state.libraryPath;
    if (!path) throw new Error("Library path unknown");
    await navigator.clipboard.writeText(path);
    const el = $("statusLine");
    const prev = el.textContent;
    el.textContent = "Library path copied";
    setTimeout(() => {
      el.textContent = prev;
    }, 1500);
  }

  async function loadHelp() {
    const data = await api("/api/help");
    const root = $("helpContent");
    if (!root) return;
    if (data.library_path) {
      state.libraryPath = data.library_path;
      updateLibraryPathDisplay(data.library_path);
    }
    const sections = data.sections || [];
    root.innerHTML = sections
      .map(
        (s) => `
      <article class="help-card">
        <h2>${escapeHtml(s.title || "")}</h2>
        <pre class="help-pre">${escapeHtml(s.body || "")}</pre>
      </article>`
      )
      .join("");
  }

  function openNewPromptModal() {
    optional("newTitle").value = "";
    optional("newOriginal").value = "";
    optional("newRefined").value = "";
    optional("newTags").value = "";
    optional("newProfile").value = "";
    optional("newFormat").value = "chat_text";
    optional("newPromptModal")?.showModal();
  }

  async function saveNewPrompt() {
    const title = ($("newTitle").value || "").trim();
    const refined = ($("newRefined").value || "").trim();
    if (!title) throw new Error("Title is required");
    if (!refined) throw new Error("Refined template is required");
    const tags = ($("newTags").value || "")
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    const profile = (optional("newProfile")?.value || "").trim();
    await api("/api/prompts", {
      method: "POST",
      body: JSON.stringify({
        title,
        original_user_prompt: $("newOriginal").value || "",
        refined_prompt: refined,
        tags,
        output_format: $("newFormat").value || "chat_text",
        profile: profile || null,
      }),
    });
    optional("newPromptModal")?.close();
    await refreshLibrary();
  }

  function openImportModal() {
    state.importPrompts = [];
    state.importCandidates = [];
    const file = optional("importFile");
    if (file) file.value = "";
    optional("importLabel").value = "";
    optional("importCandidateList").innerHTML = "";
    optional("importPreviewCount").textContent = "";
    optional("applyImport").disabled = true;
    optional("importModal")?.showModal();
  }

  async function previewImportFile() {
    const fileInput = optional("importFile");
    const file = fileInput && fileInput.files && fileInput.files[0];
    if (!file) return;
    const text = await file.text();
    const data = await api("/api/prompts/import/preview", {
      method: "POST",
      body: JSON.stringify({ raw_text: text }),
    });
    state.importPrompts = data.prompts || [];
    state.importCandidates = data.candidates || [];
    if (!optional("importLabel").value.trim() && file.name) {
      optional("importLabel").value = file.name.replace(/\.json$/i, "");
    }
    renderImportCandidates();
  }

  function renderImportCandidates() {
    const list = optional("importCandidateList");
    const countEl = optional("importPreviewCount");
    if (!list) return;
    list.innerHTML = "";
    const candidates = state.importCandidates;
    if (countEl) {
      countEl.textContent = candidates.length
        ? `${candidates.length} prompt(s) in file`
        : "No prompts found";
    }
    candidates.forEach((c) => {
      const row = document.createElement("label");
      row.className = "import-candidate";
      const disabled = c.empty_refined ? "disabled" : "";
      const checked = c.empty_refined ? "" : "checked";
      const flags = [];
      if (c.already_in_library) flags.push("already in library");
      if (c.empty_refined) flags.push("empty refined — skipped");
      row.innerHTML = `
        <input type="checkbox" data-import-index="${c.index}" ${checked} ${disabled} />
        <span class="import-candidate-body">
          <strong>${escapeHtml(c.title)}</strong>
          <span class="muted">${escapeHtml(c.refined_preview || "")}</span>
          ${flags.length ? `<span class="import-flags">${escapeHtml(flags.join(" · "))}</span>` : ""}
        </span>`;
      list.appendChild(row);
    });
    syncApplyImportBtn();
  }

  function setImportSelection(all) {
    document.querySelectorAll("[data-import-index]").forEach((el) => {
      if (!(el instanceof HTMLInputElement) || el.disabled) return;
      el.checked = all;
    });
    syncApplyImportBtn();
  }

  function syncApplyImportBtn() {
    const btn = optional("applyImport");
    if (!btn) return;
    const selected = [...document.querySelectorAll("[data-import-index]:checked")].length;
    const labelOk = Boolean((optional("importLabel")?.value || "").trim());
    btn.disabled = !(selected > 0 && labelOk && state.importPrompts.length);
  }

  async function applyImport() {
    const label = (optional("importLabel")?.value || "").trim();
    if (!label) throw new Error("Import name / tag is required");
    const indices = [...document.querySelectorAll("[data-import-index]:checked")]
      .map((el) => Number(el.dataset.importIndex))
      .filter((n) => Number.isInteger(n));
    if (!indices.length) throw new Error("Select at least one prompt");
    const result = await api("/api/prompts/import", {
      method: "POST",
      body: JSON.stringify({
        import_label: label,
        indices,
        prompts: state.importPrompts,
      }),
    });
    optional("importModal")?.close();
    alert(
      `Import “${result.import_label}”: ${result.imported} new, ${result.updated} updated` +
        (result.skipped_empty ? `, ${result.skipped_empty} empty skipped` : "") +
        (result.errors && result.errors.length ? `\nErrors: ${result.errors.join("; ")}` : "") +
        `\nTags: ${(result.import_tags || []).join(", ")}`
    );
    state.tag = (result.import_tags || []).find((t) => String(t).startsWith("import:")) || null;
    state.view = "all";
    syncNav();
    await refreshLibrary();
  }

  async function exportSelected() {
    const ids = [...state.selectedIds];
    if (!ids.length) throw new Error("Select at least one prompt");
    const res = await fetch("/api/prompts/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || res.statusText);
    }
    const blob = await res.blob();
    const disp = res.headers.get("Content-Disposition") || "";
    const match = /filename="?([^"]+)"?/.exec(disp);
    const filename = match ? match[1] : "saved_prompts_selected.json";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function init() {
    bindEvents();
    optional("importLabel")?.addEventListener("input", () => syncApplyImportBtn());
    optional("importCandidateList")?.addEventListener("change", () => syncApplyImportBtn());
    syncNav();
    syncLayoutButtons();
    syncExportSelectedBtn();
    await refreshLibrary();
    window.addEventListener("focus", () => pollLibraryInfo());
    setInterval(() => pollLibraryInfo(), LIBRARY_POLL_MS);
  }

  init().catch((err) => {
    console.error(err);
    $("statusLine").textContent = "Error loading library";
  });
})();
