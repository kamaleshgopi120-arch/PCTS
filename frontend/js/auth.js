/**
 * frontend/js/auth.js
 * =============================================================================
 * PCTS — Authentication & Registration Logic
 * =============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  // Check if we are on login.html
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    initLoginPage();
  }

  // Check if we are on register.html
  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    initRegisterPage();
  }
});

const PRESET_ACCOUNTS = {
  admin: [
    { label: "admin@pcts.com — Super Admin (National HQ)", email: "admin@pcts.com", pwd: "Admin@12345" },
    { label: "priya.admin@pcts.com — Regional Operations Admin", email: "priya.admin@pcts.com", pwd: "Admin@12345" },
    { label: "vikram.admin@pcts.com — Hub Logistics Admin", email: "vikram.admin@pcts.com", pwd: "Admin@12345" }
  ],
  delivery: [
    { label: "ravi.delivery@pcts.com — Ravi Varma (Bike • TN-01-AB-1234)", email: "ravi.delivery@pcts.com", pwd: "Delivery@12345" },
    { label: "suresh.delivery@pcts.com — Suresh Patil (Van • MH-12-CD-5678)", email: "suresh.delivery@pcts.com", pwd: "Delivery@12345" },
    { label: "anjali.delivery@pcts.com — Anjali Rao (EV Scooter • KA-05-EF-9012)", email: "anjali.delivery@pcts.com", pwd: "Delivery@12345" },
    { label: "sunil.delivery@pcts.com — Sunil Das (Express Van • DL-01-GH-3456)", email: "sunil.delivery@pcts.com", pwd: "Delivery@12345" }
  ],
  customer: [
    { label: "arun.kumar@gmail.com — Arun Kumar (Chennai)", email: "arun.kumar@gmail.com", pwd: "Customer@12345" },
    { label: "priya.sharma@yahoo.com — Priya Sharma (Bengaluru)", email: "priya.sharma@yahoo.com", pwd: "Customer@12345" },
    { label: "kavita.nair@gmail.com — Kavita Nair (Kochi)", email: "kavita.nair@gmail.com", pwd: "Customer@12345" }
  ]
};

let currentSelectedRole = "customer";

/**
 * Select a predefined demo role and populate login form
 * @param {"customer" | "admin" | "delivery"} role 
 */
function selectRole(role) {
  currentSelectedRole = role;
  const emailInput = document.getElementById("loginEmail");
  const passwordInput = document.getElementById("loginPassword");
  const presetSelect = document.getElementById("accountPresetSelect");
  const roleCustomerBtn = document.getElementById("roleCustomerBtn");
  const roleAdminBtn = document.getElementById("roleAdminBtn");
  const roleDeliveryBtn = document.getElementById("roleDeliveryBtn");

  const tabs = [roleCustomerBtn, roleAdminBtn, roleDeliveryBtn].filter(Boolean);
  tabs.forEach(btn => btn.classList.remove("active"));

  if (typeof hideAlert === "function") {
    hideAlert("loginAlert");
  }

  if (role === "admin" && roleAdminBtn) roleAdminBtn.classList.add("active");
  else if (role === "delivery" && roleDeliveryBtn) roleDeliveryBtn.classList.add("active");
  else if (roleCustomerBtn) roleCustomerBtn.classList.add("active");

  const accounts = PRESET_ACCOUNTS[role] || PRESET_ACCOUNTS.customer;

  if (presetSelect) {
    presetSelect.innerHTML = accounts.map((acc, idx) => 
      `<option value="${idx}">${acc.label}</option>`
    ).join("");
    presetSelect.value = "0";
  }

  if (accounts.length > 0) {
    if (emailInput) emailInput.value = accounts[0].email;
    if (passwordInput) passwordInput.value = accounts[0].pwd;
  }
}
window.selectRole = selectRole;

function applyAccountPreset(index) {
  const emailInput = document.getElementById("loginEmail");
  const passwordInput = document.getElementById("loginPassword");
  const accounts = PRESET_ACCOUNTS[currentSelectedRole] || PRESET_ACCOUNTS.customer;
  const acc = accounts[parseInt(index, 10)] || accounts[0];

  if (acc) {
    if (emailInput) emailInput.value = acc.email;
    if (passwordInput) passwordInput.value = acc.pwd;
  }
}
window.applyAccountPreset = applyAccountPreset;

/**
 * Initialize unified Login screen interactions & submissions
 */
