/**
 * frontend/js/book_parcel.js
 * =============================================================================
 * PCTS — Parcel Booking & Live Shipping Calculator
 * =============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  console.info("PCTS booking form script loaded: 20261106-address-fix");
  initBookingPage();
});

// Global payment toggler
window.togglePaymentInputs = function(method) {
  const container = document.getElementById("onlinePaymentDetails");
  const upiBox = document.getElementById("upiInputContainer");
  const cardBox = document.getElementById("cardInputContainer");
  const bankBox = document.getElementById("netBankingContainer");
  const submitBtn = document.getElementById("bookParcelSubmitBtn");
  const totalCostEl = document.getElementById("summaryTotalCost");
  const amount = totalCostEl ? totalCostEl.textContent.trim() : "₹50.00";

  if (!container) return;

  if (method === "COD") {
    container.style.display = "none";
    if (submitBtn) submitBtn.textContent = "Confirm & Book Shipment (Pay COD) 🚀";
  } else {
    container.style.display = "block";
    if (upiBox) upiBox.style.display = method === "UPI" ? "block" : "none";
    if (cardBox) cardBox.style.display = method === "Card" ? "block" : "none";
    if (bankBox) bankBox.style.display = method === "Net Banking" ? "block" : "none";
    if (submitBtn) submitBtn.textContent = `Pay ${amount} & Book Shipment 🔒`;
  }
};

function initBookingPage() {
  const form = document.getElementById("parcelBookingForm");
  if (!form) return;

  const senderNameInput = document.getElementById("senderName");
  const senderPhoneInput = document.getElementById("senderPhone");
  const sourceCitySelect = document.getElementById("sourceCity");

  const receiverNameInput = document.getElementById("receiverName");
  const receiverPhoneInput = document.getElementById("receiverPhone");
  const destCitySelect = document.getElementById("destCity");
  const receiverAddressInput = document.getElementById("receiverAddress");

  const categorySelect = document.getElementById("categorySelect");
  const weightInput = document.getElementById("weightInput");
  const descriptionInput = document.getElementById("parcelDescription");

  // Summary elements
  const summaryBaseRate = document.getElementById("summaryBaseRate");
  const summaryWeightCharge = document.getElementById("summaryWeightCharge");
  const summaryDistance = document.getElementById("summaryDistance");
  const summaryTotalCost = document.getElementById("summaryTotalCost");
  const submitBtn = document.getElementById("bookParcelSubmitBtn");
  const successAlert = document.getElementById("bookingSuccessAlert");
  const successLink = document.getElementById("successTrackingIdLink");

  // 1. Check if user is authenticated and prefill sender details
  const currentUser = getCurrentUser();
  if (currentUser) {
    if (currentUser.full_name && senderNameInput) senderNameInput.value = currentUser.full_name;
    if (currentUser.phone && senderPhoneInput) senderPhoneInput.value = currentUser.phone;
    if (currentUser.city && sourceCitySelect) {
      // Find matching option
      for (let i = 0; i < sourceCitySelect.options.length; i++) {
        if (sourceCitySelect.options[i].value.toLowerCase() === currentUser.city.toLowerCase()) {
          sourceCitySelect.selectedIndex = i;
          break;
        }
      }
    }
  }

  // 2. Real-time rate calculator
  function updateRateEstimate() {
    const weightText = weightInput?.value.trim() || "";
    const weight = parseFloat(weightText) || 0;
    const src = sourceCitySelect?.value;
    const dst = destCitySelect?.value;

    const validWeight = /^\d+(?:\.\d{1,2})?$/.test(weightText) && weight > 0 && weight <= 500;
    const total = validWeight ? calculateShippingCharge(weight) : 0;
    let tier = "Enter a valid weight (up to 500 kg)";
    if (validWeight && weight <= 1.0) {
      tier = "₹50 flat up to 1 kg";
    } else if (validWeight && weight <= 5.0) {
      tier = "₹30 per kg";
    } else if (validWeight && weight <= 20.0) {
      tier = "₹20 per kg";
    } else if (validWeight) {
      tier = "₹15 per kg";
    }

    if (summaryBaseRate) summaryBaseRate.textContent = tier;
    if (summaryWeightCharge) summaryWeightCharge.textContent = formatCurrency(total);
    if (summaryTotalCost) summaryTotalCost.textContent = formatCurrency(total);

    if (summaryDistance) {
      if (src && dst) {
        if (src === dst) {
          summaryDistance.textContent = "Same City (Invalid)";
          summaryDistance.style.color = "var(--accent-rose)";
        } else {
          summaryDistance.textContent = `${src} → ${dst}`;
          summaryDistance.style.color = "var(--text-primary)";
        }
      } else {
        summaryDistance.textContent = "Standard Regional";
        summaryDistance.style.color = "var(--text-secondary)";
      }
    }
  }

  if (weightInput) weightInput.addEventListener("input", updateRateEstimate);
  if (sourceCitySelect) sourceCitySelect.addEventListener("change", updateRateEstimate);
  if (destCitySelect) destCitySelect.addEventListener("change", updateRateEstimate);

  // Trigger initial rate calculation
  updateRateEstimate();

  // 3. Handle Form Submission
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    // Ensure user is logged in
    const token = getToken();
    if (!token) {
      alert("Please sign in or create an account first to book a parcel shipment.");
      window.location.href = "login.html";
      return;
    }

    const senderName = senderNameInput.value.trim();
    const senderPhone = senderPhoneInput.value.trim();
    const sourceCity = sourceCitySelect.value;

    const receiverName = receiverNameInput.value.trim();
    const receiverPhone = receiverPhoneInput.value.trim();
    const destCity = destCitySelect.value;
    const receiverAddress = receiverAddressInput.value.trim();

    const category = categorySelect.value;
    const weight = parseFloat(weightInput.value);
    const description = descriptionInput ? descriptionInput.value.trim() : "";

    // Validations
    if (!senderName || !senderPhone || !sourceCity || !receiverName || !receiverPhone || !destCity || !receiverAddress) {
      alert("Please fill in all sender, recipient, and address details.");
      return;
    }

    const cleanSender = senderPhone.replace(/^\+91/, '').replace(/\D/g, '');
    const cleanReceiver = receiverPhone.replace(/^\+91/, '').replace(/\D/g, '');

    if (!/^[0-9]{10}$/.test(cleanSender)) {
      alert("Sender mobile number must be exactly 10 digits.");
      return;
    }

    if (!/^[0-9]{10}$/.test(cleanReceiver)) {
      alert("Recipient mobile number must be exactly 10 digits.");
      return;
    }

    if (sourceCity.trim().toLowerCase() === destCity.trim().toLowerCase()) {
      alert("Source city and destination city cannot be identical. Inter-city dispatch required.");
      return;
    }

    if (isNaN(weight) || weight <= 0 || weight > 500 || !/^\d+(?:\.\d{1,2})?$/.test(weightInput.value.trim())) {
      alert("Weight must be greater than 0 and no more than 500 kg, with at most two decimal places.");
      return;
    }

    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Booking Shipment...";

    try {
      // Resolve selected payment option
      const selectedPayRadio = document.querySelector('input[name="paymentOption"]:checked');
      const payOption = selectedPayRadio ? selectedPayRadio.value : "Cash on Delivery";
      const isOnline = payOption !== "Cash on Delivery";

      const payload = {
        sender_name: senderName,
        sender_phone: cleanSender,
        receiver_name: receiverName,
        receiver_phone: cleanReceiver,
        receiver_address: receiverAddress,
        source_city: sourceCity,
        destination_city: destCity,
        parcel_type: category,
        weight_kg: weight,
        description: description || null,
        payment_method: payOption,
        payment_status: isOnline ? "Paid" : "Pending"
      };

      const result = await apiRequest("/api/parcels", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      // Display success message and generated tracking ID
      if (successAlert && successLink) {
        successLink.textContent = result.tracking_id;
        successLink.href = `track.html?id=${encodeURIComponent(result.tracking_id)}`;
        const statusNote = isOnline ? "Payment: PAID online (Instant Settlement)" : "Payment: Cash on Delivery (COD)";
        const msgEl = successAlert.querySelector("strong");
        if (msgEl) msgEl.textContent = `Shipment Booked! [${statusNote}]`;
        successAlert.style.display = "flex";
        successAlert.scrollIntoView({ behavior: "smooth", block: "center" });
      }

      // Reset receiver & package inputs for next booking
      receiverNameInput.value = "";
      receiverPhoneInput.value = "";
      destCitySelect.selectedIndex = 0;
      receiverAddressInput.value = "";
      if (descriptionInput) descriptionInput.value = "";
      weightInput.value = "1.0";
      updateRateEstimate();

    } catch (err) {
      alert(`Booking Error: ${err.message || 'Could not schedule dispatch.'}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
}
