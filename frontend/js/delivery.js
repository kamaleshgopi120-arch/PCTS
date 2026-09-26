/**
 * frontend/js/delivery.js
 * =============================================================================
 * PCTS — Delivery Executive Task Queue & Milestone Checkpoint Management
 * =============================================================================
 */

let myDeliveries = [];
let showCompleted = false;
let activeDeliveryId = null;

document.addEventListener("DOMContentLoaded", () => {
  initDeliveryPortal();
});

async function initDeliveryPortal() {
  const tasksTableBody = document.getElementById("agentTasksBody");
  if (!tasksTableBody) return;

  // 1. Guard check: Require Delivery role
  const currentUser = getCurrentUser();
  const token = getToken();

  if (!token || !currentUser || currentUser.role !== "delivery") {
    alert("Delivery agent authentication required. Redirecting to login.");
    window.location.href = "login.html";
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

  const name = user.full_name || user.email.split('@')[0];
  if (headerNameEl) headerNameEl.textContent = name;
  if (titleNameEl) titleNameEl.textContent = name;
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
      if (s.includes("delivered")) {
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
    if (tabCompEl) tabCompEl.textContent = `Delivered (${completedCount})`;

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
    const isDelivered = (d.status || "").toLowerCase().includes("delivered");
    return showCompleted ? isDelivered : !isDelivered;
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
    const weight = `${d.weight_kg || 1.0} kg`;
    const isDelivered = (d.status || "").toLowerCase().includes("delivered");
    const safeReceiver = escapeHtml(d.receiver_name || 'Customer');
    const safePhone = escapeHtml(d.receiver_phone || '');
    const safeAddress = escapeHtml(d.destination_city || 'Destination Hub');

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
        <td>${statusBadge}</td>
        <td style="text-align: right;">
          ${
            isDelivered
              ? `<span style="color: var(--accent-emerald); font-size: 0.85rem; font-weight: 600;">Delivered ✔</span>`
              : `<button class="btn btn-primary btn-sm" onclick="openUpdateModal(${d.delivery_id}, '${d.tracking_id}', '${d.status}', '${d.location || ''}')">
                   Update Status ✏️
                 </button>`
          }
        </td>
      </tr>
    `;
  }).join("");
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
  if (statusEl && currentStatus) statusEl.value = currentStatus;
  if (locEl) locEl.value = defaultLocation || "";

  const modal = document.getElementById("updateStatusModal");
  if (modal) modal.classList.add("active");
};

window.closeUpdateModal = function() {
  const modal = document.getElementById("updateStatusModal");
  if (modal) modal.classList.remove("active");
};

// Helper badge builder
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

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
