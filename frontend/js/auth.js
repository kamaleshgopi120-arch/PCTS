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

/**
 * Initialize unified Login screen interactions & submissions
 */
function initLoginPage() {
  const emailInput = document.getElementById("loginEmail");
  const passwordInput = document.getElementById("loginPassword");
  const submitBtn = document.getElementById("loginSubmitBtn");
  const loginAlert = "loginAlert";

  // Role preset selector buttons
  const roleCustomerBtn = document.getElementById("roleCustomerBtn");
  const roleAdminBtn = document.getElementById("roleAdminBtn");
  const roleDeliveryBtn = document.getElementById("roleDeliveryBtn");
  const roleTabs = [roleCustomerBtn, roleAdminBtn, roleDeliveryBtn].filter(Boolean);

  function setActiveTab(activeBtn) {
    roleTabs.forEach(btn => btn.classList.remove("active"));
    if (activeBtn) activeBtn.classList.add("active");
  }

  // Preset credentials for easy testing & grading
  if (roleCustomerBtn) {
    roleCustomerBtn.addEventListener("click", () => {
      setActiveTab(roleCustomerBtn);
      emailInput.value = "arun.kumar@gmail.com";
      passwordInput.value = "Customer@12345";
      hideAlert(loginAlert);
    });
  }

  if (roleAdminBtn) {
    roleAdminBtn.addEventListener("click", () => {
      setActiveTab(roleAdminBtn);
      emailInput.value = "admin@pcts.com";
      passwordInput.value = "Admin@12345";
      hideAlert(loginAlert);
    });
  }

  if (roleDeliveryBtn) {
    roleDeliveryBtn.addEventListener("click", () => {
      setActiveTab(roleDeliveryBtn);
      emailInput.value = "ravi.delivery@pcts.com";
      passwordInput.value = "Delivery@12345";
      hideAlert(loginAlert);
    });
  }

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
          window.location.href = "book_parcel.html";
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

    if (password.length < 6) {
      showAlert(regAlert, "Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      showAlert(regAlert, "Passwords do not match. Please re-enter your password.");
      return;
    }

    if (!/^\d{10}$/.test(phone)) {
      showAlert(regAlert, "Phone number must be exactly 10 digits.");
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
