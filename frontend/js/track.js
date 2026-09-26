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
      renderTimeline(data.history || data.events || [], data);

      resultContainer.style.display = "block";
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

    const normalized = (status || "").toLowerCase().replace(/[^a-z]/g, "");
    badgeEl.className = "badge";

    if (normalized.includes("delivered")) {
      badgeEl.classList.add("badge-delivered");
    } else if (normalized.includes("outfor") || normalized.includes("delivery")) {
      badgeEl.classList.add("badge-outfordelivery");
    } else if (normalized.includes("transit")) {
      badgeEl.classList.add("badge-intransit");
    } else if (normalized.includes("picked")) {
      badgeEl.classList.add("badge-pickedup");
    } else if (normalized.includes("failed")) {
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
    if (locEl) locEl.textContent = data.current_location || `${data.source_city || 'Origin'} Hub`;
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
    const normCurrent = (currentStatus || "").toLowerCase();

    if (normCurrent.includes("delivered")) {
      activeIdx = 4;
    } else if (normCurrent.includes("out for delivery")) {
      activeIdx = 3;
    } else if (normCurrent.includes("in transit")) {
      activeIdx = 2;
    } else if (normCurrent.includes("picked up")) {
      activeIdx = 1;
    } else {
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
          <div class="timeline-title">${parcelData.status || 'Shipment Booked'}</div>
          <div class="timeline-meta">${parcelData.current_location || parcelData.source_city || 'Origin Facility'}</div>
          <div class="timeline-notes">Parcel is active in the PCTS tracking system.</div>
        </div>
      `;
      return;
    }

    // Sort events latest first
    const sorted = [...events].reverse();

    timelineEl.innerHTML = sorted.map((ev, index) => {
      const isActive = index === 0 ? " active" : "";
      const eventTitle = ev.status || "Checkpoint Scan";
      const timestamp = formatDateTime(ev.timestamp);
      const loc = ev.location ? `${ev.location} • ` : "";
      const notes = ev.notes || "Checkpoint recorded successfully.";

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
}