function initLoginPage() {
  const emailInput = document.getElementById("loginEmail");
  const passwordInput = document.getElementById("loginPassword");
  const submitBtn = document.getElementById("loginSubmitBtn");
  const roleCustomerBtn = document.getElementById("roleCustomerBtn");
  const roleAdminBtn = document.getElementById("roleAdminBtn");
  const roleDeliveryBtn = document.getElementById("roleDeliveryBtn");
  const loginAlert = "loginAlert";

  // Preset button click listeners
  if (roleCustomerBtn) roleCustomerBtn.addEventListener("click", () => selectRole("customer"));
  if (roleAdminBtn) roleAdminBtn.addEventListener("click", () => selectRole("admin"));
  if (roleDeliveryBtn) roleDeliveryBtn.addEventListener("click", () => selectRole("delivery"));

  // Ensure Customer credentials are pre-filled on initial page load
  selectRole("customer");

  // Handle Login Submission
  const loginForm = document.getElementById("loginForm");
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert(loginAlert);

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email || !password) {
      showAlert(loginAlert, "Please provide both email address and password.");
      return;
    }

    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Signing In...";

    try {
      // 1. Authenticate and retrieve JWT token
      const tokenData = await apiRequest("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });

      // Temporarily store token so get_me can use it
      saveSession(tokenData.access_token, tokenData);

      // 2. Fetch enriched profile details (full_name, phone, role)
      let fullProfile = tokenData;
      try {
        const meData = await apiRequest("/api/auth/me");
        fullProfile = { ...tokenData, ...meData };
      } catch (profileErr) {
        console.warn("Could not retrieve full profile:", profileErr);
      }

      saveSession(tokenData.access_token, fullProfile);

      showAlert(loginAlert, "Login successful! Redirecting...", "success");

      // 3. Intelligent redirect based on role
      setTimeout(() => {
        if (fullProfile.role === "admin") {
          window.location.href = "dashboard.html";
        } else if (fullProfile.role === "delivery") {
          window.location.href = "delivery_dashboard.html";
        } else {
          window.location.href = "customer_dashboard.html";
        }
      }, 700);

    } catch (err) {
      showAlert(loginAlert, err.message || "Invalid credentials. Please verify your email and password.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
}

/**
 * Initialize customer registration interactions & submission
 */
function initRegisterPage() {
  const registerForm = document.getElementById("registerForm");
  const submitBtn = document.getElementById("registerSubmitBtn");
  const regAlert = "registerAlert";

  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert(regAlert);

    const fullName = document.getElementById("regName")?.value.trim();
    const email = document.getElementById("regEmail")?.value.trim();
    const phone = document.getElementById("regPhone")?.value.trim();
    const city = document.getElementById("regCity")?.value;
    const address = document.getElementById("regAddress")?.value.trim();
    const password = document.getElementById("regPassword")?.value;
    const confirmPassword = document.getElementById("regConfirmPassword")?.value;

    // Client-side validations
    if (!fullName || !email || !phone || !city || !address || !password) {
      showAlert(regAlert, "All fields are required. Please fill in all fields.");
      return;
    }

    if (fullName.length < 2) {
      showAlert(regAlert, "Full name must be at least 2 characters.");
      return;
    }

    if (password.length < 8) {
      showAlert(regAlert, "Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      showAlert(regAlert, "Passwords do not match. Please re-enter your password.");
      return;
    }

    if (!/^\+?[0-9]{10,14}$/.test(phone)) {
      showAlert(regAlert, "Phone number must be 10 to 14 digits (digits only, optional + prefix).");
      return;
    }

    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Creating Account...";

    try {
      // 1. Submit Registration Payload
      const payload = {
        full_name: fullName,
        email: email,
        password: password,
        phone: phone,
        city: city,
        address: address,
        role: "customer"
      };

      await apiRequest("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      showAlert(regAlert, "Account registered! Signing you in...", "success");

      // 2. Auto-login on registration success
      const tokenData = await apiRequest("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });

      const userProfile = {
        ...tokenData,
        full_name: fullName,
        email: email,
        phone: phone,
        city: city
      };

      saveSession(tokenData.access_token, userProfile);

      setTimeout(() => {
        window.location.href = "book_parcel.html";
      }, 1000);

    } catch (err) {
      showAlert(regAlert, err.message || "Registration failed. Please try again.");
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
}
