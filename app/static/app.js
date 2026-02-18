const state = {
  token: localStorage.getItem("pot_token") || "",
  user: null,
  dashboardData: null,
  profiles: [],
  activePeerId: "",
  toastTimer: null,
  chatPollTimer: null,
};

const refs = {
  authBtn: document.getElementById("authBtn"),
  toast: document.getElementById("toast"),
  overviewStats: document.getElementById("overviewStats"),
  topPairs: document.getElementById("topPairs"),
  nonObviousPairs: document.getElementById("nonObviousPairs"),
  profileSelect: document.getElementById("profileSelect"),
  profileMatches: document.getElementById("profileMatches"),
  refreshBtn: document.getElementById("refreshBtn"),
  attendeeSearch: document.getElementById("attendeeSearch"),
  attendeeRole: document.getElementById("attendeeRole"),
  attendeeRefresh: document.getElementById("attendeeRefresh"),
  attendeeList: document.getElementById("attendeeList"),
  attendeeCount: document.getElementById("attendeeCount"),
  homeViewMatches: document.getElementById("homeViewMatches"),
  homeOpenDashboard: document.getElementById("homeOpenDashboard"),
  registerForm: document.getElementById("registerForm"),
  loginForm: document.getElementById("loginForm"),
  profileForm: document.getElementById("profileForm"),
  chatAuthHint: document.getElementById("chatAuthHint"),
  chatLayout: document.getElementById("chatLayout"),
  peerList: document.getElementById("peerList"),
  chatMessages: document.getElementById("chatMessages"),
  chatInput: document.getElementById("chatInput"),
  chatSendBtn: document.getElementById("chatSendBtn"),
  chatThreadTitle: document.getElementById("chatThreadTitle"),
};

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function showToast(message, isError = false) {
  if (!refs.toast) return;
  refs.toast.textContent = message;
  refs.toast.classList.remove("error");
  if (isError) refs.toast.classList.add("error");
  refs.toast.classList.add("show");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => refs.toast.classList.remove("show"), 1900);
}

