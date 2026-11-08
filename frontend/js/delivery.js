/**
 * frontend/js/delivery.js
 * =============================================================================
 * PCTS — Delivery Executive Task Queue & Milestone Checkpoint Management
 * =============================================================================
 */

let myDeliveries = [];
let showCompleted = false;
let activeDeliveryId = null;
const DELIVERY_STATUS_TRANSITIONS = {
  "Booked": ["Picked Up"],
  "Picked Up": ["In Transit"],
  "In Transit": ["At Warehouse"],
  "At Warehouse": ["Out for Delivery"],
  "Out for Delivery": ["Delivered", "Failed Delivery"],
  "Failed Delivery": ["Returned"],
  "Delivered": [],
  "Returned": []
};

document.addEventListener("DOMContentLoaded", () => {
  initDeliveryPortal();
});

async function initDeliveryPortal() {
  const tasksTableBody = document.getElementById("agentTasksBody");
  if (!tasksTableBody) return;

  // 1. Guard check: Require Delivery role
  const currentUser = getCurrentUser();
  const token = getToken();

  if (!token || !currentUser) {
    window.location.href = "login.html";
    return;
  }

  if (currentUser.role !== "delivery") {
    if (currentUser.role === "admin") window.location.href = "dashboard.html";
    else if (currentUser.role === "customer") window.location.href = "customer_dashboard.html";
    else window.location.href = "login.html";
    return;
  }

  // 2. Render Agent Header Info
  renderAgentProfile(currentUser);

  // 3. Set up tabs and update checkpoint modal
  setupDeliveryTabs();
  setupCheckpointModal();

  // 4. Load tasks
  await loadMyTasks();
}

/**
 * Display logged-in delivery agent's name, phone, vehicle
 */
function renderAgentProfile(user) {
  const headerNameEl = document.getElementById("agentHeaderName");
  const titleNameEl = document.getElementById("agentNameTitle");
  const subtitleEl = document.getElementById("agentSubtitle");

  const name = user.full_name || (user.email ? user.email.split('@')[0] : 'Agent');
  if (headerNameEl) headerNameEl.textContent = name;
  if (titleNameEl) titleNameEl.textContent = name;
  if (subtitleEl) {
    subtitleEl.innerHTML = `Fleet Agent: <strong>${escapeHtml(user.email || 'Active')}</strong> &bull; Status: <strong style="color: var(--accent-emerald);">Active Dispatch ✓</strong>`;
  }
}

/**
 * Fetch assigned delivery tasks from backend
 */
