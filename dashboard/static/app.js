const state = { jobs: [], platforms: [], sourceStatus: [] };

const $ = (sel) => document.querySelector(sel);
const esc = (s) => {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
};

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

function scoreBadge(value) {
  const cls = value >= 0.7 ? "hi" : value >= 0.4 ? "mid" : "lo";
  return `<span class="badge ${cls}">${value.toFixed(2)}</span>`;
}

function renderJobs() {
  const tbody = $("#jobs-table tbody");
  tbody.innerHTML = state.jobs.map((job) => `
    <tr>
      <td><a href="${esc(job.url)}" target="_blank" rel="noopener">${esc(job.title)}</a></td>
      <td>${esc(job.company)}</td>
      <td><span class="pill">${esc(job.source)}</span></td>
      <td>${job.remote ? "Yes" : "No"}</td>
      <td>${esc(job.pay)}</td>
      <td>${scoreBadge(job.access_score)}</td>
      <td>${scoreBadge(job.overall_score)}</td>
      <td>
        <button class="applied-toggle" data-id="${job.id}" data-applied="${job.applied}">
          ${job.applied ? "Applied" : "Mark applied"}
        </button>
      </td>
      <td><input class="notes-input" data-id="${job.id}" value="${esc(job.notes)}" placeholder="Notes..."></td>
    </tr>
  `).join("");
  $("#job-count").textContent = `(${state.jobs.length})`;
}

async function loadJobs() {
  const params = new URLSearchParams();
  const source = $("#filter-source").value;
  const search = $("#search").value.trim();
  const minAccess = $("#filter-min-access").value;
  const applied = $("#filter-applied").value;
  if (source) params.set("source", source);
  if ($("#filter-remote").checked) params.set("remote_only", "true");
  if (minAccess && parseFloat(minAccess) > 0) params.set("min_access", minAccess);
  if (applied) params.set("applied", applied);
  if (search) params.set("search", search);
  params.set("sort", $("#sort").value);
  state.jobs = await api(`/api/jobs?${params}`);
  renderJobs();
}

function renderStatus() {
  const tbody = $("#status-table tbody");
  tbody.innerHTML = state.sourceStatus.map((s) => `
    <tr>
      <td>${esc(s.source)}</td>
      <td><span class="badge status-${s.status === "success" ? "ok" : "error"}">${esc(s.status)}</span></td>
      <td>${s.count_found}</td>
      <td>${esc((s.finished_at || s.started_at || "").replace("T", " ").slice(0, 16))}</td>
      <td>${esc(s.error || "")}</td>
    </tr>
  `).join("");
}

async function loadStatus() {
  state.sourceStatus = await api("/api/source-status");
  renderStatus();
}

function renderPlatforms() {
  const tbody = $("#platforms-table tbody");
  tbody.innerHTML = state.platforms.map((p) => `
    <tr>
      <td><a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.name)}</a></td>
      <td>${p.ethiopia_accessible ? '<span class="badge hi">Yes</span>' : '<span class="badge lo">No</span>'}</td>
      <td>
        <select class="platform-status" data-name="${esc(p.name)}">
          ${["not_applied", "applied", "pending"].map((s) =>
            `<option value="${s}" ${p.status === s ? "selected" : ""}>${s}</option>`).join("")}
        </select>
      </td>
      <td><input class="platform-notes" data-name="${esc(p.name)}" value="${esc(p.notes)}" placeholder="Notes..."></td>
    </tr>
  `).join("");
}

async function loadPlatforms() {
  state.platforms = await api("/api/platforms");
  renderPlatforms();
}

async function refresh() {
  const btn = $("#refresh-btn");
  btn.disabled = true;
  btn.textContent = "Refreshing...";
  await api("/api/refresh", { method: "POST" });
  await loadStatus();
  btn.disabled = false;
  btn.textContent = "Refresh now";
}

async function pollStatus() {
  const before = JSON.stringify(state.sourceStatus);
  await loadStatus();
  const after = JSON.stringify(state.sourceStatus);
  if (before !== after) {
    await loadJobs();
  }
}

$("#refresh-btn").addEventListener("click", async () => {
  await refresh();
  await pollStatus();
});

["#search", "#filter-source", "#filter-remote", "#filter-min-access", "#filter-applied", "#sort"]
  .forEach((sel) => $(sel).addEventListener("input", loadJobs));
$("#filter-remote").addEventListener("change", loadJobs);
$("#filter-applied").addEventListener("change", loadJobs);
$("#sort").addEventListener("change", loadJobs);

document.addEventListener("input", async (e) => {
  if (e.target.classList.contains("notes-input")) {
    await api(`/api/jobs/${e.target.dataset.id}`, { method: "PATCH", body: JSON.stringify({ notes: e.target.value }) });
  }
  if (e.target.classList.contains("platform-notes")) {
    await api(`/api/platforms/${encodeURIComponent(e.target.dataset.name)}`, { method: "PATCH", body: JSON.stringify({ notes: e.target.value }) });
  }
});

document.addEventListener("click", async (e) => {
  if (e.target.classList.contains("applied-toggle")) {
    const applied = e.target.dataset.applied !== "true";
    e.target.dataset.applied = String(applied);
    e.target.textContent = applied ? "Applied" : "Mark applied";
    await api(`/api/jobs/${e.target.dataset.id}`, { method: "PATCH", body: JSON.stringify({ applied }) });
  }
});

document.addEventListener("change", async (e) => {
  if (e.target.classList.contains("platform-status")) {
    await api(`/api/platforms/${encodeURIComponent(e.target.dataset.name)}`, { method: "PATCH", body: JSON.stringify({ status: e.target.value }) });
  }
});

async function init() {
  await loadStatus();
  const sources = [...new Set(state.sourceStatus.map((s) => s.source))].sort();
  const sel = $("#filter-source");
  sources.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    sel.appendChild(opt);
  });
  await Promise.all([loadJobs(), loadPlatforms()]);
  setInterval(pollStatus, 10000);
}

init();
