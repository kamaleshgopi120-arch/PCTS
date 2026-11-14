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
  setupExportReport();

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

/**
 * Setup Official PDF & CSV Export for Admin Operations & Shipments
 */
function setupExportReport() {
  const exportBtn = document.getElementById("btnExportReport");
  if (!exportBtn) return;

  exportBtn.addEventListener("click", async () => {
    const origHtml = exportBtn.innerHTML;
    try {
      exportBtn.disabled = true;
      exportBtn.innerHTML = "⏳ Preparing PDF Report...";

      // 1. Fetch latest parcels if none cached
      let parcelsToExport = allParcels;
      if (!parcelsToExport || parcelsToExport.length === 0) {
        parcelsToExport = await apiRequest("/api/parcels?limit=500");
      }

      if (!parcelsToExport || parcelsToExport.length === 0) {
        alert("No shipment records available to generate PDF report.");
        exportBtn.disabled = false;
        exportBtn.innerHTML = origHtml;
        return;
      }

      // 2. Compute Summary Metrics for the PDF Header
      const totalShipments = parcelsToExport.length;
      let totalRevenue = 0;
      let activeTransit = 0;
      let deliveredCount = 0;

      parcelsToExport.forEach(p => {
        totalRevenue += parseFloat(p.charge || 0);
        const s = (p.status || "").toLowerCase();
        if (s === "delivered") deliveredCount++;
        else if (s.includes("transit") || s.includes("out for delivery") || s.includes("picked") || s.includes("warehouse")) {
          activeTransit++;
        }
      });

      const todayStr = new Date().toLocaleDateString('en-IN', {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });
      const fileDate = new Date().toISOString().split("T")[0];

      // 3. Build Table Rows HTML
      const tableRowsHtml = parcelsToExport.map((p, idx) => {
        const booked = p.booked_at ? new Date(p.booked_at).toLocaleDateString('en-IN') : 'N/A';
        const status = p.status || 'Booked';
        let badgeColor = "#2563eb";
        let badgeBg = "#dbeafe";
        if (status === "Delivered") { badgeColor = "#059669"; badgeBg = "#d1fae5"; }
        else if (status.includes("Transit") || status.includes("Out")) { badgeColor = "#d97706"; badgeBg = "#fef3c7"; }
        else if (status.includes("Failed") || status.includes("Returned")) { badgeColor = "#dc2626"; badgeBg = "#fee2e2"; }

        const payStatus = p.payment_status || 'Pending';
        const payColor = payStatus === "Paid" ? "#059669" : "#d97706";

        return `
          <tr>
            <td style="text-align: center; font-weight: bold; color: #64748b;">${idx + 1}</td>
            <td style="font-family: monospace; font-weight: 700; color: #1e3a8a;">${escapeHtml(p.tracking_id)}</td>
            <td>${booked}</td>
            <td>
              <strong>${escapeHtml(p.sender_name)}</strong><br>
              <span style="font-size: 0.78rem; color: #64748b;">${escapeHtml(p.sender_phone)}</span>
            </td>
            <td>
              <strong>${escapeHtml(p.receiver_name)}</strong><br>
              <span style="font-size: 0.78rem; color: #64748b;">${escapeHtml(p.destination_city)} (${escapeHtml(p.receiver_phone)})</span>
            </td>
            <td style="text-align: center;">${p.weight_kg} kg<br><span style="font-size: 0.75rem; color: #64748b;">${escapeHtml(p.parcel_type)}</span></td>
            <td style="text-align: right; font-weight: 700; color: #0f172a;">₹${parseFloat(p.charge).toFixed(2)}</td>
            <td style="text-align: center;">
              <span style="background: ${badgeBg}; color: ${badgeColor}; padding: 3px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; display: inline-block;">
                ${escapeHtml(status)}
              </span>
            </td>
            <td>
              ${escapeHtml(p.delivery_person_name || 'Unassigned')}<br>
              <span style="font-size: 0.75rem; color: #64748b;">${escapeHtml(p.location || 'Processing Hub')}</span>
            </td>
            <td style="text-align: center; font-weight: 700; font-size: 0.8rem; color: ${payColor};">
              ${escapeHtml(payStatus)}<br>
              <span style="font-size: 0.72rem; color: #64748b; font-weight: normal;">${escapeHtml(p.payment_method || 'COD')}</span>
            </td>
          </tr>
        `;
      }).join("");

      // 4. Construct Complete Printable HTML Document
      const pdfHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PCTS_Operations_Report_${fileDate}</title>
  <style>
    @page {
      size: A4 landscape;
      margin: 10mm;
    }
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      color: #0f172a;
      background: #f8fafc;
      margin: 0;
      padding: 20px;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    @media print {
      body { background: #ffffff; padding: 0; }
      .no-print { display: none !important; }
      table { page-break-inside: auto; }
      tr { page-break-inside: avoid; page-break-after: auto; }
      thead { display: table-header-group; }
    }
    .toolbar {
      position: sticky;
      top: 0;
      z-index: 100;
      background: #1e293b;
      color: #ffffff;
      padding: 12px 24px;
      border-radius: 8px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .btn {
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
      border: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn-primary { background: #2563eb; color: #fff; }
    .btn-primary:hover { background: #1d4ed8; }
    .btn-secondary { background: #475569; color: #fff; }
    .report-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .header-table { width: 100%; border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 20px; }
    .stat-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-box {
      background: #f1f5f9;
      border-left: 4px solid #2563eb;
      padding: 12px 16px;
      border-radius: 4px;
    }
    .stat-box h4 { margin: 0; font-size: 0.78rem; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em; }
    .stat-box .val { font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-top: 4px; }
    table.data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
    }
    table.data-table th {
      background: #0f172a;
      color: #ffffff;
      padding: 8px 10px;
      text-align: left;
      font-weight: 600;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    table.data-table td {
      padding: 8px 10px;
      border-bottom: 1px solid #e2e8f0;
      vertical-align: middle;
    }
    table.data-table tr:nth-child(even) td { background: #f8fafc; }
    .footer-sign {
      margin-top: 32px;
      display: flex;
      justify-content: space-between;
      border-top: 1px solid #cbd5e1;
      padding-top: 16px;
      font-size: 0.8rem;
      color: #64748b;
    }
  </style>
</head>
<body>

  <!-- Floating Print Control Toolbar (Screen only) -->
  <div class="toolbar no-print">
    <div style="display: flex; align-items: center; gap: 10px;">
      <span style="font-size: 1.2rem;">📄</span>
      <strong>PCTS Official Executive Report Viewer</strong>
      <span style="font-size: 0.8rem; opacity: 0.8;">(Select "Destination: Save as PDF" in print dialog)</span>
    </div>
    <div style="display: flex; gap: 10px;">
      <button class="btn btn-primary" onclick="window.print()">
        🖨️ Save as PDF / Print
      </button>
      <button class="btn btn-secondary" onclick="window.close()">
        ✖️ Close
      </button>
    </div>
  </div>

  <div class="report-card">
    <table class="header-table">
      <tr>
        <td style="vertical-align: top;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 2.2rem;">📦</div>
            <div>
              <h1 style="margin: 0; font-size: 1.5rem; color: #0f172a; letter-spacing: -0.02em;">
                PARCEL AND COURIER TRACKING SYSTEM (PCTS)
              </h1>
              <p style="margin: 3px 0 0; color: #475569; font-size: 0.85rem;">
                National Logistics Hub & Operations Command Center • Executive Audit Report
              </p>
            </div>
          </div>
        </td>
        <td style="text-align: right; vertical-align: top; font-size: 0.82rem; color: #475569;">
          <strong>Report Date:</strong> ${todayStr}<br>
          <strong>Generated By:</strong> National Operations HQ (Admin)<br>
          <strong>Database:</strong> TiDB Cloud Serverless (MySQL 8.0)
        </td>
      </tr>
    </table>

    <!-- Key Metrics Grid -->
    <div class="stat-row">
      <div class="stat-box" style="border-left-color: #2563eb;">
        <h4>Total Shipments</h4>
        <div class="val">${totalShipments} Packages</div>
      </div>
      <div class="stat-box" style="border-left-color: #d97706;">
        <h4>Active In-Transit</h4>
        <div class="val" style="color: #d97706;">${activeTransit} Dispatches</div>
      </div>
      <div class="stat-box" style="border-left-color: #059669;">
        <h4>Successfully Delivered</h4>
        <div class="val" style="color: #059669;">${deliveredCount} Completed</div>
      </div>
      <div class="stat-box" style="border-left-color: #7c3aed;">
        <h4>Total Revenue Booked</h4>
        <div class="val" style="color: #7c3aed;">₹${totalRevenue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
      </div>
    </div>

    <!-- Data Table -->
    <table class="data-table">
      <thead>
        <tr>
          <th style="width: 30px; text-align: center;">#</th>
          <th>Tracking ID</th>
          <th>Booked Date</th>
          <th>Sender Info</th>
          <th>Recipient & Destination</th>
          <th style="text-align: center;">Weight</th>
          <th style="text-align: right;">Charge</th>
          <th style="text-align: center;">Milestone Status</th>
          <th>Assigned Courier Agent</th>
          <th style="text-align: center;">Settlement</th>
        </tr>
      </thead>
      <tbody>
        ${tableRowsHtml}
      </tbody>
    </table>

    <!-- Sign-off Block -->
    <div class="footer-sign">
      <div>
        <strong>System Verification:</strong> PCTS Relational Database Engine (BCNF Compliant)<br>
        <strong>Academic Record:</strong> CSPL502 — Database Systems Lab, Pondicherry University
      </div>
      <div style="text-align: right;">
        <strong>Authorized Signatory:</strong><br>
        <span style="font-family: serif; font-size: 1.1rem; color: #1e3a8a;">G. Kamalesh</span><br>
        <span style="font-size: 0.75rem;">(Reg. No: 24BTCSEPY0026)</span>
      </div>
    </div>
  </div>

  <script>
    // Auto-trigger native Print / Save as PDF dialog after render
    window.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        window.print();
      }, 600);
    });
  <\/script>
</body>
</html>`;

      // 5. Open in dedicated popup/tab and write content
      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        alert("Popup blocked! Please allow popups for this site to generate and save your PDF report.");
        exportBtn.disabled = false;
        exportBtn.innerHTML = origHtml;
        return;
      }

      printWindow.document.open();
      printWindow.document.write(pdfHtml);
      printWindow.document.close();

      exportBtn.disabled = false;
      exportBtn.innerHTML = "✅ PDF Generated!";
      setTimeout(() => {
        exportBtn.innerHTML = origHtml;
      }, 2500);

    } catch (err) {
      console.error("Export PDF failed:", err);
      alert("Failed to export PDF report: " + (err.message || "Unknown error"));
      exportBtn.disabled = false;
      exportBtn.innerHTML = origHtml;
    }
  });
}