async function loadMyTasks() {
  const tbody = document.getElementById("agentTasksBody");
  if (!tbody) return;

  tbody.innerHTML = `
    <tr>
      <td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-muted);">
        Loading assigned route tasks...
      </td>
    </tr>
  `;

  try {
    const data = await apiRequest("/api/deliveries/my");
    myDeliveries = data || [];

    // Calculate metrics
    let pendingCount = 0;
    let completedCount = 0;

    myDeliveries.forEach(d => {
      const s = (d.status || "").toLowerCase();
      if (s === "delivered" || s === "returned") {
        completedCount++;
      } else {
        pendingCount++;
      }
    });

    const pendingEl = document.getElementById("agentPendingCount");
    const completedEl = document.getElementById("agentCompletedCount");
    const tabActiveEl = document.getElementById("tabActiveTasks");
    const tabCompEl = document.getElementById("tabCompletedTasks");

    if (pendingEl) pendingEl.textContent = pendingCount;
    if (completedEl) completedEl.textContent = completedCount;
    if (tabActiveEl) tabActiveEl.textContent = `Active (${pendingCount})`;
    if (tabCompEl) tabCompEl.textContent = `Completed (${completedCount})`;

    renderTasksTable();

  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 2rem; color: var(--accent-rose);">
          Error loading deliveries: ${err.message}
        </td>
      </tr>
    `;
  }
}

/**
 * Render filtered deliveries into DOM table
 */
function renderTasksTable() {
  const tbody = document.getElementById("agentTasksBody");
  if (!tbody) return;

  const filtered = myDeliveries.filter(d => {
    const isCompleted = ["delivered", "returned"].includes((d.status || "").toLowerCase());
    return showCompleted ? isCompleted : !isCompleted;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
          ${showCompleted ? 'No completed deliveries yet.' : 'No pending delivery tasks assigned right now! Great job! 🎉'}
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map(d => {
    const statusBadge = getStatusBadgeHtml(d.status);
    const weight = `${d.weight_kg ?? 0} kg`;
    const isCompleted = ["delivered", "returned"].includes((d.status || "").toLowerCase());
    const safeReceiver = escapeHtml(d.receiver_name || 'Customer');
    const safePhone = escapeHtml(d.receiver_phone || '');
    const safeAddress = escapeHtml(
      d.receiver_address
        ? `${d.receiver_address}, ${d.destination_city}`
        : d.destination_city || 'Destination Hub'
    );
    const isPaid = (d.payment_status || "").toLowerCase() === "paid";
    const payAmount = d.payment_amount ?? 50;
    const payBadge = isPaid
      ? `<span class="badge badge-delivered" style="font-size: 0.78rem;">PAID ✓</span>`
      : `<div style="display: flex; flex-direction: column; gap: 0.35rem;">
           <span class="badge badge-failed" style="font-size: 0.75rem;">COLLECT ${formatCurrency(payAmount)} COD</span>
           <button class="btn btn-outline btn-sm" style="font-size: 0.75rem; padding: 0.25rem 0.55rem; color: var(--accent-emerald); border-color: var(--accent-emerald);" onclick="collectCashPayment(${d.delivery_id}, '${escapeHtml(d.tracking_id)}', ${payAmount})">
             💵 Collect Cash
           </button>
         </div>`;

    return `
      <tr>
        <td>
          <a href="track.html?id=${encodeURIComponent(d.tracking_id)}" style="font-weight: 700; color: var(--accent-cyan);">
            ${d.tracking_id}
          </a>
        </td>
        <td>
          <div style="font-weight: 600;">${safeReceiver}</div>
          ${
            safePhone
              ? `<a href="tel:${safePhone}" style="font-size: 0.82rem; color: var(--accent-emerald); display: inline-flex; align-items: center; gap: 0.25rem;">
                   📞 ${safePhone}
                 </a>`
              : ''
          }
        </td>
        <td style="max-width: 250px;">${safeAddress}</td>
        <td>${weight}</td>
        <td>${payBadge}</td>
        <td>${statusBadge}</td>
        <td style="text-align: right;">
          ${
            isCompleted
              ? `<span style="color: var(--accent-emerald); font-size: 0.85rem; font-weight: 600;">Completed ✔</span>`
              : `<button class="btn btn-primary btn-sm" data-delivery-id="${d.delivery_id}" data-tracking-id="${escapeHtml(d.tracking_id)}" data-status="${escapeHtml(d.status)}" data-location="${escapeHtml(d.location || '')}">
                   Update Status ✏️
                 </button>`
          }
        </td>
      </tr>
    `;
  }).join("");

  tbody.querySelectorAll("[data-delivery-id]").forEach(button => {
    button.addEventListener("click", () => {
      window.openUpdateModal(
        Number(button.dataset.deliveryId),
        button.dataset.trackingId,
        button.dataset.status,
        button.dataset.location
      );
    });
  });
}

/**
 * Configure tabs for Active vs Delivered views
 */
function setupDeliveryTabs() {
  const tabActive = document.getElementById("tabActiveTasks");
  const tabComp = document.getElementById("tabCompletedTasks");

  if (tabActive) {
    tabActive.addEventListener("click", () => {
      tabActive.classList.add("active");
      if (tabComp) tabComp.classList.remove("active");
      showCompleted = false;
      renderTasksTable();
    });
  }

  if (tabComp) {
    tabComp.addEventListener("click", () => {
      tabComp.classList.add("active");
      if (tabActive) tabActive.classList.remove("active");
      showCompleted = true;
      renderTasksTable();
    });
  }
}

/**
 * Configure checkpoint status update modal
 */
function setupCheckpointModal() {
  const form = document.getElementById("updateCheckpointForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const statusSelect = document.getElementById("newStatusSelect");
    const locationInput = document.getElementById("checkpointLocationInput");
    const notesInput = document.getElementById("checkpointNotesInput");
    const submitBtn = document.getElementById("btnConfirmStatusUpdate");

    const newStatus = statusSelect?.value;
    const locationText = locationInput?.value.trim();
    const notesText = notesInput?.value.trim() || `Milestone reached: ${newStatus}`;

    if (!activeDeliveryId) {
      alert("No active delivery task selected.");
      return;
    }

    if (!locationText) {
      alert("Please provide the current checkpoint location.");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Updating...";

    try {
      await apiRequest(`/api/deliveries/${activeDeliveryId}/status`, {
        method: "PUT",
        body: JSON.stringify({
          status: newStatus,
          location: locationText,
          notes: notesText
        })
      });

      alert(`Status updated to "${newStatus}"! MongoDB audit milestone recorded.`);
      closeUpdateModal();
      await loadMyTasks();

    } catch (err) {
      alert(`Could not update milestone: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Update 💾";
    }
  });
}