async function api(path, options = {}, requireAuth = false) {
  const headers = { ...(options.headers || {}) };
  if (!headers["Content-Type"] && options.body && typeof options.body === "string") {
    headers["Content-Type"] = "application/json";
  }
  if (requireAuth) {
    if (!state.token) throw new Error("Not authenticated");
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(path, { ...options, headers });
  let payload = {};
  try {
    payload = await response.json();
  } catch (_err) {
    payload = {};
  }
  if (!response.ok) {
    const detail = payload.detail || payload.error || `Request failed (${response.status})`;
    throw new Error(detail);
  }
  return payload;
}

function routeForPath(pathname) {
  if (pathname.startsWith("/dashboard")) return "/dashboard";
  if (pathname.startsWith("/attendees")) return "/attendees";
  if (pathname.startsWith("/chat")) return "/chat";
  if (pathname.startsWith("/auth")) return "/auth";
  return "/";
}

function setActiveRoute(route) {
  document.querySelectorAll(".main-nav a").forEach((a) => {
    const isActive = a.dataset.route === route;
    a.classList.toggle("active", isActive);
  });
  document.querySelectorAll(".view").forEach((view) => view.classList.add("hidden"));
  const target = document.getElementById(`view-${route === "/" ? "home" : route.slice(1)}`);
  if (target) target.classList.remove("hidden");
}

async function navigate(path, replace = false) {
  const route = routeForPath(path);
  if (replace) {
    history.replaceState({}, "", route);
  } else {
    history.pushState({}, "", route);
  }
  setActiveRoute(route);
  await onRouteEnter(route);
}

function wireNav() {
  document.querySelectorAll("[data-route]").forEach((link) => {
    link.addEventListener("click", async (event) => {
      event.preventDefault();
      const route = link.dataset.route || "/";
      await navigate(route);
    });
  });
  window.addEventListener("popstate", async () => {
    const route = routeForPath(location.pathname);
    setActiveRoute(route);
    await onRouteEnter(route);
  });
}

function stat(label, value) {
  return `<div class="stat"><div class="label">${escapeHtml(label)}</div><div class="value">${escapeHtml(value)}</div></div>`;
}

function statusBadge(status) {
  const safe = status || "pending";
  return `<span class="badge badge-${safe}">${escapeHtml(safe)}</span>`;
}

function riskBadge(level) {
  const safe = level || "medium";
  return `<span class="badge badge-risk-${safe}">${escapeHtml(safe)} risk</span>`;
}

function roleBadge(role) {
  const safe = role || "attendee";
  return `<span class="badge badge-pending">${escapeHtml(safe)}</span>`;
}

function renderOverview(overview) {
  const risk = overview.risk_distribution || { low: 0, medium: 0, high: 0 };
  refs.overviewStats.innerHTML = [
    stat("Attendees", overview.attendee_count),
    stat("Top Intro Pairs", overview.recommended_intro_count),
    stat("Actioned Intros", overview.actioned_intro_count || 0),
    stat("Low Risk", risk.low || 0),
    stat("Medium Risk", risk.medium || 0),
    stat("High Risk", risk.high || 0),
  ].join("");
}

function renderTopPairs(items) {
  refs.topPairs.innerHTML = items
    .map(
      (row, index) => `
      <article class="item">
        <h3>#${index + 1}: ${escapeHtml(row.from_name)} ↔ ${escapeHtml(row.to_name)}</h3>
        <p class="meta">Score ${escapeHtml(row.score)} | Confidence ${escapeHtml(row.confidence || "-")} | ${riskBadge(row.risk_level)} | ${statusBadge(row.action?.status)}</p>
        <p>${escapeHtml(row.rationale)}</p>
        <p class="meta">${escapeHtml((row.risk_reasons || []).join(", "))}</p>
      </article>
    `,
    )
    .join("");
}

function renderNonObvious(items) {
  refs.nonObviousPairs.innerHTML = items
    .map(
      (row, index) => `
      <article class="item">
        <h3>#${index + 1}: ${escapeHtml(row.from_name)} ↔ ${escapeHtml(row.to_name)}</h3>
        <p class="meta">Score ${escapeHtml(row.score)} | Novelty ${escapeHtml(row.novelty_score)} | ${riskBadge(row.risk_level)}</p>
        <p>${escapeHtml(row.rationale)}</p>
      </article>
    `,
    )
    .join("");
}

function renderProfileOptions(profileMap) {
  const current = refs.profileSelect.value;
  const options = Object.keys(profileMap || {});
  const names = Object.fromEntries(state.profiles.map((p) => [p.id, p.name]));
  refs.profileSelect.innerHTML = options
    .map((id) => `<option value="${escapeHtml(id)}">${escapeHtml(names[id] || id)}</option>`)
    .join("");
  if (current && options.includes(current)) {
    refs.profileSelect.value = current;
  } else if (options.length > 0) {
    refs.profileSelect.value = options[0];
  }
}

function bindSaveButtons() {
  document.querySelectorAll(".save-action-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await saveAction(btn.dataset.from, btn.dataset.to);
    });
  });
  document.querySelectorAll('[id^="status-"]').forEach((statusEl) => {
    statusEl.addEventListener("change", () => {
      const card = document.getElementById(`match-${statusEl.id.replace("status-", "")}`);
      const original = statusEl.dataset.originalStatus || "pending";
      if (!card) return;
      card.classList.remove("status-pending", "status-approved", "status-rejected");
      card.classList.add(`status-${statusEl.value}`);
      if (statusEl.value !== original) card.classList.add("status-changed");
      else card.classList.remove("status-changed");
    });
  });
}

