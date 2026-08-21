(() => {
  const LAYOUT_KEY = "promptStudio.layout";

  const state = {
    view: "all",
    tag: null,
    q: "",
    layout: localStorage.getItem(LAYOUT_KEY) === "list" ? "list" : "cards",
    prompts: [],
    suites: [],
    activePromptId: null,
    suitePickPromptId: null,
    activeSuiteId: null,
  };

  const $ = (id) => document.getElementById(id);

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

  function formatLabel(outputFormat) {
    const key = (outputFormat || "chat_text").toLowerCase();
    if (key === "json") return "JSON";
    if (key === "excel_download") return "Excel download";
    return "Text";
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
    const tags = (p.tags || []).map((t) => `<span class="chip">${escapeHtml(t)}</span>`).join("");
    const tools = (p.tools || [])
      .slice(0, 4)
      .map((t) => `<span class="chip tool">${escapeHtml(t)}</span>`)
      .join("");
    return tags + tools;
  }

  function metaStatsHtml(p) {
    const fmt = formatLabel(p.output_format);
    return `
      <div class="stat-grid">
        <div><span class="stat-key">Format</span><span class="stat-val format-badge">${escapeHtml(fmt)}</span></div>
        <div><span class="stat-key">Runs</span><span class="stat-val">${p.run_count || 0}</span></div>
        <div><span class="stat-key">Last run</span><span class="stat-val">${escapeHtml(formatWhen(p.last_run_at))}</span></div>
        <div><span class="stat-key">Created</span><span class="stat-val">${escapeHtml(formatWhen(p.created_at))}</span></div>
        <div><span class="stat-key">Placeholders</span><span class="stat-val">${p.placeholder_count || 0}</span></div>
      </div>`;
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
    const data = await api(`/api/prompts?${params}`);
    state.prompts = data.prompts || [];
    renderPrompts();
  }

  function renderPrompts() {
    const grid = $("promptGrid");
    const empty = $("emptyState");
    $("resultCount").textContent = `${state.prompts.length} prompt${state.prompts.length === 1 ? "" : "s"}`;
    syncLayoutButtons();
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
        row.className = "prompt-list-row";
        row.innerHTML = `
          <div class="list-title-cell">
            <strong>${escapeHtml(p.title)}</strong>
            <div class="chip-row compact">${chipHtml(p)}</div>
          </div>
          <span class="format-badge">${escapeHtml(formatLabel(p.output_format))}</span>
          <span>${p.run_count || 0}</span>
          <span class="muted">${escapeHtml(formatWhen(p.last_run_at))}</span>
          <div class="list-actions">
            <button type="button" class="icon-btn ${p.favorite ? "starred" : ""}" data-fav="${p.id}" title="Favorite">★</button>
            <button type="button" class="btn-primary" data-run="${p.id}">Run</button>
            <button type="button" class="btn-secondary" data-suite-add="${p.id}">Add to suite…</button>
          </div>`;
        grid.appendChild(row);
        return;
      }

      const card = document.createElement("article");
      card.className = "prompt-card";
      card.innerHTML = `
        <div class="card-top">
          <h3 class="card-title">${escapeHtml(p.title)}</h3>
          <button type="button" class="icon-btn ${p.favorite ? "starred" : ""}" data-fav="${p.id}" title="Favorite">★</button>
        </div>
        <div class="chip-row">${chipHtml(p)}</div>
        ${metaStatsHtml(p)}
        <div class="card-actions">
          <button type="button" class="btn-primary" data-run="${p.id}">Run</button>
          <button type="button" class="btn-secondary" data-suite-add="${p.id}">Add to suite…</button>
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
    if (state.view !== "suites") {
      $("statusLine").textContent = "Library";
    } else {
      $("statusLine").textContent = "Suites";
    }
  }

  function stampUpdated() {
    const t = new Date().toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    $("statusLine").textContent = `Updated ${t}`;
  }

  async function refreshLibrary() {
    await Promise.all([loadTags(), loadPrompts()]);
    stampUpdated();
  }

  async function refreshSuites() {
    await loadSuites();
    if (state.activeSuiteId) {
      await openSuite(state.activeSuiteId);
    }
    stampUpdated();
  }

  async function openRun(promptId) {
    const detail = await api(`/api/prompts/${promptId}`);
    state.activePromptId = promptId;
    $("modalTitle").textContent = detail.title;
    $("modalTemplate").textContent = detail.refined_prompt;
    $("generatedOut").value = "";
    $("modalFormatLabel").textContent = formatLabel(detail.output_format);

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
      <span><strong>Placeholders:</strong> ${(detail.placeholders || []).length}</span>`;

    const fields = $("varFields");
    fields.innerHTML = "";
    (detail.placeholders || []).forEach((name) => {
      const wrap = document.createElement("div");
      wrap.className = "var-field";
      const hint = detail.variables && detail.variables[name] != null ? String(detail.variables[name]) : "";
      const recent = (detail.recent_values && detail.recent_values[name]) || [];
      wrap.innerHTML = `<label for="var_${name}">{{${name}}}</label>
        <input id="var_${name}" name="${name}" value="${escapeAttr(hint)}" list="dl_${name}" />
        <datalist id="dl_${name}">${recent.map((v) => `<option value="${escapeAttr(v)}"></option>`).join("")}</datalist>`;
      if (recent.length) {
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
    $("runModal").showModal();
  }

  async function generate() {
    if (!state.activePromptId) return;
    const values = {};
    $("varFields").querySelectorAll("input").forEach((input) => {
      values[input.name] = input.value;
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
        ${metaStatsHtml(p)}
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
      if (t.dataset.run) openRun(t.dataset.run);
      if (t.dataset.fav) toggleFavorite(t.dataset.fav);
      if (t.dataset.suiteAdd) openSuitePicker(t.dataset.suiteAdd);
    });

    $("layoutCards").addEventListener("click", () => setLayout("cards"));
    $("layoutList").addEventListener("click", () => setLayout("list"));
    $("refreshBtn").addEventListener("click", () => refreshLibrary().catch(alert));
    $("refreshSuitesBtn").addEventListener("click", () => refreshSuites().catch(alert));

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
      if (t instanceof HTMLElement && t.dataset.run) openRun(t.dataset.run);
    });

    $("newSuiteBtn").addEventListener("click", async () => {
      const name = prompt("Suite name");
      if (!name || !name.trim()) return;
      await createSuite(name.trim());
    });

    $("closeModal").addEventListener("click", () => $("runModal").close());
    $("generateBtn").addEventListener("click", () => generate().catch(alert));
    $("copyBtn").addEventListener("click", () => copyGenerated().catch(alert));
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
    if (deepPrompt) openRun(deepPrompt).catch(() => {});
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
    await Promise.all([loadTags(), loadPrompts()]);
  }

  init().catch((err) => {
    console.error(err);
    $("statusLine").textContent = "Error loading library";
  });
})();
