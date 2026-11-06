/**
 * frontend/js/track.js
 * =============================================================================
 * PCTS — Live Parcel Tracking & Chronological Event Timeline
 * =============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  initTrackingPage();
});

const STATUS_PROGRESSION = [
  "Booked",
  "Picked Up",
  "In Transit",
  "Out for Delivery",
  "Delivered"
];

function initTrackingPage() {
  const searchForm = document.getElementById("trackSearchForm");
  const searchInput = document.getElementById("trackSearchInput");
  const searchBtn = document.getElementById("trackSearchBtn");
  const resultContainer = document.getElementById("trackingResultContainer");
  const errorAlert = "trackErrorAlert";

  // Check URL query parameters for ?id=TRK...
  const urlParams = new URLSearchParams(window.location.search);
  const initialId = urlParams.get("id");

  if (initialId && searchInput) {
    searchInput.value = initialId.trim();
    performTracking(initialId.trim());
  } else if (resultContainer) {
    // Hide results initially if no search ID provided
    resultContainer.style.display = "none";
  }

  // Handle Search Submission
  if (searchForm) {
    searchForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const trackingId = searchInput.value.trim();
      if (trackingId) {
        // Update URL query string without reloading page
        const newUrl = `${window.location.pathname}?id=${encodeURIComponent(trackingId)}`;
        window.history.replaceState({ path: newUrl }, "", newUrl);
        performTracking(trackingId);
      }
    });
  }

  /**
   * Fetch tracking data and populate DOM components
   */
  async function performTracking(trackingId) {
    hideAlert(errorAlert);
    hideAlert("trackingHistoryWarning");
    if (!resultContainer) return;

    if (searchBtn) {
      searchBtn.disabled = true;
      searchBtn.textContent = "Tracing...";
    }

    try {
      const data = await apiRequest(`/api/track/${encodeURIComponent(trackingId)}`);

      // Render Overview Elements
      const displayTrackingId = document.getElementById("displayTrackingId");
      if (displayTrackingId) displayTrackingId.textContent = data.tracking_id;

      renderStatusBadge(data.status);
      renderMetadataGrid(data);
      renderStepWizard(data.status);
      renderPaymentCard(data);
      renderTimeline(data.history || data.events || [], data);

      resultContainer.style.display = "block";
      if (data.warning) {
        showAlert("trackingHistoryWarning", data.warning, "warning");
      }
      resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });

    } catch (err) {
      resultContainer.style.display = "none";
      showAlert(
        errorAlert,
        err.message || `No parcel record found for Tracking ID "${trackingId}". Please verify your tracking number.`
      );
    } finally {
      if (searchBtn) {
        searchBtn.disabled = false;
        searchBtn.textContent = "🔍 Track";
      }
    }
  }

  /**
   * Update current status badge styling and text
   */
  function renderStatusBadge(status) {
    const badgeEl = document.getElementById("displayStatusBadge");
    const textEl = document.getElementById("statusBadgeText");
    if (!badgeEl || !textEl) return;

    // Fix: use exact lowercase match to avoid "failed delivery" matching "delivered"
    const normalized = (status || "").toLowerCase().trim();
    badgeEl.className = "badge";

    if (normalized === "delivered") {
      badgeEl.classList.add("badge-delivered");
    } else if (normalized === "out for delivery") {
      badgeEl.classList.add("badge-outfordelivery");
    } else if (normalized === "in transit" || normalized === "at warehouse") {
      badgeEl.classList.add("badge-intransit");
    } else if (normalized === "picked up") {
      badgeEl.classList.add("badge-pickedup");
    } else if (normalized === "failed delivery" || normalized === "returned") {
      badgeEl.classList.add("badge-failed");
    } else {
      badgeEl.classList.add("badge-booked");
    }

    textEl.textContent = status || "Booked";
  }

  /**
   * Render Route & Package Metadata
   */
  function renderMetadataGrid(data) {
    const originEl = document.getElementById("displayOrigin");
    const destEl = document.getElementById("displayDestination");
    const locEl = document.getElementById("displayLocation");
    const weightCatEl = document.getElementById("displayWeightCategory");

    if (originEl) originEl.textContent = data.source_city || "N/A";
    if (destEl) destEl.textContent = data.destination_city || "N/A";
    // Fix: API field is `location`, not `current_location`
    if (locEl) locEl.textContent = data.location || `${data.source_city || 'Origin'} Hub`;
    if (weightCatEl) {
      weightCatEl.textContent = `${data.weight_kg || 0} kg • ${data.parcel_type || 'Standard'}`;
    }
  }

  /**
   * Update 5-Step Horizontal Progress Wizard
   */
  function renderStepWizard(currentStatus) {
    const stepIds = [
      "stepBooked",
      "stepPickedUp",
      "stepInTransit",
      "stepOutForDelivery",
      "stepDelivered"
    ];

    // Determine current progression index
    let activeIdx = 0;
    const normCurrent = (currentStatus || "").toLowerCase().trim();

    if (normCurrent === "delivered") {
      activeIdx = 4;
    } else if (normCurrent === "out for delivery") {
      activeIdx = 3;
    } else if (normCurrent === "in transit" || normCurrent === "at warehouse") {
      // At Warehouse is between In Transit and Out for Delivery — show step 3 (In Transit)
      activeIdx = 2;
    } else if (normCurrent === "picked up") {
      activeIdx = 1;
    } else if (normCurrent === "failed delivery" || normCurrent === "returned") {
      // Failed/Returned: keep wizard at last known active step (Out for Delivery)
      activeIdx = 3;
    } else {
      // Booked or unknown
      activeIdx = 0;
    }

    stepIds.forEach((id, index) => {
      const stepEl = document.getElementById(id);
      if (!stepEl) return;
      stepEl.className = "step-item";

      if (index < activeIdx) {
        stepEl.classList.add("completed");
      } else if (index === activeIdx) {
        stepEl.classList.add("current");
      }
    });
  }

  /**
   * Render Checkpoint Timeline Logs from MongoDB NoSQL Event Store
   */
  function renderTimeline(events, parcelData) {
    const timelineEl = document.getElementById("trackingTimeline");
    if (!timelineEl) return;

    if (!events || events.length === 0) {
      // Fallback single milestone if MongoDB history has no entries
      timelineEl.innerHTML = `
        <div class="timeline-item active">
          <div class="timeline-dot"></div>
          <div class="timeline-title">${escapeHtml(parcelData.status || 'Shipment Booked')}</div>
          <div class="timeline-meta">${escapeHtml(parcelData.location || parcelData.source_city || 'Origin Facility')}</div>
          <div class="timeline-notes">Parcel is active in the PCTS tracking system.</div>
        </div>
      `;
      return;
    }

    // Sort events latest first
    const sorted = [...events].reverse();

    timelineEl.innerHTML = sorted.map((ev, index) => {
      const isActive = index === 0 ? " active" : "";
      const eventTitle = escapeHtml(ev.status || "Checkpoint Scan");
      const timestamp = escapeHtml(formatDateTime(ev.timestamp));
      const loc = ev.location ? `${escapeHtml(ev.location)} • ` : "";
      const notes = escapeHtml(ev.notes || "Checkpoint recorded successfully.");

      return `
        <div class="timeline-item${isActive}">
          <div class="timeline-dot"></div>
          <div class="timeline-title">${eventTitle}</div>
          <div class="timeline-meta">${loc}${timestamp}</div>
          <div class="timeline-notes">${notes}</div>
        </div>
      `;
    }).join("");
  }

  /**
   * Render Payment Status Card
   */
  function renderPaymentCard(data) {
    const amountEl = document.getElementById("displayPaymentAmount");
    const methodEl = document.getElementById("displayPaymentMethod");
    const badgeEl = document.getElementById("displayPaymentBadge");
    const badgeTextEl = document.getElementById("paymentBadgeText");
    const payBtn = document.getElementById("btnPayOnlineModal");

    window._currentTrackingData = data;

    const charge = data.charge ?? 50.00;
    const isPaid = (data.payment_status || "").toLowerCase() === "paid";
    const method = data.payment_method || (isPaid ? "Online" : "Cash on Delivery");

    if (amountEl) amountEl.textContent = formatCurrency(charge);
    if (methodEl) methodEl.textContent = `via ${method}`;

    if (badgeEl && badgeTextEl) {
      badgeEl.className = "badge";
      if (isPaid) {
        badgeEl.classList.add("badge-delivered");
        badgeTextEl.textContent = "PAID ✓";
        if (payBtn) payBtn.style.display = "none";
      } else {
        badgeEl.classList.add("badge-failed");
        badgeTextEl.textContent = "PENDING (COD)";
        if (payBtn) payBtn.style.display = "inline-flex";
      }
    }
  }

  // Setup Track Online Payment Modal Form
  const trackPayForm = document.getElementById("trackPayForm");
  if (trackPayForm) {
    trackPayForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const data = window._currentTrackingData;
      if (!data) return;

      const methodSelect = document.getElementById("trackPayMethodSelect");
      const chosenMethod = methodSelect ? methodSelect.value : "UPI";
      const submitBtn = document.getElementById("btnConfirmOnlinePay");

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Processing Payment...";
      }

      try {
        await apiRequest(`/api/payments/pay-online/${encodeURIComponent(data.tracking_id)}`, {
          method: "POST",
          body: JSON.stringify({
            payment_method: chosenMethod
          })
        });

        alert(`Payment of ${formatCurrency(data.charge ?? 50)} settled successfully via ${chosenMethod}!`);
        closeTrackPayModal();
        performTracking(data.tracking_id);
      } catch (err) {
        alert(`Payment Error: ${err.message || 'Could not complete online settlement.'}`);
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Authorize & Pay Now 🔒";
        }
      }
    });
  }
}

// Global modal triggers for tracking page
window.openTrackPayModal = function() {
  const data = window._currentTrackingData;
  const modal = document.getElementById("trackPayModal");
  const displayAmount = document.getElementById("modalPayAmountDisplay");
  if (displayAmount && data) {
    displayAmount.textContent = formatCurrency(data.charge ?? 50);
  }
  if (modal) modal.classList.add("active");
};

window.closeTrackPayModal = function() {
  const modal = document.getElementById("trackPayModal");
  if (modal) modal.classList.remove("active");
};

window.toggleTrackPayOption = function(method) {
  const upiBox = document.getElementById("trackUpiBox");
  const cardBox = document.getElementById("trackCardBox");
  if (upiBox) upiBox.style.display = method === "UPI" ? "block" : "none";
  if (cardBox) cardBox.style.display = method === "Card" ? "block" : "none";
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
