/**
 * frontend/js/book_parcel.js
 * =============================================================================
 * PCTS — Parcel Booking & Live Shipping Calculator
 * =============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  initBookingPage();
});

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
    const weight = parseFloat(weightInput?.value) || 0;
    const src = sourceCitySelect?.value;
    const dst = destCitySelect?.value;

    const total = calculateShippingCharge(weight);
    let base = 50.0;
    let weightSurcharge = 0.0;

    if (weight <= 1.0) {
      base = total;
      weightSurcharge = 0.0;
    } else {
      base = 50.0;
      weightSurcharge = Math.max(0, total - 50.0);
    }

    if (summaryBaseRate) summaryBaseRate.textContent = formatCurrency(base);
    if (summaryWeightCharge) summaryWeightCharge.textContent = formatCurrency(weightSurcharge);
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

    if (sourceCity === destCity) {
      alert("Source city and destination city cannot be identical. Inter-city dispatch required.");
      return;
    }

    if (isNaN(weight) || weight <= 0) {
      alert("Weight must be greater than 0 kg.");
      return;
    }

    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Booking Shipment...";

    try {
      const payload = {
        sender_name: senderName,
        sender_phone: senderPhone,
        receiver_name: receiverName,
        receiver_phone: receiverPhone,
        source_city: sourceCity,
        destination_city: destCity,
        parcel_type: category,
        weight_kg: weight,
        description: description ? `${description} | Delivery to: ${receiverAddress}` : `Delivery to: ${receiverAddress}`
      };

      const result = await apiRequest("/api/parcels", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      // Display success message and generated tracking ID
      if (successAlert && successLink) {
        successLink.textContent = result.tracking_id;
        successLink.href = `track.html?id=${encodeURIComponent(result.tracking_id)}`;
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
