/**
 * frontend/js/dashboard.js
 * =============================================================================
 * PCTS — Admin Operations & Parcel Management Dashboard
 * =============================================================================
 */

let allParcels = [];
let allAgents = [];
let activeFilter = "ALL";
let activeParcelMap = new Map(); // tracking_id -> parcel_id

document.addEventListener("DOMContentLoaded", () => {
  initAdminDashboard();
});

async function initAdminDashboard() {
  const tableBody = document.getElementById("adminTableBody");
  if (!tableBody) return;

  // 1. Guard check: Require admin privileges
  const currentUser = getCurrentUser();
  const token = getToken();

  if (!token || !currentUser || currentUser.role !== "admin") {
    alert("Administrative access required. Redirecting to login portal.");
    window.location.href = "login.html";
    return;
  }

  // 2. Set up event listeners
  setupFilterTabs();
  setupSearch();
  setupAssignModal();

  const refreshBtn = document.getElementById("btnRefreshTable");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadDashboardData();
    });
  }

  // 3. Initial Data Fetch
  await Promise.allSettled([
    loadKPIStats(),
    loadAgents(),
    loadDashboardData()
  ]);
}

/**
 * Fetch KPI statistics from reports endpoints
 */
async function loadKPIStats() {
  try {
    const [parcelReport, paymentReport] = await Promise.all([
      apiRequest("/api/reports/parcels"),
      apiRequest("/api/reports/payments")
    ]);

    // Update KPI Card values
    const totalParcelsEl = document.getElementById("valTotalParcels");
    const activeDelivEl = document.getElementById("valActiveDeliveries");
    const deliveredEl = document.getElementById("valDeliveredParcels");
    const totalRevenueEl = document.getElementById("valTotalRevenue");

    if (totalParcelsEl && parcelReport.total_parcels !== undefined) {
      totalParcelsEl.textContent = parcelReport.total_parcels.toLocaleString();
    }

    if (parcelReport.breakdown) {
      let activeCount = 0;
      let deliveredCount = 0;

      parcelReport.breakdown.forEach(b => {
        const s = (b.status || "").toLowerCase();
        if (s.includes("transit") || s.includes("out for delivery") || s.includes("picked")) {
          activeCount += b.count;
        } else if (s.includes("delivered")) {
          deliveredCount += b.count;
        }
      });

      if (activeDelivEl) activeDelivEl.textContent = activeCount.toLocaleString();
      if (deliveredEl) deliveredEl.textContent = deliveredCount.toLocaleString();
    }

    if (totalRevenueEl && paymentReport.total_revenue !== undefined) {
      totalRevenueEl.textContent = formatCurrency(paymentReport.total_revenue);
    }

  } catch (err) {
    console.warn("Could not load full KPI reports:", err);
  }
}

/**
 * Load active delivery staff for assignment modal dropdown
 */
async function loadAgents() {
  try {
    const agents = await apiRequest("/api/deliveries/agents");
    allAgents = agents || [];

    const selectEl = document.getElementById("modalAgentSelect");
    if (!selectEl) return;

    selectEl.innerHTML = '<option value="" disabled selected>Choose a delivery executive</option>';
    allAgents.forEach(agent => {
      const opt = document.createElement("option");
      opt.value = agent.delivery_person_id;
      opt.textContent = `${agent.full_name} (${agent.vehicle_number || 'Vehicle'}) • Phone: ${agent.phone}`;
      selectEl.appendChild(opt);
    });
  } catch (err) {
    console.warn("Could not load delivery agents list:", err);
  }
}

/**
 * Fetch parcels list from backend
 */
