# =============================================================
# 02_conditionals_and_loops.py
# Topic: if/elif/else   |   for loop   |   while loop
# =============================================================

# =============================================================
# PART 1 â€” Conditionals (if / elif / else)
# =============================================================
# An "if" statement runs a block of code ONLY IF a condition is True.
# "elif" means "else if" â€” check another condition if the first was False.
# "else" runs when NONE of the above conditions were True.
# =============================================================

print("=== PART 1: Conditionals ===\n")

# --- Example 1: Check parcel status and print a message ---
status = "In Transit"

if status == "Booked":
    print("Your parcel has been registered. Awaiting pickup.")
elif status == "Picked Up":
    print("Your parcel has been collected from the sender.")
elif status == "In Transit":
    print("Your parcel is on its way!")
elif status == "Out for Delivery":
    print("Your parcel is out for delivery today.")
elif status == "Delivered":
    print("Your parcel has been delivered. Thank you!")
else:
    print("Unknown status. Please contact support.")

# --- Example 2: Calculate delivery charge based on weight ---
weight_kg = 3.5

if weight_kg <= 0:
    print("Error: Weight must be greater than 0.")
elif weight_kg <= 1:
    charge = 50.0
    print(f"Flat charge for up to 1 kg: â‚¹{charge}")
elif weight_kg <= 5:
    charge = weight_kg * 30
    print(f"Charge for {weight_kg} kg at â‚¹30/kg: â‚¹{charge}")
elif weight_kg <= 20:
    charge = weight_kg * 20
    print(f"Charge for {weight_kg} kg at â‚¹20/kg: â‚¹{charge}")
else:
    charge = weight_kg * 15
    print(f"Charge for {weight_kg} kg at â‚¹15/kg: â‚¹{charge}")

# --- Example 3: Check payment status ---
payment_status = "Pending"
is_admin = True

# You can combine conditions with "and" / "or" / "not"
if payment_status == "Pending" and is_admin:
    print("\nAdmin alert: This parcel has a pending payment.")

if payment_status != "Paid":
    print("Payment not yet completed.")


# =============================================================
# PART 2 â€” for loop
# =============================================================
# A "for" loop repeats a block of code for each item in a sequence.
# =============================================================

print("\n=== PART 2: for loop ===\n")

# --- Example 1: Print all parcel statuses in order ---
parcel_statuses = [
    "Booked",
    "Picked Up",
    "In Transit",
    "At Warehouse",
    "Out for Delivery",
    "Delivered"
]

print("All possible parcel statuses:")
for status in parcel_statuses:
    print(" -", status)

# --- Example 2: Loop with index using enumerate() ---
print("\nStatus order:")
for index, status in enumerate(parcel_statuses, start=1):
    print(f"  Step {index}: {status}")

# --- Example 3: Loop over a list of parcels ---
parcels = [
    {"tracking_id": "PCTS-001", "status": "Delivered", "weight_kg": 1.2},
    {"tracking_id": "PCTS-002", "status": "In Transit", "weight_kg": 3.0},
    {"tracking_id": "PCTS-003", "status": "Booked",     "weight_kg": 0.5},
]

print("\nAll parcels:")
for parcel in parcels:
    print(f"  {parcel['tracking_id']} | {parcel['status']} | {parcel['weight_kg']} kg")

# --- Example 4: range() â€” loop a specific number of times ---
print("\nGenerating sample tracking IDs:")
for i in range(1, 6):       # 1, 2, 3, 4, 5
    tid = f"PCTS-20240925-{i:04d}"   # :04d pads with zeros â†’ 0001, 0002 ...
    print(" ", tid)

# --- Example 5: List comprehension (a compact for loop that builds a list) ---
weights = [0.5, 1.5, 3.0, 7.0, 25.0]
# For each weight, calculate the charge (simplified rule: weight * 30)
charges = [w * 30 for w in weights]
print("\nWeights:", weights)
print("Charges:", charges)


# =============================================================
# PART 3 â€” while loop
# =============================================================
# A "while" loop keeps repeating AS LONG AS a condition is True.
# Warning: if the condition never becomes False, it runs forever (infinite loop).
# Always make sure the condition will eventually become False.
# =============================================================

print("\n=== PART 3: while loop ===\n")

# --- Example 1: Simulate retrying Tracking ID generation ---
import random

MAX_RETRIES = 5
attempt = 0
tracking_id = None

while attempt < MAX_RETRIES:
    attempt += 1
    # Simulate generating a random ID (in real code, we check if it already exists)
    candidate_id = f"PCTS-{random.randint(1000, 9999)}"
    print(f"  Attempt {attempt}: Generated {candidate_id}")
    tracking_id = candidate_id
    break   # In a real system, break only when we confirm it's unique

print(f"Final Tracking ID assigned: {tracking_id}")

# --- Example 2: break and continue ---
print("\nLooping through statuses, stopping at 'Delivered':")
for s in parcel_statuses:
    if s == "At Warehouse":
        continue    # skip this one, jump to next iteration
    if s == "Delivered":
        print(f"  Reached final status: {s}")
        break       # stop the loop entirely
    print(f"  Processing status: {s}")

