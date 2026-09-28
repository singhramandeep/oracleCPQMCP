(() => {
  const LAYOUT_KEY = "promptStudio.layout";
  const SHOW_DISABLED_KEY = "promptStudio.showDisabled";
  const PROFILE_FILTER_KEY = "promptStudio.profileFilter";
  const RATING_FILTER_KEY = "promptStudio.ratingFilter";
  const LIBRARY_POLL_MS = 30000;
  const UNSCOPED_PROFILE = "__unscoped__";

  const LOGS_FILE_KEY = "promptStudio.logsFile";

  /** @returns {{ ratingFilter: string, minRating: number|null }} */
  function parseRatingFilterValue(raw) {
    const v = (raw || "").trim();
    if (v === "unrated") return { ratingFilter: "unrated", minRating: null };
    if (v === "rated") return { ratingFilter: "rated", minRating: null };
    if (v === "7" || v === "8" || v === "9" || v === "10") {
      return { ratingFilter: "", minRating: Number(v) };
    }
    return { ratingFilter: "", minRating: null };
  }

  const state = {
    view: "all",
    tag: null,
    q: "",
    profile: localStorage.getItem(PROFILE_FILTER_KEY) || "",
    ratingFilterValue: localStorage.getItem(RATING_FILTER_KEY) || "",
    layout: localStorage.getItem(LAYOUT_KEY) === "list" ? "list" : "cards",
    showDisabled: localStorage.getItem(SHOW_DISABLED_KEY) === "true",
    prompts: [],
    suites: [],
    selectedIds: new Set(),
    libraryTotal: 0,
    libraryPath: null,
    libraryHelp: "",
    studioVersion: null,
    lastSeenModified: null,
    activePromptId: null,
    suitePickPromptId: null,
    activeSuiteId: null,
    editMode: false,
    editDraft: null,
    modalDetail: null,
    importPrompts: [],
    importCandidates: [],
    logsFiles: [],
    logsDir: "",
    logsFile: localStorage.getItem(LOGS_FILE_KEY) || "",
    logsEntries: [],
    logsSummary: null,
    logsSelected: new Set(),
    logsMethod: "",
    logsStatus: "",
    logsMinMs: "",
    logsErrorsOnly: false,
    logsP95: null,
    configProfiles: [],
    configProfile: localStorage.getItem("promptStudio.configProfile") || "",
    configEnv: localStorage.getItem("promptStudio.configEnv") || "dev",
    configYaml: "",
    configPaths: null,
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

  function formatDurationMs(ms) {
    if (ms == null || ms === "") return "—";
    const n = Number(ms);
    if (!Number.isFinite(n) || n < 0) return "—";
    if (n < 1000) return `${Math.round(n)}ms`;
    if (n < 60000) return `${(n / 1000).toFixed(n < 10000 ? 1 : 0)}s`;
    const mins = Math.floor(n / 60000);
    const secs = Math.round((n % 60000) / 1000);
    return `${mins}m ${secs}s`;
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

  function ratingBadgeHtml(p) {
    if (p.rating == null) {
      return `<span class="rating-badge muted" title="No rating">—/10</span>`;
    }
    return `<span class="rating-badge" title="Rating">${escapeHtml(String(p.rating))}/10</span>`;
  }

  function cardMetaHtml(p) {
    const fmt = formatLabel(p.output_format);
    const runs = p.run_count || 0;
    const comments = p.comment_count || 0;
    const profileBit = p.profile
      ? `<span class="profile-badge">${escapeHtml(p.profile)}</span>`
      : "";
    const source = p.last_source
      ? `<span class="source-badge source-${escapeAttr(p.last_source)}">${escapeHtml(p.last_source)}</span>`
      : "";
    const elapsed = p.last_duration_ms != null
      ? `<span title="Last elapsed">${escapeHtml(formatDurationMs(p.last_duration_ms))}</span>`
      : "";
    return `
      <div class="card-meta-line">
        ${profileBit}
        <span class="comment-count" title="Comments">${comments} comment${comments === 1 ? "" : "s"}</span>
        <span class="format-badge">${escapeHtml(fmt)}</span>
        <span>${runs} run${runs === 1 ? "" : "s"}</span>
        ${source}
        ${elapsed}
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
    const ratingParts = parseRatingFilterValue(state.ratingFilterValue);
    if (ratingParts.ratingFilter) params.set("rating_filter", ratingParts.ratingFilter);
    if (ratingParts.minRating != null) params.set("min_rating", String(ratingParts.minRating));
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
      state.q ||
        state.tag ||
        state.profile ||
        state.ratingFilterValue ||
        state.view === "favorites"
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
        <span>Rating</span>
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
        const comments = p.comment_count || 0;
        const lastRunTitleParts = [];
        if (p.last_source) lastRunTitleParts.push(`source: ${p.last_source}`);
        if (p.last_duration_ms != null) {
          lastRunTitleParts.push(`elapsed: ${formatDurationMs(p.last_duration_ms)}`);
        }
        const lastRunTitle = lastRunTitleParts.length
          ? ` title="${escapeAttr(lastRunTitleParts.join(" · "))}"`
          : "";
        const runsTitle = p.last_source
          ? ` title="Last source: ${escapeAttr(p.last_source)}"`
          : "";
        row.innerHTML = `
          ${selectHtml}
          <div class="list-title-cell">
            <strong title="${escapeAttr(p.title)}">${escapeHtml(p.title)}</strong>
            <div class="original-preview muted">${escapeHtml(p.original_preview || p.original_user_prompt || "(no original prompt recorded)")}</div>
            <div class="list-title-meta">
              ${disabledBadgeHtml(p)}
              ${profileBadgeHtml(p)}
              <span class="comment-count muted" title="Comments">${comments}c</span>
              <div class="chip-row compact">${chipHtml(p)}</div>
            </div>
          </div>
          <span class="list-cell list-cell-rating">${ratingBadgeHtml(p)}</span>
          <span class="list-cell"><span class="format-badge">${escapeHtml(formatLabel(p.output_format))}</span></span>
          <span class="list-cell list-cell-runs"${runsTitle}>${p.run_count || 0}</span>
          <span class="list-cell muted"${lastRunTitle}>${escapeHtml(formatWhen(p.last_run_at))}</span>
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
            ${ratingBadgeHtml(p)}
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
      logs: "API logs",
      config: "Profiles & Paths",
      help: "Help",
    };
    const viewTitle = optional("viewTitle");
    if (viewTitle) {
      viewTitle.textContent = state.tag ? `Tag: ${state.tag}` : titles[state.view] || "All prompts";
    }
    const isLibrary = state.view === "all" || state.view === "favorites";
    $("libraryView").classList.toggle("hidden", !isLibrary);
    $("suitesView").classList.toggle("hidden", state.view !== "suites");
    optional("logsView")?.classList.toggle("hidden", state.view !== "logs");
    optional("configView")?.classList.toggle("hidden", state.view !== "config");
    optional("helpView")?.classList.toggle("hidden", state.view !== "help");
    const search = optional("searchInput");
    if (search) {
      search.placeholder =
        state.view === "logs" ? "Search method, path, URL, curl…" : "Search prompts…";
    }
  }

  function renderSourceStats(stats) {
    const grid = optional("modalSourceStatsGrid");
    if (!grid) return;
    const buckets = stats || {};
    const labels = {
      cache: "Cached runs",
      api: "API runs",
      mixed: "Mixed runs",
    };
    grid.innerHTML = ["cache", "api", "mixed"]
      .map((source) => {
        const b = buckets[source] || {};
        const count = b.count || 0;
        return `
          <div class="source-stat-card source-${source}">
            <div class="source-stat-title">${labels[source]}</div>
            <div class="source-stat-line"><span>Count</span><strong>${count}</strong></div>
            <div class="source-stat-line"><span>Last</span><strong>${escapeHtml(formatDurationMs(b.last_duration_ms))}</strong></div>
            <div class="source-stat-line"><span>Average</span><strong>${escapeHtml(formatDurationMs(b.avg_duration_ms))}</strong></div>
            <div class="source-stat-line muted"><span>Last at</span><span>${escapeHtml(formatWhen(b.last_at))}</span></div>
          </div>`;
      })
      .join("");
  }

  function renderComments(detail) {
    const list = optional("modalComments");
    if (!list) return;
    const comments = detail.comments || [];
    if (!comments.length) {
      list.innerHTML = `<p class="muted">No comments yet.</p>`;
      return;
    }
    list.innerHTML = comments
      .map((c) => {
        const edited = c.updated_at
          ? ` · edited ${escapeHtml(formatWhen(c.updated_at))}`
          : "";
        return `
          <div class="comment-item" data-comment-id="${escapeAttr(c.id)}">
            <div class="comment-meta muted">${escapeHtml(formatWhen(c.created_at))}${edited}</div>
            <p class="comment-text">${escapeHtml(c.text)}</p>
            <div class="comment-actions">
              <button type="button" class="btn-ghost btn-sm" data-comment-edit="${escapeAttr(c.id)}">Edit</button>
              <button type="button" class="btn-ghost btn-sm danger" data-comment-delete="${escapeAttr(c.id)}">Delete</button>
            </div>
          </div>`;
      })
      .join("");
  }

  async function refreshModalDetail(detail) {
    state.modalDetail = detail;
    populateRunModal(detail);
  }

  async function saveRating() {
    if (!state.activePromptId) return;
    const select = optional("modalRatingSelect");
    const raw = select ? select.value : "";
    const rating = raw === "" ? null : Number(raw);
    const detail = await api(`/api/prompts/${state.activePromptId}/rating`, {
      method: "PATCH",
      body: JSON.stringify({ rating }),
    });
    await refreshModalDetail(detail);
    showToast(rating == null ? "Rating cleared" : `Rated ${rating}/10`);
    await loadPrompts().catch(() => {});
  }

  async function addComment() {
    if (!state.activePromptId) return;
    const box = optional("modalCommentText");
    const text = (box?.value || "").trim();
    if (!text) {
      showError(new Error("Comment text is required"));
      return;
    }
    const detail = await api(`/api/prompts/${state.activePromptId}/comments`, {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    if (box) box.value = "";
    await refreshModalDetail(detail);
    showToast("Comment added");
    await loadPrompts().catch(() => {});
  }

  async function deleteComment(commentId) {
    if (!state.activePromptId || !commentId) return;
    if (!window.confirm("Delete this comment?")) return;
    const detail = await api(
      `/api/prompts/${state.activePromptId}/comments/${encodeURIComponent(commentId)}`,
      { method: "DELETE" }
    );
    await refreshModalDetail(detail);
    showToast("Comment deleted");
    await loadPrompts().catch(() => {});
  }

  async function editComment(commentId) {
    if (!state.activePromptId || !commentId) return;
    const existing = (state.modalDetail?.comments || []).find((c) => c.id === commentId);
    const next = window.prompt("Edit comment", existing?.text || "");
    if (next == null) return;
    const text = next.trim();
    if (!text) {
      showError(new Error("Comment text is required"));
      return;
    }
    const detail = await api(
      `/api/prompts/${state.activePromptId}/comments/${encodeURIComponent(commentId)}`,
      { method: "PATCH", body: JSON.stringify({ text }) }
    );
    await refreshModalDetail(detail);
    showToast("Comment updated");
  }

  async function loadConfigProfiles() {
    const data = await api("/api/config/profiles");
    state.configProfiles = data.profiles || [];
    const select = optional("configProfileSelect");
    if (!select) return;
    const previous = state.configProfile;
    select.innerHTML = "";
    if (!state.configProfiles.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No profile YAML found";
      select.appendChild(opt);
      state.configProfile = "";
    } else {
      state.configProfiles.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p.customer_id;
        opt.textContent = p.customer_id + (p.has_catalog ? " (+catalog)" : "");
        select.appendChild(opt);
      });
      if (!previous || !state.configProfiles.some((p) => p.customer_id === previous)) {
        state.configProfile = state.configProfiles[0].customer_id;
      }
      select.value = state.configProfile;
    }
    const envSelect = optional("configEnvSelect");
    if (envSelect) envSelect.value = state.configEnv || "dev";
    const count = optional("configResultCount");
    if (count) {
      count.textContent = `${state.configProfiles.length} profile${
        state.configProfiles.length === 1 ? "" : "s"
      }`;
    }
    await loadConfigDetail();
  }

  function renderConfigPaths(paths) {
    const grid = optional("configPathCards");
    if (!grid) return;
    const order = [
      ["profile_yaml", "Profile YAML"],
      ["catalog_yaml", "Catalog YAML"],
      ["saved_prompts", "Saved prompts"],
      ["studio_state", "Studio state"],
      ["logs_dir", "Logs directory"],
      ["debug_log", "Debug log"],
      ["local_data_root", "Local cache"],
      ["exports_dir", "Exports"],
      ["config_dir", "Config directory"],
      ["example_profile_yaml", "Example profile"],
    ];
    grid.innerHTML = order
      .filter(([key]) => paths && paths[key])
      .map(([key, label]) => {
        const info = paths[key];
        const exists = info.exists ? "exists" : "missing";
        return `
          <div class="config-path-card">
            <div class="config-path-title">${escapeHtml(label)}</div>
            <div class="config-path-status ${exists}">${exists}</div>
            <code class="config-path-value" title="${escapeAttr(info.path)}">${escapeHtml(info.path)}</code>
            <button type="button" class="btn-secondary btn-sm" data-copy-path="${escapeAttr(info.path)}">Copy path</button>
          </div>`;
      })
      .join("");
  }

  async function loadConfigDetail() {
    const yamlOut = optional("configYamlOut");
    if (!state.configProfile) {
      state.configYaml = "";
      if (yamlOut) yamlOut.textContent = "Select a profile to view redacted YAML.";
      renderConfigPaths(null);
      return;
    }
    localStorage.setItem("promptStudio.configProfile", state.configProfile);
    localStorage.setItem("promptStudio.configEnv", state.configEnv || "dev");
    const [profile, pathsBody] = await Promise.all([
      api(`/api/config/profiles/${encodeURIComponent(state.configProfile)}`),
      api(
        `/api/workspace/paths?profile=${encodeURIComponent(state.configProfile)}&environment=${encodeURIComponent(state.configEnv || "dev")}`
      ),
    ]);
    state.configYaml = profile.yaml_redacted || "";
    if (yamlOut) yamlOut.textContent = state.configYaml || "(empty)";
    state.configPaths = pathsBody.paths || null;
    renderConfigPaths(state.configPaths);
  }

  function showToast(message) {
    const el = optional("toast");
    if (!el) return;
    el.textContent = message;
    el.classList.remove("hidden");
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => el.classList.add("hidden"), 1800);
  }

  function statusClassOf(status) {
    if (status == null) return "other";
    if (typeof status === "string") {
      const lower = status.toLowerCase();
      if (lower === "error" || lower === "timeout" || lower === "exception") return "error";
      const n = Number(status);
      if (!Number.isFinite(n)) return "other";
      status = n;
    }
    if (status >= 200 && status < 300) return "2xx";
    if (status >= 300 && status < 400) return "3xx";
    if (status >= 400 && status < 500) return "4xx";
    if (status >= 500 && status < 600) return "5xx";
    return "other";
  }

  async function loadLogsFileList() {
    const data = await api("/api/logs");
    state.logsFiles = data.files || [];
    state.logsDir = data.logs_dir || "";
    const hint = optional("logsDirHint");
    if (hint) {
      hint.textContent = state.logsDir
        ? `Directory: ${state.logsDir} (DEBUG_MODE writes {profile}-{env}.log)`
        : "";
    }
    const select = optional("logsFileSelect");
    if (!select) return;
    const prev = state.logsFile;
    select.innerHTML = "";
    if (!state.logsFiles.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "(no .log files)";
      select.appendChild(opt);
      state.logsFile = "";
      return;
    }
    state.logsFiles.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f.name;
      const kb = Math.max(1, Math.round((f.size_bytes || 0) / 1024));
      opt.textContent = `${f.name} (${kb} KB)`;
      select.appendChild(opt);
    });
    const names = new Set(state.logsFiles.map((f) => f.name));
    if (prev && names.has(prev)) {
      state.logsFile = prev;
    } else {
      state.logsFile = state.logsFiles[0].name;
    }
    select.value = state.logsFile;
    localStorage.setItem(LOGS_FILE_KEY, state.logsFile);
  }

  function syncLogsCopyButtons() {
    const n = state.logsSelected.size;
    ["logsCopyCurlBtn", "logsCopyBlocksBtn", "logsCopyJsonBtn"].forEach((id) => {
      const btn = optional(id);
      if (btn) btn.disabled = n === 0;
    });
  }

  function renderLogsCharts() {
    const charts = optional("logsCharts");
    const summary = state.logsSummary;
    if (!charts) return;
    if (!summary || !state.logsEntries.length) {
      charts.classList.add("hidden");
      return;
    }
    charts.classList.remove("hidden");

    const buckets = summary.status_buckets || {};
    const colors = {
      "2xx": "#2e7d32",
      "3xx": "#1565c0",
      "4xx": "#ef6c00",
      "5xx": "#c62828",
      error: "#c62828",
      other: "#757575",
    };
    const order = ["2xx", "3xx", "4xx", "5xx", "error", "other"];
    const parts = order
      .map((k) => ({ key: k, count: buckets[k] || 0, color: colors[k] }))
      .filter((p) => p.count > 0);
    const total = parts.reduce((s, p) => s + p.count, 0) || 1;
    let acc = 0;
    const arcs = parts.map((p) => {
      const start = (acc / total) * 360;
      acc += p.count;
      const end = (acc / total) * 360;
      return `${p.color} ${start}deg ${end}deg`;
    });
    const statusEl = optional("logsStatusChart");
    if (statusEl) {
      const legend = parts
        .map(
          (p) =>
            `<li><span class="logs-swatch s${p.key}"></span>${escapeHtml(p.key)} · ${p.count}</li>`
        )
        .join("");
      statusEl.innerHTML = `
        <div style="width:88px;height:88px;border-radius:50%;background:conic-gradient(${
          arcs.length ? arcs.join(",") : "#eee 0deg 360deg"
        });"></div>
        <ul class="logs-status-legend">${legend || "<li class='muted'>No data</li>"}</ul>`;
    }

    const hist = summary.latency_histogram || [];
    const maxH = Math.max(1, ...hist.map((h) => h.count || 0));
    const histEl = optional("logsHistChart");
    if (histEl) {
      histEl.innerHTML = hist
        .map((h) => {
          const pct = Math.round(((h.count || 0) / maxH) * 100);
          return `<div class="logs-hist-bar-wrap" title="${escapeHtml(h.label)}: ${h.count}">
            <div class="logs-hist-bar" style="height:${Math.max(2, pct)}%"></div>
            <div class="logs-hist-label">${escapeHtml(h.label)}<br>${h.count}</div>
          </div>`;
        })
        .join("");
    }

    const p95 = summary.p95_ms;
    state.logsP95 = p95;
    const p95Hint = optional("logsP95Hint");
    if (p95Hint) {
      const p50 = summary.p50_ms;
      p95Hint.textContent =
        p50 != null
          ? `(p50 ${Math.round(p50)} ms · p95 ${Math.round(p95)} ms)`
          : "";
    }
    const strip = optional("logsLatencyStrip");
    if (strip) {
      const recent = state.logsEntries.slice(0, 80).reverse();
      const maxMs = Math.max(1, ...recent.map((e) => e.duration_ms || 0));
      strip.innerHTML = recent
        .map((e) => {
          const sc = statusClassOf(e.status);
          const ms = e.duration_ms || 0;
          const h = Math.max(4, Math.round((ms / maxMs) * 100));
          const slow = p95 != null && ms > p95 ? " is-slow" : "";
          return `<div class="logs-latency-bar s${sc}${slow}" style="height:${h}%" title="${escapeHtml(
            `${e.method} ${e.path} · ${e.status} · ${ms}ms`
          )}"></div>`;
        })
        .join("");
    }
  }

  function renderLogsTimeline() {
    const root = optional("logsTimeline");
    const empty = optional("logsEmpty");
    if (!root) return;
    root.innerHTML = "";
    const entries = state.logsEntries;
    if (empty) empty.classList.toggle("hidden", entries.length > 0);
    const p95 = state.logsP95;
    entries.forEach((e) => {
      const sc = statusClassOf(e.status);
      const slow = p95 != null && e.duration_ms != null && e.duration_ms > p95;
      const checked = state.logsSelected.has(String(e.index)) ? "checked" : "";
      const article = document.createElement("article");
      article.className =
        "logs-entry" + (slow ? " is-slow" : "") + (sc === "4xx" || sc === "5xx" || sc === "error" ? " is-error" : "");
      article.dataset.logIndex = String(e.index);
      const ms = e.duration_ms != null ? `${Math.round(e.duration_ms)} ms` : "—";
      article.innerHTML = `
        <div class="logs-entry-top">
          <input type="checkbox" data-log-select="${e.index}" ${checked} aria-label="Select request" />
          <span class="method-badge ${escapeHtml(e.method || "")}">${escapeHtml(e.method || "?")}</span>
          <span class="logs-path">${escapeHtml(e.path || "")}</span>
          <span class="status-pill s${sc}">${escapeHtml(String(e.status ?? "—"))}</span>
          <span class="logs-entry-meta">${escapeHtml(ms)}</span>
          ${slow ? '<span class="slow-chip">slow</span>' : ""}
          <span class="logs-entry-meta">${escapeHtml(e.timestamp || "")}</span>
          <div class="logs-entry-actions">
            <button type="button" class="btn-secondary btn-sm" data-log-copy-curl="${e.index}">Copy curl</button>
            <button type="button" class="btn-secondary btn-sm" data-log-copy-block="${e.index}">Copy block</button>
          </div>
        </div>
        <details>
          <summary>URL, parameters, curl</summary>
          <pre class="logs-pre">${escapeHtml(e.url || "")}</pre>
          <pre class="logs-pre">${escapeHtml((e.parameters || []).join("\n") || "(no parameters)")}</pre>
          <pre class="logs-pre">${escapeHtml(e.curl || "(no curl)")}</pre>
        </details>`;
      root.appendChild(article);
    });
    syncLogsCopyButtons();
  }

  async function loadLogEntries() {
    if (!state.logsFile) {
      state.logsEntries = [];
      state.logsSummary = null;
      optional("logsCharts")?.classList.add("hidden");
      const timeline = optional("logsTimeline");
      if (timeline) timeline.innerHTML = "";
      optional("logsEmpty")?.classList.remove("hidden");
      const countEl = optional("logsResultCount");
      if (countEl) countEl.textContent = "No log file";
      optional("logsTruncated")?.classList.add("hidden");
      return;
    }
    const params = new URLSearchParams();
    if (state.q) params.set("q", state.q);
    if (state.logsMethod) params.set("method", state.logsMethod);
    const status = state.logsErrorsOnly ? "error" : state.logsStatus;
    if (status) params.set("status", status);
    if (state.logsMinMs !== "" && state.logsMinMs != null) {
      params.set("min_ms", String(state.logsMinMs));
    }
    params.set("limit", "300");
    const data = await api(`/api/logs/${encodeURIComponent(state.logsFile)}?${params}`);
    state.logsEntries = data.entries || [];
    state.logsSummary = data.summary || null;
    state.logsSelected = new Set(
      [...state.logsSelected].filter((id) =>
        state.logsEntries.some((e) => String(e.index) === id)
      )
    );
    const countEl = optional("logsResultCount");
    if (countEl) {
      countEl.textContent = `${data.total_matched ?? 0} matched · ${data.total_parsed ?? 0} parsed`;
    }
    optional("logsTruncated")?.classList.toggle("hidden", !data.truncated);
    renderLogsCharts();
    renderLogsTimeline();
  }

  async function refreshLogs() {
    await loadLogsFileList();
    await loadLogEntries();
  }

  function selectedLogEntries() {
    return state.logsEntries.filter((e) => state.logsSelected.has(String(e.index)));
  }

  async function copyLogsPayload(kind) {
    const rows = selectedLogEntries();
    if (!rows.length) throw new Error("Select one or more requests");
    let text = "";
    if (kind === "curl") {
      text = rows.map((e) => e.curl).filter(Boolean).join("\n\n");
    } else if (kind === "blocks") {
      text = rows.map((e) => e.raw).join("\n");
    } else {
      text = JSON.stringify(rows, null, 2);
    }
    if (!text.trim()) throw new Error("Nothing to copy");
    await navigator.clipboard.writeText(text);
    showToast(`Copied ${rows.length} ${kind === "json" ? "JSON" : kind}`);
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

  function updateStudioVersion(info) {
    const el = optional("studioVersion");
    if (!el) return;
    const raw =
      (info && info.version) ||
      state.studioVersion ||
      "";
    if (raw) {
      state.studioVersion = String(raw);
      el.textContent = `v${state.studioVersion}`;
      el.title = `Prompt Studio ${el.textContent}`;
    } else {
      el.textContent = "v?";
      el.title = "Prompt Studio version unavailable";
    }
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
    updateStudioVersion(info);
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

  function autosizeCodeEdit(el) {
    if (!el || el.classList.contains("hidden")) return;
    el.style.height = "auto";
    const cs = window.getComputedStyle(el);
    const borderY =
      (parseFloat(cs.borderTopWidth) || 0) + (parseFloat(cs.borderBottomWidth) || 0);
    el.style.height = `${Math.ceil(el.scrollHeight + borderY)}px`;
  }

  function autosizeEditFields() {
    autosizeCodeEdit(optional("modalOriginalEdit"));
    autosizeCodeEdit(optional("modalTemplateEdit"));
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
      requestAnimationFrame(() => autosizeEditFields());
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
      <span><strong>Placeholders:</strong> ${extractPlaceholdersFromDetail(detail).length}</span>
      <span><strong>Last source:</strong> ${escapeHtml(detail.last_source || "—")}</span>
      <span><strong>Last elapsed:</strong> ${escapeHtml(formatDurationMs(detail.last_duration_ms))}</span>`;

    const ratingSelect = optional("modalRatingSelect");
    if (ratingSelect) {
      ratingSelect.value = detail.rating == null ? "" : String(detail.rating);
    }
    renderComments(detail);
    renderSourceStats(detail.stats);

    const resources = optional("modalResourcePaths");
    if (resources) {
      const profile = detail.profile || "(unscoped)";
      resources.innerHTML = `
        <div>Prompt id: <code>${escapeHtml(detail.id)}</code></div>
        <div>Profile stamp: <code>${escapeHtml(profile)}</code></div>
        <div class="muted">Open Profiles &amp; Paths for YAML and workspace directories.</div>`;
    }

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
    requestAnimationFrame(() => autosizeEditFields());
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
        } else if (state.view === "logs") {
          await refreshLogs().catch(showError);
        } else if (state.view === "config") {
          await loadConfigProfiles().catch(showError);
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
        if (state.view === "suites" || state.view === "help" || state.view === "config") {
          return;
        }
        if (state.view === "logs") {
          loadLogEntries().catch(showError);
          return;
        }
        loadPrompts();
      }, 200)
    );

    optional("logsTimeline")?.addEventListener("change", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLInputElement) || !t.dataset.logSelect) return;
      const id = t.dataset.logSelect;
      if (t.checked) state.logsSelected.add(id);
      else state.logsSelected.delete(id);
      syncLogsCopyButtons();
    });

    optional("logsTimeline")?.addEventListener("click", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      const curlBtn = t.closest("[data-log-copy-curl]");
      if (curlBtn instanceof HTMLElement && curlBtn.dataset.logCopyCurl) {
        const entry = state.logsEntries.find(
          (x) => String(x.index) === curlBtn.dataset.logCopyCurl
        );
        if (entry?.curl) {
          navigator.clipboard.writeText(entry.curl).then(() => showToast("Curl copied"));
        }
        return;
      }
      const blockBtn = t.closest("[data-log-copy-block]");
      if (blockBtn instanceof HTMLElement && blockBtn.dataset.logCopyBlock) {
        const entry = state.logsEntries.find(
          (x) => String(x.index) === blockBtn.dataset.logCopyBlock
        );
        if (entry?.raw) {
          navigator.clipboard.writeText(entry.raw).then(() => showToast("Block copied"));
        }
      }
    });

    bindClick("logsRefreshBtn", () => refreshLogs().catch(showError));
    bindClick("logsDownloadRawBtn", () => {
      if (!state.logsFile) {
        showError(new Error("No log file selected"));
        return;
      }
      window.location.href = `/api/logs/${encodeURIComponent(state.logsFile)}/raw`;
    });
    bindClick("logsCopyCurlBtn", () => copyLogsPayload("curl").catch(showError));
    bindClick("logsCopyBlocksBtn", () => copyLogsPayload("blocks").catch(showError));
    bindClick("logsCopyJsonBtn", () => copyLogsPayload("json").catch(showError));

    bindClick("configRefreshBtn", () => loadConfigProfiles().catch(showError));
    bindClick("configCopyYamlBtn", () => {
      if (!state.configYaml) {
        showError(new Error("No YAML loaded"));
        return;
      }
      navigator.clipboard.writeText(state.configYaml).then(() => showToast("YAML copied"));
    });
    bindClick("configOpenLogsBtn", () => {
      if (!state.configProfile) {
        showError(new Error("Select a profile first"));
        return;
      }
      const name = `${state.configProfile}-${state.configEnv || "dev"}.log`;
      state.logsFile = name;
      localStorage.setItem(LOGS_FILE_KEY, name);
      state.view = "logs";
      syncNav();
      refreshLogs().catch(showError);
    });
    optional("configProfileSelect")?.addEventListener("change", (e) => {
      state.configProfile = e.target.value || "";
      loadConfigDetail().catch(showError);
    });
    optional("configEnvSelect")?.addEventListener("change", (e) => {
      state.configEnv = e.target.value || "dev";
      loadConfigDetail().catch(showError);
    });
    optional("configPathCards")?.addEventListener("click", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      const btn = t.closest("[data-copy-path]");
      if (!(btn instanceof HTMLElement) || !btn.dataset.copyPath) return;
      navigator.clipboard.writeText(btn.dataset.copyPath).then(() => showToast("Path copied"));
    });

    bindClick("modalSaveRatingBtn", () => saveRating().catch(showError));
    bindClick("modalAddCommentBtn", () => addComment().catch(showError));
    optional("modalComments")?.addEventListener("click", (e) => {
      const t = e.target;
      if (!(t instanceof HTMLElement)) return;
      const del = t.closest("[data-comment-delete]");
      if (del instanceof HTMLElement && del.dataset.commentDelete) {
        deleteComment(del.dataset.commentDelete).catch(showError);
        return;
      }
      const ed = t.closest("[data-comment-edit]");
      if (ed instanceof HTMLElement && ed.dataset.commentEdit) {
        editComment(ed.dataset.commentEdit).catch(showError);
      }
    });

    const logsFileSelect = optional("logsFileSelect");
    if (logsFileSelect) {
      logsFileSelect.addEventListener("change", () => {
        state.logsFile = logsFileSelect.value;
        localStorage.setItem(LOGS_FILE_KEY, state.logsFile);
        state.logsSelected = new Set();
        loadLogEntries().catch(showError);
      });
    }
    const logsMethod = optional("logsMethodFilter");
    if (logsMethod) {
      logsMethod.addEventListener("change", () => {
        state.logsMethod = logsMethod.value;
        loadLogEntries().catch(showError);
      });
    }
    const logsStatus = optional("logsStatusFilter");
    if (logsStatus) {
      logsStatus.addEventListener("change", () => {
        state.logsStatus = logsStatus.value;
        loadLogEntries().catch(showError);
      });
    }
    const logsMinMs = optional("logsMinMs");
    if (logsMinMs) {
      logsMinMs.addEventListener(
        "input",
        debounce(() => {
          state.logsMinMs = logsMinMs.value;
          loadLogEntries().catch(showError);
        }, 250)
      );
    }
    const logsErrorsOnly = optional("logsErrorsOnly");
    if (logsErrorsOnly) {
      logsErrorsOnly.addEventListener("change", () => {
        state.logsErrorsOnly = logsErrorsOnly.checked;
        if (logsStatus) logsStatus.disabled = logsErrorsOnly.checked;
        loadLogEntries().catch(showError);
      });
    }

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
    const ratingFilter = optional("ratingFilter");
    if (ratingFilter) {
      ratingFilter.value = state.ratingFilterValue || "";
      ratingFilter.addEventListener("change", () => {
        state.ratingFilterValue = ratingFilter.value || "";
        localStorage.setItem(RATING_FILTER_KEY, state.ratingFilterValue);
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
    const originalEditEl = optional("modalOriginalEdit");
    const templateEditEl = optional("modalTemplateEdit");
    if (originalEditEl) {
      originalEditEl.addEventListener("input", () => autosizeCodeEdit(originalEditEl));
    }
    if (templateEditEl) {
      templateEditEl.addEventListener("input", () => autosizeCodeEdit(templateEditEl));
    }
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

  async function loadStudioVersion() {
    try {
      const health = await api("/api/health");
      updateStudioVersion(health);
    } catch {
      updateStudioVersion(null);
    }
  }

  async function init() {
    bindEvents();
    optional("importLabel")?.addEventListener("input", () => syncApplyImportBtn());
    optional("importCandidateList")?.addEventListener("change", () => syncApplyImportBtn());
    syncNav();
    syncLayoutButtons();
    syncExportSelectedBtn();
    await loadStudioVersion();
    await refreshLibrary();
    window.addEventListener("focus", () => pollLibraryInfo());
    setInterval(() => pollLibraryInfo(), LIBRARY_POLL_MS);
  }

  init().catch((err) => {
    console.error(err);
    $("statusLine").textContent = "Error loading library";
    loadStudioVersion().catch(() => updateStudioVersion(null));
  });
})();