async function loadDashboardData() {
  const tableBody = document.getElementById("adminTableBody");
  if (!tableBody) return;

  tableBody.innerHTML = `
    <tr>
      <td colspan="9" style="text-align: center; padding: 2rem; color: var(--text-muted);">
        Loading parcels from database...
      </td>
    </tr>
  `;

  try {
    const parcels = await apiRequest("/api/parcels?limit=100");
    allParcels = parcels || [];
    activeParcelMap.clear();

    allParcels.forEach(p => {
      activeParcelMap.set(p.tracking_id, p.parcel_id);
    });

    renderParcelsTable();

  } catch (err) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align: center; padding: 2rem; color: var(--accent-rose);">
          Error loading parcels: ${err.message}
        </td>
      </tr>
    `;
  }
}

/**
 * Filter and render parcels into DOM table
 */
function renderParcelsTable() {
  const tableBody = document.getElementById("adminTableBody");
  const searchInput = document.getElementById("adminTableSearch");
  if (!tableBody) return;

  const searchQuery = (searchInput ? searchInput.value : "").trim().toLowerCase();

  const filtered = allParcels.filter(p => {
    // 1. Status Filter
    if (activeFilter !== "ALL") {
      const pStatus = (p.status || "").toLowerCase();
      const targetFilter = activeFilter.toLowerCase();
      if (!pStatus.includes(targetFilter)) {
        return false;
      }
    }

    // 2. Search Query Filter
    if (searchQuery) {
      const matchTrack = (p.tracking_id || "").toLowerCase().includes(searchQuery);
      const matchSender = (p.sender_name || "").toLowerCase().includes(searchQuery);
      const matchReceiver = (p.receiver_name || "").toLowerCase().includes(searchQuery);
      const matchCity = (p.destination_city || "").toLowerCase().includes(searchQuery) ||
                        (p.source_city || "").toLowerCase().includes(searchQuery);
      if (!matchTrack && !matchSender && !matchReceiver && !matchCity) {
        return false;
      }
    }

    return true;
  });

  if (filtered.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          No matching parcels found for the current filters.
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = filtered.map(p => {
    const statusBadge = getStatusBadgeHtml(p.status);
    const paymentBadge = getPaymentBadgeHtml(p.payment_status);
    const route = `${p.source_city} &rarr; ${p.destination_city}`;
    const weight = `${p.weight_kg} kg`;
    const isDelivered = (p.status || "").toLowerCase().includes("delivered");

    return `
      <tr>
        <td>
          <a href="track.html?id=${encodeURIComponent(p.tracking_id)}" style="font-weight: 700; color: var(--accent-cyan);">
            ${p.tracking_id}
          </a>
        </td>
        <td>${escapeHtml(p.sender_name)}</td>
        <td>${escapeHtml(p.receiver_name)}</td>
        <td>${route}</td>
        <td>${weight}</td>
        <td>${statusBadge}</td>
        <td>${paymentBadge}</td>
        <td>${escapeHtml(p.location || 'Pending Dispatch')}</td>
        <td style="text-align: right;">
          ${
            isDelivered
              ? `<a href="track.html?id=${encodeURIComponent(p.tracking_id)}" class="btn btn-outline btn-sm">Logs</a>`
              : `<button class="btn btn-primary btn-sm" onclick="openAssignModal('${p.tracking_id}', ${p.parcel_id})">Assign</button>`
          }
        </td>
      </tr>
    `;
  }).join("");
}

/**
 * Configure tabs for filtering by status
 */
function setupFilterTabs() {
  const tabs = document.querySelectorAll("#statusFilterTabs .tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      activeFilter = tab.getAttribute("data-filter") || "ALL";
      renderParcelsTable();
    });
  });
}

/**
 * Search input listener
 */
function setupSearch() {
  const searchInput = document.getElementById("adminTableSearch");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderParcelsTable();
    });
  }
}

/**
 * Modal dialog submission handler
 */
function setupAssignModal() {
  const form = document.getElementById("assignAgentForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const trackingIdInput = document.getElementById("modalTrackingId");
    const agentSelect = document.getElementById("modalAgentSelect");
    const notesInput = document.getElementById("modalAssignNotes");
    const submitBtn = document.getElementById("btnConfirmAssign");

    const trackingId = trackingIdInput?.value;
    const agentId = parseInt(agentSelect?.value, 10);
    const notes = notesInput?.value.trim() || "Assigned via Admin Command Center";

    const parcelId = activeParcelMap.get(trackingId);
    if (!parcelId) {
      alert("Could not resolve parcel record for this tracking ID.");
      return;
    }

    if (!agentId) {
      alert("Please select a delivery agent.");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Assigning...";

    try {
      await apiRequest("/api/deliveries", {
        method: "POST",
        body: JSON.stringify({
          parcel_id: parcelId,
          delivery_person_id: agentId,
          notes: notes
        })
      });

      alert(`Parcel ${trackingId} successfully assigned to delivery executive!`);
      closeAssignModal();
      loadDashboardData();
      loadKPIStats();

    } catch (err) {
      alert(`Assignment failed: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Confirm Assignment";
    }
  });
}

// Global modal triggers for HTML onclick compatibility
window.openAssignModal = function(trackingId, parcelId) {
  const trackingIdInput = document.getElementById("modalTrackingId");
  if (trackingIdInput) trackingIdInput.value = trackingId;
  if (parcelId) activeParcelMap.set(trackingId, parcelId);
  const modal = document.getElementById("assignModal");
  if (modal) modal.classList.add("active");
};

window.closeAssignModal = function() {
  const modal = document.getElementById("assignModal");
  if (modal) modal.classList.remove("active");
};

// Helper badge builders
function getStatusBadgeHtml(status) {
  const s = (status || "").toLowerCase();
  let badgeClass = "badge-booked";
  if (s.includes("delivered")) badgeClass = "badge-delivered";
  else if (s.includes("out for delivery")) badgeClass = "badge-outfordelivery";
  else if (s.includes("transit")) badgeClass = "badge-intransit";
  else if (s.includes("picked")) badgeClass = "badge-pickedup";
  else if (s.includes("failed")) badgeClass = "badge-failed";

  return `<span class="badge ${badgeClass}"><span class="badge-dot"></span>${escapeHtml(status || 'Booked')}</span>`;
}

function getPaymentBadgeHtml(paymentStatus) {
  const p = (paymentStatus || "").toLowerCase();
  if (p === "paid" || p === "completed") {
    return `<span class="badge badge-delivered">PAID</span>`;
  }
  return `<span class="badge badge-failed">PENDING</span>`;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
