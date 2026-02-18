const overviewStats = document.getElementById("overviewStats");
const topPairs = document.getElementById("topPairs");
const nonObviousPairs = document.getElementById("nonObviousPairs");
const profileSelect = document.getElementById("profileSelect");
const profileMatches = document.getElementById("profileMatches");
const refreshBtn = document.getElementById("refreshBtn");
const toast = document.getElementById("toast");

let dashboardData = null;
let profiles = [];
let toastTimer = null;

function stat(label, value) {
  return `<div class="stat"><div class="label">${label}</div><div class="value">${value}</div></div>`;
}

function renderOverview(overview) {
  const risk = overview.risk_distribution || { low: 0, medium: 0, high: 0 };
  overviewStats.innerHTML = [
    stat("Attendees", overview.attendee_count),
    stat("Top Intro Pairs", overview.recommended_intro_count),
    stat("Actioned Intros", overview.actioned_intro_count || 0),
    stat("Low Risk", risk.low || 0),
    stat("Medium Risk", risk.medium || 0),
    stat("High Risk", risk.high || 0),
    stat("Model", "Weighted + Explainable"),
  ].join("");
}

function statusBadge(status) {
  const safe = status || "pending";
  return `<span class="badge badge-${safe}">${safe}</span>`;
}

function riskBadge(riskLevel) {
  const safe = riskLevel || "medium";
  return `<span class="badge badge-risk-${safe}">${safe} risk</span>`;
}

function renderTopPairs(items) {
  topPairs.innerHTML = items
    .map(
      (row, idx) => `
      <article class="item">
        <h3>#${idx + 1}: ${row.from_name} ↔ ${row.to_name}</h3>
        <p class="meta">Score: ${row.score} | Confidence: ${row.confidence || "-"} | ${riskBadge(row.risk_level)} | ${statusBadge(row.action?.status)}</p>
        <p>${row.rationale}</p>
        <p class="meta">${(row.risk_reasons || []).join(", ")}</p>
      </article>
    `,
    )
    .join("");
}

function renderNonObvious(items) {
  nonObviousPairs.innerHTML = items
    .map(
      (row, idx) => `
      <article class="item">
        <h3>#${idx + 1}: ${row.from_name} ↔ ${row.to_name}</h3>
        <p class="meta">Score: ${row.score} | Novelty: ${row.novelty_score} | ${riskBadge(row.risk_level)}</p>
        <p>${row.rationale}</p>
      </article>
    `,
    )
    .join("");
}

function renderProfileOptions(profileMap) {
  const keys = Object.keys(profileMap);
  const nameById = Object.fromEntries(profiles.map((p) => [p.id, p.name]));
  profileSelect.innerHTML = keys
    .map((id) => `<option value="${id}">${nameById[id] || id}</option>`)
    .join("");
}

function renderProfileMatches(profileId) {
  const matches = dashboardData.per_profile[profileId] || [];
  profileMatches.innerHTML = matches
    .map(
      (m) => `
      <article class="item profile-item status-${m.action?.status || "pending"}" id="match-${profileId}-${m.target_id}">
        <h3>Priority ${m.priority_rank}: ${m.target_name}</h3>
        <p class="meta">Score ${m.score} | Fit ${m.fit_score} | Complementarity ${m.complementarity_score} | Readiness ${m.readiness_score} | Confidence ${m.confidence}</p>
        <p class="meta">Risk: ${riskBadge(m.risk_level)} | Status: ${statusBadge(m.action?.status)}</p>
        <p class="meta">${(m.risk_reasons || []).join(", ")}</p>
        <p>${m.rationale}</p>
        <div class="action-row">
          <select id="status-${profileId}-${m.target_id}" data-original-status="${m.action?.status || "pending"}">
            <option value="pending" ${m.action?.status === "pending" ? "selected" : ""}>pending</option>
            <option value="approved" ${m.action?.status === "approved" ? "selected" : ""}>approved</option>
            <option value="rejected" ${m.action?.status === "rejected" ? "selected" : ""}>rejected</option>
          </select>
          <input id="notes-${profileId}-${m.target_id}" placeholder="Organizer notes" value="${(m.action?.notes || "").replaceAll('"', "&quot;")}" />
          <button data-from="${profileId}" data-to="${m.target_id}" class="save-action-btn">Save</button>
        </div>
      </article>
    `,
    )
    .join("");

  bindSaveButtons();
}

async function saveAction(fromId, toId) {
  const statusEl = document.getElementById(`status-${fromId}-${toId}`);
  const notesEl = document.getElementById(`notes-${fromId}-${toId}`);
  const cardEl = document.getElementById(`match-${fromId}-${toId}`);
  const payload = {
    from_id: fromId,
    to_id: toId,
    status: statusEl?.value || "pending",
    notes: notesEl?.value || "",
  };
  const res = await fetch("/api/actions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    showToast("Save failed. Please retry.", true);
    return;
  }
  if (statusEl) {
    statusEl.dataset.originalStatus = statusEl.value;
  }
  if (cardEl) {
    cardEl.classList.remove("status-changed");
    cardEl.classList.add("saved-flash");
    setTimeout(() => cardEl.classList.remove("saved-flash"), 900);
  }
  showToast("Saved successfully");
  await loadDashboard();
  profileSelect.value = fromId;
  renderProfileMatches(fromId);
}

function showToast(message, isError = false) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("error");
  if (isError) {
    toast.classList.add("error");
  }
  toast.classList.add("show");
  if (toastTimer) {
    clearTimeout(toastTimer);
  }
  toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 1800);
}

function bindStatusChangeTracking() {
  document.querySelectorAll('[id^="status-"]').forEach((statusEl) => {
    statusEl.addEventListener("change", () => {
      const fromTo = statusEl.id.replace("status-", "");
      const cardEl = document.getElementById(`match-${fromTo}`);
      const original = statusEl.dataset.originalStatus || "pending";
      if (!cardEl) return;
      cardEl.classList.remove("status-pending", "status-approved", "status-rejected");
      cardEl.classList.add(`status-${statusEl.value}`);
      if (statusEl.value !== original) {
        cardEl.classList.add("status-changed");
      } else {
        cardEl.classList.remove("status-changed");
      }
    });
  });
}

function bindSaveButtons() {
  document.querySelectorAll(".save-action-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await saveAction(btn.dataset.from, btn.dataset.to);
    });
  });
  bindStatusChangeTracking();
}

async function loadProfiles() {
  const res = await fetch("/api/profiles");
  const data = await res.json();
  profiles = data.profiles || [];
}

async function loadDashboard() {
  const res = await fetch("/api/dashboard");
  dashboardData = await res.json();

  renderOverview(dashboardData.overview);
  renderTopPairs(dashboardData.top_intro_pairs);
  renderNonObvious(dashboardData.top_non_obvious_pairs || []);
  renderProfileOptions(dashboardData.per_profile);

  if (profileSelect.value) {
    renderProfileMatches(profileSelect.value);
  } else {
    const first = Object.keys(dashboardData.per_profile)[0];
    profileSelect.value = first;
    renderProfileMatches(first);
  }
}

profileSelect.addEventListener("change", (e) => {
  renderProfileMatches(e.target.value);
});

refreshBtn.addEventListener("click", async () => {
  await loadProfiles();
  await loadDashboard();
});

(async function init() {
  await loadProfiles();
  await loadDashboard();
})();
