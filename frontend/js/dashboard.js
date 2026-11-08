/**
 * frontend/js/dashboard.js
 * =============================================================================
 * PCTS — Admin Operations & Parcel Management Dashboard
 * =============================================================================
 */

let allParcels = [];
let allDeliveries = [];
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

  // 2. Set up event listeners
  setupFilterTabs();
  setupSearch();
  setupAssignModal();
  setupPaymentModal();

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

    // Fix: API returns `by_status`, not `breakdown`
    if (parcelReport.by_status) {
      let activeCount = 0;
      let deliveredCount = 0;

      parcelReport.by_status.forEach(b => {
        const s = (b.status || "").toLowerCase();
        if (s.includes("transit") || s.includes("out for delivery") || s.includes("picked") || s.includes("at warehouse")) {
          activeCount += b.count;
        } else if (s.includes("delivered")) {
          deliveredCount += b.count;
        }
      });

      if (activeDelivEl) activeDelivEl.textContent = activeCount.toLocaleString();
      if (deliveredEl) deliveredEl.textContent = deliveredCount.toLocaleString();
    }

    const grossRev = paymentReport.collected_amount ?? paymentReport.total_amount ?? paymentReport.total_revenue ?? 0;
    if (totalRevenueEl) {
      totalRevenueEl.textContent = formatCurrency(grossRev);
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
    const [parcels, deliveries] = await Promise.all([
      apiRequest("/api/parcels?limit=100"),
      apiRequest("/api/deliveries?limit=100")
    ]);
    allParcels = parcels || [];
    allDeliveries = deliveries || [];
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
        <td colspan="10" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
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
    const status = (p.status || "").toLowerCase();
    const isCompleted = status === "delivered" || status === "returned";
    const assignment = allDeliveries.find(d => d.parcel_id === p.parcel_id);
    const isAssigned = p.is_assigned || !!assignment;
    const agentName = p.delivery_person_name || (assignment ? assignment.delivery_person_name : null);
    const deliveryId = p.delivery_id || (assignment ? assignment.delivery_id : null);
    const agentId = p.delivery_person_id || (assignment ? assignment.delivery_person_id : null);

    return `
      <tr>
        <td>
          <a href="track.html?id=${encodeURIComponent(p.tracking_id)}" style="font-weight: 700; color: var(--accent-cyan);">
            ${p.tracking_id}
          </a>
        </td>
        <td>${escapeHtml(p.sender_name)}</td>
        <td>${escapeHtml(p.receiver_name)}</td>
        <td>${escapeHtml(p.source_city)} &rarr; ${escapeHtml(p.destination_city)}</td>
        <td>${escapeHtml(weight)}</td>
        <td>${statusBadge}</td>
        <td>
          ${paymentBadge}
          ${p.payment_status !== "Paid" ? `<button class="btn btn-outline btn-sm" style="margin-left: 0.5rem;" onclick="openPaymentModal('${p.tracking_id}', ${p.parcel_id}, '${p.payment_status}', ${p.payment_amount || p.charge})">Settle</button>` : ''}
        </td>
        <td>
          ${isAssigned
        ? `<strong style="color: var(--accent-emerald);">✓ ${escapeHtml(agentName || 'Assigned')}</strong>`
        : '<span class="badge badge-booked" style="font-size: 0.75rem;">Unassigned</span>'
      }
        </td>
        <td style="text-align: right;">
          <div style="display: flex; gap: 0.35rem; justify-content: flex-end; align-items: center;">
            <a href="track.html?id=${encodeURIComponent(p.tracking_id)}" class="btn btn-outline btn-sm" title="View tracking audit logs">Logs 📋</a>
            ${isCompleted
        ? `<span class="badge badge-delivered" style="font-size: 0.75rem;">Done</span>`
        : isAssigned
          ? `<button class="btn btn-outline btn-sm" style="color: var(--accent-cyan); border-color: var(--accent-cyan);" onclick="openAssignModal('${p.tracking_id}', ${p.parcel_id}, ${deliveryId || ''}, ${agentId || ''})" title="Reassign agent">Reassign 🔄</button>`
          : `<button class="btn btn-primary btn-sm" onclick="openAssignModal('${p.tracking_id}', ${p.parcel_id})">Assign 🚚</button>`
      }
          </div>
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
 * Modal dialog submission handler for assignment
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
      let deliveryId = window._currentReassignDeliveryId;
      if (!deliveryId && Array.isArray(allDeliveries)) {
        const found = allDeliveries.find(d => d.parcel_id === parcelId);
        if (found) {
          deliveryId = found.delivery_id;
        }
      }

      if (deliveryId) {
        await apiRequest(`/api/deliveries/${deliveryId}/reassign`, {
          method: "PUT",
          body: JSON.stringify({
            parcel_id: parcelId,
            delivery_person_id: agentId,
            notes: notes
          })
        });
        alert(`Parcel ${trackingId} successfully reassigned!`);
      } else {
        await apiRequest("/api/deliveries", {
          method: "POST",
          body: JSON.stringify({
            parcel_id: parcelId,
            delivery_person_id: agentId,
            notes: notes
          })
        });
        alert(`Parcel ${trackingId} successfully assigned to delivery executive!`);
      }

      closeAssignModal();
      await loadDashboardData();
      await loadKPIStats();

    } catch (err) {
      alert(`Assignment failed: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Confirm Assignment";
    }
  });
}