function renderProfileMatches(profileId) {
  const matches = state.dashboardData?.per_profile?.[profileId] || [];
  refs.profileMatches.innerHTML = matches
    .map(
      (m) => `
      <article class="item profile-item status-${escapeHtml(m.action?.status || "pending")}" id="match-${escapeHtml(profileId)}-${escapeHtml(m.target_id)}">
        <h3>Priority ${escapeHtml(m.priority_rank)}: ${escapeHtml(m.target_name)}</h3>
        <p class="meta">Score ${escapeHtml(m.score)} | Fit ${escapeHtml(m.fit_score)} | Complementarity ${escapeHtml(m.complementarity_score)} | Readiness ${escapeHtml(m.readiness_score)} | Confidence ${escapeHtml(m.confidence)}</p>
        <p class="meta">Risk: ${riskBadge(m.risk_level)} | Status: ${statusBadge(m.action?.status)}</p>
        <p class="meta">${escapeHtml((m.risk_reasons || []).join(", "))}</p>
        <p>${escapeHtml(m.rationale)}</p>
        <div class="action-row">
          <select id="status-${escapeHtml(profileId)}-${escapeHtml(m.target_id)}" data-original-status="${escapeHtml(m.action?.status || "pending")}">
            <option value="pending" ${m.action?.status === "pending" ? "selected" : ""}>pending</option>
            <option value="approved" ${m.action?.status === "approved" ? "selected" : ""}>approved</option>
            <option value="rejected" ${m.action?.status === "rejected" ? "selected" : ""}>rejected</option>
          </select>
          <input id="notes-${escapeHtml(profileId)}-${escapeHtml(m.target_id)}" placeholder="Organizer notes" value="${escapeHtml(m.action?.notes || "")}" />
          <button data-from="${escapeHtml(profileId)}" data-to="${escapeHtml(m.target_id)}" class="btn primary save-action-btn">Save</button>
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
  try {
    await api(
      "/api/actions",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from_id: fromId,
          to_id: toId,
          status: statusEl?.value || "pending",
          notes: notesEl?.value || "",
        }),
      },
      false,
    );
    if (statusEl) statusEl.dataset.originalStatus = statusEl.value;
    if (cardEl) {
      cardEl.classList.remove("status-changed");
      cardEl.classList.add("saved-flash");
      setTimeout(() => cardEl.classList.remove("saved-flash"), 900);
    }
    showToast("Saved successfully");
    await loadDashboard();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function loadProfiles() {
  const data = await api("/api/profiles");
  state.profiles = data.profiles || [];
}

async function loadDashboard() {
  const data = await api("/api/dashboard");
  state.dashboardData = data;
  renderOverview(data.overview || {});
  renderTopPairs(data.top_intro_pairs || []);
  renderNonObvious(data.top_non_obvious_pairs || []);
  renderProfileOptions(data.per_profile || {});
  if (refs.profileSelect.value) {
    renderProfileMatches(refs.profileSelect.value);
  }
}

async function loadAttendees() {
  const search = refs.attendeeSearch.value.trim();
  const role = refs.attendeeRole.value;
  const query = new URLSearchParams();
  if (search) query.set("search", search);
  if (role) query.set("role", role);
  const data = await api(`/api/attendees?${query.toString()}`);
  refs.attendeeCount.textContent = `${data.count} decision-makers registered`;
  refs.attendeeList.innerHTML = (data.attendees || [])
    .map(
      (a) => `
      <article class="item">
        <h3>${escapeHtml(a.name)} ${roleBadge(a.role)}</h3>
        <p class="meta">${escapeHtml(a.title)} · ${escapeHtml(a.organization)}</p>
        <p>${escapeHtml(a.bio || "No bio provided yet.")}</p>
        <p class="meta">Website: ${escapeHtml(a.website || "-")} | Social signals: ${(a.enrichment?.inferred_tags || []).slice(0, 3).map(escapeHtml).join(", ") || "-"}</p>
      </article>
    `,
    )
    .join("");
}

function setSession(token, user) {
  state.token = token || "";
  state.user = user || null;
  if (state.token) localStorage.setItem("pot_token", state.token);
  else localStorage.removeItem("pot_token");
  updateAuthButton();
}

function updateAuthButton() {
  if (!refs.authBtn) return;
  if (state.user) {
    refs.authBtn.textContent = `Logout (${state.user.full_name})`;
    refs.authBtn.onclick = async () => {
      setSession("", null);
      showToast("Signed out");
      await navigate("/");
    };
  } else {
    refs.authBtn.textContent = "Sign in";
    refs.authBtn.onclick = async () => navigate("/auth");
  }
}

async function tryRestoreSession() {
  if (!state.token) return;
  try {
    const data = await api("/api/auth/me", {}, true);
    state.user = data.user;
  } catch (_error) {
    setSession("", null);
  }
}

async function handleRegisterSubmit(event) {
  event.preventDefault();
  const formData = new FormData(refs.registerForm);
  const payload = {
    full_name: formData.get("full_name"),
    email: formData.get("email"),
    password: formData.get("password"),
    title: formData.get("title") || "",
    organization: formData.get("organization") || "",
    role: formData.get("role") || "attendee",
    website: formData.get("website") || "",
    bio: formData.get("bio") || "",
    social_links: { linkedin: formData.get("linkedin") || "" },
    focus: [],
    looking_for: [],
  };
  try {
    const data = await api("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setSession(data.token, data.user);
    hydrateProfileForm(data.user);
    showToast("Account created");
    await loadProfiles();
    await loadAttendees();
    await navigate("/chat");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  const formData = new FormData(refs.loginForm);
  try {
    const data = await api("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });
    setSession(data.token, data.user);
    hydrateProfileForm(data.user);
    showToast("Signed in successfully");
    await loadProfiles();
    await loadAttendees();
    await navigate("/chat");
  } catch (error) {
    showToast(error.message, true);
  }
}

function hydrateProfileForm(user) {
  if (!refs.profileForm || !user) return;
  refs.profileForm.full_name.value = user.full_name || "";
  refs.profileForm.title.value = user.title || "";
  refs.profileForm.organization.value = user.organization || "";
  refs.profileForm.role.value = user.role || "attendee";
  refs.profileForm.website.value = "";
  refs.profileForm.linkedin.value = "";
  refs.profileForm.bio.value = "";
}

async function handleProfileUpdate(event) {
  event.preventDefault();
  if (!state.user) {
    showToast("Sign in first", true);
    return;
  }
  const formData = new FormData(refs.profileForm);
  const payload = {
    full_name: formData.get("full_name"),
    title: formData.get("title") || "",
    organization: formData.get("organization") || "",
    role: formData.get("role") || "attendee",
    website: formData.get("website") || "",
    bio: formData.get("bio") || "",
    social_links: { linkedin: formData.get("linkedin") || "" },
    focus: [],
    looking_for: [],
  };
  try {
    const data = await api(
      "/api/profile/me",
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      true,
    );
    state.user = data.user;
    updateAuthButton();
    showToast("Profile updated");
    await loadProfiles();
    await loadAttendees();
    await loadDashboard();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function loadChatPeers() {
  if (!state.user) return [];
  const data = await api("/api/chat/peers", {}, true);
  return data.peers || [];
}

function renderPeerList(peers) {
  refs.peerList.innerHTML = peers
    .map(
      (peer) => `
      <div class="chat-peer ${peer.user_id === state.activePeerId ? "active" : ""}" data-peer-id="${escapeHtml(peer.user_id)}">
        <strong>${escapeHtml(peer.full_name)}</strong>
        <p class="meta">${escapeHtml(peer.title)} · ${escapeHtml(peer.organization)}</p>
        <p class="meta">${escapeHtml(peer.latest_message || "No messages yet")}</p>
      </div>
    `,
    )
    .join("");
  document.querySelectorAll(".chat-peer").forEach((el) => {
    el.addEventListener("click", async () => {
      state.activePeerId = el.dataset.peerId;
      await renderChatView();
    });
  });
}

async function loadChatMessages(peerUserId) {
  if (!peerUserId) return [];
  const data = await api(`/api/chat/messages/${encodeURIComponent(peerUserId)}`, {}, true);
  return data.messages || [];
}

function renderChatMessages(messages) {
  refs.chatMessages.innerHTML = messages
    .map((m) => {
      const mine = m.from_user_id === state.user?.id;
      return `
      <div class="chat-bubble ${mine ? "mine" : "theirs"}">
        <div>${escapeHtml(m.body)}</div>
        <div class="meta">${escapeHtml(m.created_at)}</div>
      </div>
    `;
    })
    .join("");
  refs.chatMessages.scrollTop = refs.chatMessages.scrollHeight;
}

async function sendChatMessage() {
  const peerId = state.activePeerId;
  const body = refs.chatInput.value.trim();
  if (!peerId || !body) return;
  try {
    await api(
      "/api/chat/messages",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to_user_id: peerId, body }),
      },
      true,
    );
    refs.chatInput.value = "";
    await renderChatView();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function renderChatView() {
  if (!state.user) {
    refs.chatAuthHint.classList.remove("hidden");
    refs.chatLayout.classList.add("hidden");
    return;
  }
  refs.chatAuthHint.classList.add("hidden");
  refs.chatLayout.classList.remove("hidden");

  const peers = await loadChatPeers();
  renderPeerList(peers);
  if (!state.activePeerId && peers.length > 0) {
    state.activePeerId = peers[0].user_id;
  }
  const activePeer = peers.find((p) => p.user_id === state.activePeerId);
  refs.chatThreadTitle.textContent = activePeer
    ? `Conversation with ${activePeer.full_name}`
    : "Conversation";
  if (state.activePeerId) {
    const messages = await loadChatMessages(state.activePeerId);
    renderChatMessages(messages);
  } else {
    refs.chatMessages.innerHTML = `<p class="meta">No matched peers yet. Your peer list appears after matching.</p>`;
  }
}

async function onRouteEnter(route) {
  clearInterval(state.chatPollTimer);
  if (route === "/dashboard") {
    await loadProfiles();
    await loadDashboard();
  }
  if (route === "/attendees") {
    await loadAttendees();
  }
  if (route === "/chat") {
    await renderChatView();
    state.chatPollTimer = setInterval(async () => {
      if (routeForPath(location.pathname) === "/chat" && state.user) {
        await renderChatView();
      }
    }, 7000);
  }
  if (route === "/auth" && state.user) {
    hydrateProfileForm(state.user);
  }
}

function wireEvents() {
  refs.profileSelect.addEventListener("change", (event) => {
    renderProfileMatches(event.target.value);
  });
  refs.refreshBtn.addEventListener("click", async () => {
    await loadProfiles();
    await loadDashboard();
    showToast("Dashboard refreshed");
  });
  refs.attendeeRefresh.addEventListener("click", async () => loadAttendees());
  refs.attendeeSearch.addEventListener("input", async () => loadAttendees());
  refs.attendeeRole.addEventListener("change", async () => loadAttendees());
  refs.homeViewMatches.addEventListener("click", async () => navigate("/attendees"));
  refs.homeOpenDashboard.addEventListener("click", async () => navigate("/dashboard"));
  refs.registerForm.addEventListener("submit", handleRegisterSubmit);
  refs.loginForm.addEventListener("submit", handleLoginSubmit);
  refs.profileForm.addEventListener("submit", handleProfileUpdate);
  refs.chatSendBtn.addEventListener("click", sendChatMessage);
  refs.chatInput.addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      await sendChatMessage();
    }
  });
}

(async function init() {
  wireNav();
  wireEvents();
  await tryRestoreSession();
  updateAuthButton();
  await loadProfiles();
  const route = routeForPath(location.pathname);
  setActiveRoute(route);
  await onRouteEnter(route);
})();
