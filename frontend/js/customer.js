/**
 * frontend/js/customer.js
 * =============================================================================
 * PCTS — Customer Dashboard Logic: Shipments, Live Milestones & Settlements
 * =============================================================================
 */

let myParcels = [];
let activeCustomerFilter = "ALL";
let currentPayParcel = null;

document.addEventListener("DOMContentLoaded", async () => {
  // 1. Session Guard — Customer Role Only
  const user = getCurrentUser();
  const token = getToken();

  if (!token || !user) {
    window.location.href = "login.html";
    return;
  }

  if (user.role !== "customer") {
    // If Admin or Delivery Agent logged in, direct to their dedicated dashboard
    if (user.role === "admin") window.location.href = "dashboard.html";
    else if (user.role === "delivery") window.location.href = "delivery_dashboard.html";
    else window.location.href = "login.html";
    return;
  }

  // 2. Setup Profile & UI Elements
  renderCustomerProfile(user);
  setupTabs();
  setupSearch();
  setupPaymentModal();

  const refreshBtn = document.getElementById("btnRefreshCustomerData");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => loadCustomerParcels());
  }

  // 3. Load Customer Data
  await loadCustomerParcels();
});

/**
 * Display customer details in header and profile section
 */
function renderCustomerProfile(user) {
  const nameEl = document.getElementById("customerNavName");
  const welcomeEl = document.getElementById("welcomeCustomerHeading");
  const pName = document.getElementById("profileFullName");
  const pEmail = document.getElementById("profileEmail");
  const pPhone = document.getElementById("profilePhone");
  const pCity = document.getElementById("profileCity");

  const displayName = user.full_name || user.email.split('@')[0];
  if (nameEl) nameEl.textContent = displayName;
  if (welcomeEl) welcomeEl.textContent = `Welcome, ${displayName}!`;

  if (pName) pName.textContent = user.full_name || displayName;
  if (pEmail) pEmail.textContent = user.email || "—";
  if (pPhone) pPhone.textContent = user.phone || "—";
  if (pCity) pCity.textContent = user.city ? `${user.city} (${user.address || 'Registered'})` : (user.address || "—");
}

/**
 * Fetch parcels booked by the current logged-in customer
 */
