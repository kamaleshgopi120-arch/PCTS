/**
 * frontend/js/admin_fleet.js
 * =============================================================================
 * PCTS — Admin Logistics Fleet & Delivery Personnel Management
 * =============================================================================
 */

let allFleetAgents = [];
let allFleetDeliveries = [];

document.addEventListener("DOMContentLoaded", async () => {
  // 1. Session Guard — Admin Role Only
  const currentUser = getCurrentUser();
  const token = getToken();

  if (!token || !currentUser) {
    window.location.href = "login.html";
    return;
  }

  if (currentUser.role !== "admin") {
    if (currentUser.role === "customer") window.location.href = "customer_dashboard.html";
    else if (currentUser.role === "delivery") window.location.href = "delivery_dashboard.html";
    else window.location.href = "login.html";
    return;
  }

  // 2. Setup event listeners
  setupAgentSearch();
  setupAddAgentModal();

  const refreshBtn = document.getElementById("btnRefreshAgents");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => loadFleetData());
  }

  // 3. Initial Data Load
  await loadFleetData();
});

/**
 * Fetch all delivery agents and current delivery tasks
 */
async function loadFleetData() {
  const tbody = document.getElementById("fleetTableBody");
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
        Loading fleet and delivery executives...
      </td>
    </tr>
  `;

  try {
    const [agents, deliveries] = await Promise.all([
      apiRequest("/api/deliveries/agents?active_only=false"),
      apiRequest("/api/deliveries?limit=100")
    ]);

    allFleetAgents = Array.isArray(agents) ? agents : [];
    allFleetDeliveries = Array.isArray(deliveries) ? deliveries : [];

    updateFleetKPIs();
    renderFleetTable();

  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 2rem; color: var(--accent-rose);">
          Error loading fleet roster: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
  }
}

/**
 * Compute and display KPI metrics
 */
function updateFleetKPIs() {
  const totalEl = document.getElementById("valTotalStaff");
  const activeEl = document.getElementById("valActiveStaff");
  const bikesEl = document.getElementById("valBikesCount");
  const vansEl = document.getElementById("valVansCount");

  const total = allFleetAgents.length;
  let active = 0;
  let bikes = 0;
  let vans = 0;

  allFleetAgents.forEach(a => {
    if (a.is_active) active++;
    const v = (a.vehicle_number || "").toLowerCase();
    if (v.includes("van") || v.includes("car") || v.includes("truck")) {
      vans++;
    } else {
      bikes++;
    }
  });

  if (totalEl) totalEl.textContent = total;
  if (activeEl) activeEl.textContent = active;
  if (bikesEl) bikesEl.textContent = bikes;
  if (vansEl) vansEl.textContent = vans;
}

/**
 * Render agents directory into DOM table
 */
function renderFleetTable() {
  const tbody = document.getElementById("fleetTableBody");
  const searchInput = document.getElementById("agentSearchInput");
  if (!tbody) return;

  const query = (searchInput ? searchInput.value : "").trim().toLowerCase();

  const filtered = allFleetAgents.filter(a => {
    if (!query) return true;
    const matchName = (a.full_name || "").toLowerCase().includes(query);
    const matchPhone = (a.phone || "").toLowerCase().includes(query);
    const matchVehicle = (a.vehicle_number || "").toLowerCase().includes(query);
    return matchName || matchPhone || matchVehicle;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          No delivery executives matching your search.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map(a => {
    const assignedTasks = allFleetDeliveries.filter(d => 
      d.delivery_person_id === a.delivery_person_id &&
      !["delivered", "returned"].includes((d.status || "").toLowerCase())
    ).length;

    const completedTasks = allFleetDeliveries.filter(d => 
      d.delivery_person_id === a.delivery_person_id &&
      ["delivered", "returned"].includes((d.status || "").toLowerCase())
    ).length;

    const statusBadge = a.is_active
      ? `<span class="badge badge-delivered"><span class="badge-dot"></span>Active Duty</span>`
      : `<span class="badge badge-failed"><span class="badge-dot"></span>Off Duty</span>`;

    return `
      <tr>
        <td style="font-weight: 700; color: var(--primary);">#AG-${a.delivery_person_id}</td>
        <td>
          <strong>${escapeHtml(a.full_name)}</strong>
        </td>
        <td>
          <a href="tel:${escapeHtml(a.phone)}" style="color: var(--accent-emerald); font-weight: 600;">
            📞 ${escapeHtml(a.phone)}
          </a>
        </td>
        <td>
          <span style="background: #f1f5f9; padding: 0.25rem 0.6rem; border-radius: 4px; font-size: 0.82rem; font-weight: 600;">
            🚚 ${escapeHtml(a.vehicle_number || 'Standard Vehicle')}
          </span>
        </td>
        <td>
          <strong style="color: var(--accent-amber);">${assignedTasks} Active</strong> 
          <span style="font-size: 0.8rem; color: var(--text-muted);">(${completedTasks} fulfilled)</span>
        </td>
        <td>${statusBadge}</td>
        <td style="text-align: right;">
          <button 
            class="btn btn-outline btn-sm" 
            onclick="toggleAgentDutyStatus(${a.delivery_person_id}, '${escapeHtml(a.full_name)}', ${a.is_active})"
            title="Toggle active / off duty"
          >
            ${a.is_active ? 'Set Off-Duty ⚪' : 'Activate Duty 🟢'}
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

/**
 * Search input listener
 */
function setupAgentSearch() {
  const searchInput = document.getElementById("agentSearchInput");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderFleetTable();
    });
  }
}

