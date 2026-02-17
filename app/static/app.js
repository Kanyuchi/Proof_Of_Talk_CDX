const overviewStats = document.getElementById("overviewStats");
const topPairs = document.getElementById("topPairs");
const profileSelect = document.getElementById("profileSelect");
const profileMatches = document.getElementById("profileMatches");
const refreshBtn = document.getElementById("refreshBtn");

let dashboardData = null;
let profiles = [];

function stat(label, value) {
  return `<div class="stat"><div class="label">${label}</div><div class="value">${value}</div></div>`;
}

function renderOverview(overview) {
  overviewStats.innerHTML = [
    stat("Attendees", overview.attendee_count),
    stat("Top Intro Pairs", overview.recommended_intro_count),
    stat("Model", "Weighted + Explainable"),
  ].join("");
}

function renderTopPairs(items) {
  topPairs.innerHTML = items
    .map(
      (row, idx) => `
      <article class="item">
        <h3>#${idx + 1}: ${row.from_name} ↔ ${row.to_name}</h3>
        <p class="meta">Score: ${row.score}</p>
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
      <article class="item">
        <h3>Priority ${m.priority_rank}: ${m.target_name}</h3>
        <p class="meta">Score ${m.score} | Fit ${m.fit_score} | Complementarity ${m.complementarity_score} | Readiness ${m.readiness_score} | Confidence ${m.confidence}</p>
        <p>${m.rationale}</p>
      </article>
    `,
    )
    .join("");
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