/**
 * Setup payment modal form submission
 */
function setupPaymentModal() {
  const form = document.getElementById("paymentUpdateForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const trackingIdInput = document.getElementById("paymentTrackingId");
    const parcelIdInput = document.getElementById("paymentParcelId");
    const amountInput = document.getElementById("paymentAmount");
    const statusSelect = document.getElementById("paymentStatus");
    const methodSelect = document.getElementById("paymentMethod");
    const notesInput = document.getElementById("paymentNotes");
    const submitBtn = document.getElementById("btnConfirmPayment");

    const trackingId = trackingIdInput?.value;
    const parcelId = parseInt(parcelIdInput?.value, 10);
    const amount = parseFloat(amountInput?.value);
    const status = statusSelect?.value;
    const method = methodSelect?.value;
    const notes = notesInput?.value.trim() || "Updated via Admin Dashboard";

    if (!parcelId || !amount || !status || !method) {
      alert("Please fill all required payment fields.");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Updating...";

    try {
      // Check if payment exists first
      let existingPayment = null;
      try {
        existingPayment = await apiRequest(`/api/payments/${parcelId}`);
      } catch (err) {
        // Payment doesn't exist yet
      }

      if (existingPayment) {
        // Update existing payment
        await apiRequest(`/api/payments/id/${existingPayment.payment_id}`, {
          method: "PUT",
          body: JSON.stringify({
            payment_status: status,
            payment_method: method,
            amount: amount,
            notes: notes
          })
        });
      } else {
        // Create new payment record
        await apiRequest("/api/payments", {
          method: "POST",
          body: JSON.stringify({
            parcel_id: parcelId,
            payment_status: status,
            payment_method: method,
            amount: amount,
            notes: notes
          })
        });
      }

      alert(`Payment for ${trackingId} updated successfully!`);
      closePaymentModal();
      loadDashboardData();
      loadKPIStats();

    } catch (err) {
      alert(`Payment update failed: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Update Payment";
    }
  });
}

// Global modal triggers for HTML onclick compatibility
window.openAssignModal = function (trackingId, parcelId, deliveryId, currentAgentId) {
  if (!allAgents || allAgents.length === 0) {
    loadAgents();
  }
  window._currentReassignDeliveryId = deliveryId || null;
  const trackingIdInput = document.getElementById("modalTrackingId");
  const modalTitle = document.getElementById("assignModalTitle");
  const agentSelect = document.getElementById("modalAgentSelect");
  const submitBtn = document.getElementById("btnConfirmAssign");

  if (trackingIdInput) trackingIdInput.value = trackingId;
  if (parcelId) activeParcelMap.set(trackingId, parcelId);
  if (agentSelect && currentAgentId) agentSelect.value = currentAgentId;
  if (modalTitle) {
    modalTitle.textContent = deliveryId ? "Reassign Delivery Executive" : "Assign Delivery Agent";
  }
  if (submitBtn) {
    submitBtn.textContent = deliveryId ? "Confirm Reassignment" : "Confirm Assignment";
  }

  const modal = document.getElementById("assignModal");
  if (modal) modal.classList.add("active");
};

window.closeAssignModal = function () {
  window._currentReassignDeliveryId = null;
  const modal = document.getElementById("assignModal");
  if (modal) modal.classList.remove("active");
};

window.openPaymentModal = function (trackingId, parcelId, currentStatus, currentAmount) {
  const trackingIdInput = document.getElementById("paymentTrackingId");
  const parcelIdInput = document.getElementById("paymentParcelId");
  const amountInput = document.getElementById("paymentAmount");
  const statusSelect = document.getElementById("paymentStatus");

  if (trackingIdInput) trackingIdInput.value = trackingId;
  if (parcelIdInput) parcelIdInput.value = parcelId;
  if (amountInput) amountInput.value = currentAmount || 0;
  if (statusSelect) statusSelect.value = currentStatus || "Pending";

  const modal = document.getElementById("paymentModal");
  if (modal) modal.classList.add("active");
};

window.closePaymentModal = function () {
  const modal = document.getElementById("paymentModal");
  if (modal) modal.classList.remove("active");
};

// Helper badge builders
function getStatusBadgeHtml(status) {
  const s = (status || "").toLowerCase();
  let badgeClass = "badge-booked";
  if (s === "delivered") badgeClass = "badge-delivered";
  else if (s === "out for delivery") badgeClass = "badge-outfordelivery";
  else if (s === "in transit") badgeClass = "badge-intransit";
  else if (s === "picked up") badgeClass = "badge-pickedup";
  else if (s === "failed delivery") badgeClass = "badge-failed";
  else if (s === "at warehouse") badgeClass = "badge-intransit";
  else if (s === "returned") badgeClass = "badge-failed";

  return `<span class="badge ${badgeClass}"><span class="badge-dot"></span>${escapeHtml(status || 'Booked')}</span>`;
}

function getPaymentBadgeHtml(paymentStatus) {
  const p = (paymentStatus || "").toLowerCase();
  if (p === "paid") {
    return `<span class="badge badge-delivered">PAID</span>`;
  } else if (p === "failed") {
    return `<span class="badge badge-failed">FAILED</span>`;
  }
  return `<span class="badge badge-booked">PENDING</span>`;
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