/**
 * Toggle active duty status of an agent
 */
window.toggleAgentDutyStatus = async function(agentId, agentName, currentStatus) {
  const action = currentStatus ? "mark OFF-DUTY" : "ACTIVATE for dispatch";
  if (!confirm(`Are you sure you want to ${action} for delivery executive ${agentName}?`)) {
    return;
  }

  try {
    await apiRequest(`/api/deliveries/agents/${agentId}/toggle-status`, { method: "PUT" });
    await loadFleetData();
  } catch (err) {
    alert(`Could not update agent status: ${err.message}`);
  }
};

/**
 * Configure Add Agent Modal
 */
function setupAddAgentModal() {
  const form = document.getElementById("addAgentForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const nameInput = document.getElementById("newAgentName");
    const phoneInput = document.getElementById("newAgentPhone");
    const vehicleInput = document.getElementById("newAgentVehicle");
    const emailInput = document.getElementById("newAgentEmail");
    const pwdInput = document.getElementById("newAgentPassword");
    const submitBtn = document.getElementById("btnConfirmAddAgent");

    const full_name = nameInput?.value.trim();
    const phone = phoneInput?.value.trim();
    const vehicle_number = vehicleInput?.value.trim();
    const email = emailInput?.value.trim();
    const password = pwdInput?.value.trim() || "Delivery@12345";

    if (!full_name || !phone || !email) {
      alert("Please fill all required agent fields.");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Registering...";

    try {
      await apiRequest("/api/deliveries/agents", {
        method: "POST",
        body: JSON.stringify({
          full_name,
          phone,
          vehicle_number,
          email,
          password
        })
      });

      alert(`Delivery executive ${full_name} successfully registered into the fleet!`);
      closeAddAgentModal();
      form.reset();
      await loadFleetData();

    } catch (err) {
      alert(`Could not register agent: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Register Executive 🚀";
    }
  });
}

window.openAddAgentModal = function() {
  const modal = document.getElementById("addAgentModal");
  if (modal) modal.classList.add("active");
};

window.closeAddAgentModal = function() {
  const modal = document.getElementById("addAgentModal");
  if (modal) modal.classList.remove("active");
};

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