async function loadCustomerParcels() {
  const tbody = document.getElementById("customerTableBody");
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">
        Fetching your shipments from database...
      </td>
    </tr>
  `;

  try {
    const data = await apiRequest("/api/parcels?limit=100");
    myParcels = Array.isArray(data) ? data : [];

    updateCustomerKPIs(myParcels);
    renderCustomerParcelsTable();

  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 2rem; color: var(--accent-rose);">
          Error loading shipments: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
  }
}

/**
 * Compute and display KPI metrics
 */
function updateCustomerKPIs(parcels) {
  const totalBookedEl = document.getElementById("valTotalBooked");
  const activeTransitEl = document.getElementById("valActiveTransit");
  const deliveredEl = document.getElementById("valDelivered");
  const totalSpentEl = document.getElementById("valTotalSpent");
  const pendingCodeEl = document.getElementById("valPendingCOD");

  const total = parcels.length;
  let active = 0;
  let delivered = 0;
  let totalAmount = 0;
  let pendingAmount = 0;

  parcels.forEach(p => {
    const s = (p.status || "").toLowerCase();
    const charge = parseFloat(p.charge || p.payment_amount || 0);
    totalAmount += charge;

    if (s === "delivered") {
      delivered++;
    } else if (s !== "returned") {
      active++;
    }

    if (p.payment_status !== "Paid") {
      pendingAmount += charge;
    }
  });

  if (totalBookedEl) totalBookedEl.textContent = total;
  if (activeTransitEl) activeTransitEl.textContent = active;
  if (deliveredEl) deliveredEl.textContent = delivered;
  if (totalSpentEl) totalSpentEl.textContent = `₹${totalAmount.toFixed(2)}`;
  if (pendingCodeEl) {
    pendingCodeEl.textContent = pendingAmount > 0
      ? `₹${pendingAmount.toFixed(2)} pending collection (COD)`
      : "All shipments fully paid ✓";
    pendingCodeEl.style.color = pendingAmount > 0 ? "var(--accent-amber)" : "var(--accent-emerald)";
  }
}

/**
 * Render parcels table with filter and search
 */
function renderCustomerParcelsTable() {
  const tbody = document.getElementById("customerTableBody");
  const searchInput = document.getElementById("customerTableSearch");
  if (!tbody) return;

  const query = (searchInput ? searchInput.value : "").trim().toLowerCase();

  const filtered = myParcels.filter(p => {
    // 1. Status Filter
    if (activeCustomerFilter !== "ALL") {
      const s = (p.status || "").toLowerCase();
      const f = activeCustomerFilter.toLowerCase();
      if (!s.includes(f)) return false;
    }

    // 2. Search Query
    if (query) {
      const matchTrack = (p.tracking_id || "").toLowerCase().includes(query);
      const matchRecv = (p.receiver_name || "").toLowerCase().includes(query);
      const matchCity = (p.destination_city || "").toLowerCase().includes(query);
      if (!matchTrack && !matchRecv && !matchCity) return false;
    }

    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          No shipments match the selected filters.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map(p => {
    const statusBadge = getStatusBadgeHtml(p.status);
    const paymentBadge = getPaymentBadgeHtml(p.payment_status);
    const bookedDate = safeFormatDate(p.booked_at);
    const charge = parseFloat(p.charge || p.payment_amount || 0).toFixed(2);
    const isPaid = (p.payment_status || "").toLowerCase() === "paid";

    return `
      <tr>
        <td>
          <a href="track.html?id=${encodeURIComponent(p.tracking_id)}" style="font-weight: 700; color: var(--primary);">
            ${escapeHtml(p.tracking_id)}
          </a>
        </td>
        <td>
          <strong>${escapeHtml(p.receiver_name)}</strong><br>
          <span style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(p.receiver_phone || '')}</span>
        </td>
        <td>
          ${escapeHtml(p.source_city)} &rarr; <strong>${escapeHtml(p.destination_city)}</strong>
        </td>
        <td>
          ${escapeHtml(p.parcel_type)} &bull; ${escapeHtml(p.weight_kg)} kg
        </td>
        <td style="font-size: 0.85rem; color: var(--text-muted);">
          ${bookedDate}
        </td>
        <td>${statusBadge}</td>
        <td>
          ${paymentBadge}<br>
          <span style="font-size: 0.82rem; font-weight: 600;">₹${charge}</span>
          ${!isPaid ? `<br><button class="btn btn-primary btn-sm" style="margin-top: 0.35rem; font-size: 0.75rem; padding: 0.2rem 0.55rem;" onclick="openCustPayModal('${p.tracking_id}', ${charge})">Pay Online 💳</button>` : ''}
        </td>
        <td style="text-align: right;">
          <a href="track.html?id=${encodeURIComponent(p.tracking_id)}" class="btn btn-outline btn-sm">
            Track 📍
          </a>
        </td>
      </tr>
    `;
  }).join("");
}

/**
 * Filter tabs listener
 */
function setupTabs() {
  const tabs = document.querySelectorAll("#customerStatusFilterTabs .tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      activeCustomerFilter = tab.getAttribute("data-filter") || "ALL";
      renderCustomerParcelsTable();
    });
  });
}

/**
 * Search input listener
 */
function setupSearch() {
  const input = document.getElementById("customerTableSearch");
  if (input) {
    input.addEventListener("input", () => {
      renderCustomerParcelsTable();
    });
  }
}

/**
 * Payment Modal Setup
 */
function setupPaymentModal() {
  const form = document.getElementById("custPayForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const trackingId = document.getElementById("custPayTrackingId")?.value;
    const method = document.getElementById("custPaymentMethod")?.value;
    const submitBtn = document.getElementById("btnConfirmCustPay");

    if (!trackingId || !method) return;

    submitBtn.disabled = true;
    submitBtn.textContent = "Processing Payment...";

    try {
      await apiRequest(`/api/payments/pay-online/${encodeURIComponent(trackingId)}`, {
        method: "POST",
        body: JSON.stringify({ payment_method: method })
      });

      alert(`Payment for parcel ${trackingId} settled successfully!`);
      closeCustPayModal();
      await loadCustomerParcels();

    } catch (err) {
      alert(`Payment failed: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Confirm & Pay Now 🔒";
    }
  });
}

window.openCustPayModal = function (trackingId, amount) {
  const trkInput = document.getElementById("custPayTrackingId");
  const amtInput = document.getElementById("custPayAmount");
  if (trkInput) trkInput.value = trackingId;
  if (amtInput) amtInput.value = `₹${parseFloat(amount).toFixed(2)}`;

  const modal = document.getElementById("custPayModal");
  if (modal) modal.classList.add("active");
};

window.closeCustPayModal = function () {
  const modal = document.getElementById("custPayModal");
  if (modal) modal.classList.remove("active");
};

// Helper Badge Builders
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
    return `<span class="badge badge-delivered">PAID ✓</span>`;
  } else if (p === "failed") {
    return `<span class="badge badge-failed">FAILED</span>`;
  }
  return `<span class="badge badge-booked">PENDING</span>`;
}

function safeFormatDate(iso) {
  if (typeof formatDate === "function") return formatDate(iso);
  if (typeof formatDateTime === "function") return formatDateTime(iso);
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" });
  } catch (e) {
    return String(iso);
  }
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

