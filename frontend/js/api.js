/**
 * frontend/js/api.js
 * =============================================================================
 * PCTS — Shared API Client & Session Management Utilities
 * =============================================================================
 */

const API_BASE = ""; // Relative to server root (works on localhost:8000 and any port)

// Session Storage Keys
const TOKEN_KEY = "pcts_access_token";
const USER_KEY = "pcts_user_profile";

/**
 * Retrieve saved JWT token from localStorage.
 */
function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Save JWT token and user profile into localStorage.
 */
function saveSession(token, userProfile) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  if (userProfile) localStorage.setItem(USER_KEY, JSON.stringify(userProfile));
}

/**
 * Retrieve cached user profile from localStorage.
 */
function getCurrentUser() {
  const data = localStorage.getItem(USER_KEY);
  try {
    return data ? JSON.parse(data) : null;
  } catch (e) {
    return null;
  }
}

/**
 * Clear session and log out.
 */
function logout(redirectUrl = "login.html") {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  if (redirectUrl) {
    window.location.href = redirectUrl;
  }
}

/**
 * Standard fetch wrapper with automatic headers, JWT Bearer attachment,
 * and unified error extraction.
 */
async function apiRequest(endpoint, options = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
  const headers = options.headers ? { ...options.headers } : {};

  if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const token = getToken();
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, { ...options, headers });

    // Try parsing JSON body
    let data;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      // Extract human-friendly error detail
      let errorMessage = `HTTP ${response.status}`;
      if (data && typeof data === "object") {
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            // Pydantic validation list
            errorMessage = data.detail.map(e => `${e.loc?.slice(-1)[0] || 'field'}: ${e.msg}`).join("; ");
          } else {
            errorMessage = data.detail;
          }
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.error) {
          errorMessage = data.error;
        }
      } else if (typeof data === "string" && data.length < 200) {
        errorMessage = data;
      }

      // If Unauthorized on protected page, offer clean redirect
      if (response.status === 401 && !url.includes("/api/auth/login")) {
        console.warn("Session expired or invalid token.");
      }

      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    // Network / offline error
    if (!err.status) {
      err.message = "Unable to connect to PCTS backend server. Please verify your connection.";
    }
    throw err;
  }
}

/**
 * Client-side shipping charge calculator matching backend tiered rules.
 */
function calculateShippingCharge(weightKg) {
  const w = parseFloat(weightKg);
  if (isNaN(w) || w <= 0) return 0.0;
  if (w <= 1.0) return 50.0;
  if (w <= 5.0) return Number((30.0 * w).toFixed(2));
  if (w <= 20.0) return Number((20.0 * w).toFixed(2));
  return Number((15.0 * w).toFixed(2));
}

/**
 * Format currency in Indian Rupees.
 */
function formatCurrency(amount) {
  const num = parseFloat(amount) || 0;
  return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Format ISO datetime string into readable human date.
 */
function formatDateTime(isoString) {
  if (!isoString) return "N/A";
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return isoString;
  return d.toLocaleString("en-IN", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  });
}

/**
 * Display an alert banner on the page.
 */
function showAlert(elementId, message, type = "danger") {
  const alertEl = document.getElementById(elementId);
  if (!alertEl) return;
  alertEl.className = `alert alert-${type}`;
  alertEl.style.display = "flex";
  const messageEl = alertEl.querySelector("span");
  if (messageEl) {
    messageEl.textContent = message;
  } else {
    alertEl.textContent = message;
  }
  alertEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/**
 * Hide an alert banner.
 */
function hideAlert(elementId) {
  const alertEl = document.getElementById(elementId);
  if (alertEl) alertEl.style.display = "none";
}

/**
 * Update top navbar with logged-in user profile, role badge, and logout action.
 */
function initNavbarAuth() {
  const user = getCurrentUser();
  const navAuth = document.querySelector(".nav-auth");
  if (!navAuth) return;

  if (user && getToken()) {
    const roleBadges = {
      customer: '<span class="badge badge-booked" style="margin-right: 0.5rem;">Customer</span>',
      admin: '<span class="badge badge-pickedup" style="margin-right: 0.5rem;">Admin</span>',
      delivery: '<span class="badge badge-delivered" style="margin-right: 0.5rem;">Delivery</span>'
    };

    const roleBadge = roleBadges[user.role] || '';
    const displayName = user.full_name || user.email.split('@')[0];

    navAuth.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        ${roleBadge}
        <span style="font-size: 0.88rem; color: var(--text-primary); font-weight: 600;">
          ${displayName}
        </span>
        <button id="globalLogoutBtn" class="btn btn-outline btn-sm">
          Sign Out
        </button>
      </div>
    `;

    const logoutBtn = document.getElementById("globalLogoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => logout());
    }
  }
}

// Auto-initialize navbar on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initNavbarAuth();
});