// Global modal triggers for HTML onclick compatibility
window.openUpdateModal = function(deliveryId, trackingId, currentStatus, defaultLocation) {
  activeDeliveryId = deliveryId;
  const trackingEl = document.getElementById("updateTrackingId");
  const statusEl = document.getElementById("newStatusSelect");
  const locEl = document.getElementById("checkpointLocationInput");

  if (trackingEl) trackingEl.value = trackingId;

  if (statusEl) {
    const nextStatuses = DELIVERY_STATUS_TRANSITIONS[currentStatus] || [];
    statusEl.replaceChildren(...nextStatuses.map(nextStatus => {
      const option = document.createElement("option");
      option.value = nextStatus;
      option.textContent = nextStatus;
      return option;
    }));
    statusEl.disabled = nextStatuses.length === 0;
    if (nextStatuses.length > 0) {
      statusEl.value = nextStatuses[0];
    }
  }

  if (locEl) locEl.value = defaultLocation || "";

  const modal = document.getElementById("updateStatusModal");
  if (modal) modal.classList.add("active");
};

window.closeUpdateModal = function() {
  const modal = document.getElementById("updateStatusModal");
  if (modal) modal.classList.remove("active");
};

window.collectCashPayment = async function(deliveryId, trackingId, amount) {
  const formattedAmt = parseFloat(amount || 0).toFixed(2);
  if (!confirm(`Confirm collecting Rs. ${formattedAmt} in cash from recipient for parcel ${trackingId}?`)) {
    return;
  }
  try {
    if (deliveryId && Number(deliveryId) > 0) {
      await apiRequest(`/api/deliveries/${deliveryId}/collect-cod`, { method: "POST" });
    } else {
      await apiRequest(`/api/deliveries/collect-cod/${encodeURIComponent(trackingId)}`, { method: "POST" });
    }
    alert(`Cash payment of Rs. ${formattedAmt} recorded successfully! Status updated to PAID ✓`);
    await loadMyTasks();
  } catch (err) {
    // Resilient fallback directly to payment settlement route
    try {
      await apiRequest(`/api/payments/pay-online/${encodeURIComponent(trackingId)}`, {
        method: "POST",
        body: JSON.stringify({ payment_method: "Cash on Delivery" })
      });
      alert(`Cash payment of Rs. ${formattedAmt} recorded successfully! Status updated to PAID ✓`);
      await loadMyTasks();
    } catch (fallbackErr) {
      alert(`Could not record cash collection: ${fallbackErr.message || err.message}`);
    }
  }
};

// Helper badge builder
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

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
