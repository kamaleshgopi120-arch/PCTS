# =============================================================
# 04_lists_and_dicts.py
# Topic: Lists and Dictionaries â€” the two most used data structures in Python
# =============================================================
# A LIST is an ordered collection of items. Like a numbered queue.
# A DICT (dictionary) stores data as key-value paiRs. Like a form with labels.
# =============================================================

print("=== PART 1: Lists ===\n")

# --- Creating a list ---
# Lists use square brackets [ ]
# Items can be of any type and can be mixed (but usually same type)

parcel_statuses = ["Booked", "Picked Up", "In Transit", "At Warehouse",
                   "Out for Delivery", "Delivered", "Failed Delivery", "Returned"]

# --- Accessing items by index (starts at 0) ---
print("First status :", parcel_statuses[0])    # Booked
print("Last status  :", parcel_statuses[-1])   # Returned (negative index = from end)
print("Steps 2-4    :", parcel_statuses[1:4])  # slicing: index 1, 2, 3

# --- List operations ---
tracking_ids = ["PCTS-001", "PCTS-002", "PCTS-003"]
print("\nBefore:", tracking_ids)

tracking_ids.append("PCTS-004")    # add to end
print("After append:", tracking_ids)

tracking_ids.remove("PCTS-002")    # remove by value
print("After remove:", tracking_ids)

print("Length:", len(tracking_ids))     # number of items

print("Is PCTS-001 in list?", "PCTS-001" in tracking_ids)   # True
print("Is PCTS-002 in list?", "PCTS-002" in tracking_ids)   # False

# --- Looping over a list ---
print("\nAll tracking IDs:")
for tid in tracking_ids:
    print(" -", tid)

# --- Sorting ---
weights = [3.5, 0.5, 10.0, 1.2, 7.8]
weights.sort()
print("\nSorted weights:", weights)
weights.sort(reverse=True)
print("Descending:", weights)

# --- List comprehension (compact way to create a new list) ---
raw_weights = ["1.5", "3.0", "0.8"]       # came in as strings from a form
float_weights = [float(w) for w in raw_weights]   # convert each to float
print("\nConverted weights:", float_weights)

# Filter only heavy parcels (> 2 kg)
heavy = [w for w in float_weights if w > 2.0]
print("Heavy parcels:", heavy)


print("\n=== PART 2: Dictionaries ===\n")

# --- Creating a dictionary ---
# Dicts use curly braces { }
# Each entry is: "key": value
# Keys are usually strings. Values can be anything.

parcel = {
    "parcel_id": 1,
    "tracking_id": "PCTS-20240925-0001",
    "customer_name": "Kamalesh",
    "sender_name": "Kamalesh",
    "receiver_name": "Priya",
    "source_city": "Chennai",
    "destination_city": "Mumbai",
    "weight_kg": 2.5,
    "parcel_type": "Electronics",
    "charge": 75.0,
    "status": "Booked"
}

# --- Accessing values by key ---
print("Tracking ID :", parcel["tracking_id"])
print("Customer    :", parcel["customer_name"])
print("Charge      : â‚¹", parcel["charge"])

# --- Safe access with .get() â€” returns None if key doesn't exist ---
print("Description :", parcel.get("description"))         # None (key missing)
print("Description :", parcel.get("description", "N/A"))  # "N/A" (default)

# --- Adding and updating values ---
parcel["status"] = "Picked Up"       # update existing key
parcel["description"] = "Laptop"     # add new key
print("\nUpdated parcel:", parcel)

# --- Removing a key ---
del parcel["description"]
print("\nAfter deleting 'description':", parcel.get("description"))  # None

# --- Checking if a key exists ---
print("\n'status' in parcel    :", "status" in parcel)
print("'delivered_at' in parcel:", "delivered_at" in parcel)

# --- Looping over a dictionary ---
print("\nAll parcel fields:")
for key, value in parcel.items():
    print(f"  {key}: {value}")

# --- Keys, Values, Items ---
print("\nKeys  :", list(parcel.keys()))
print("Values:", list(parcel.values()))


print("\n=== PART 3: List of Dictionaries ===\n")

# This is the most common pattern in web apps:
# A list of dicts = a "table" of records (like rows in a database table)

parcels = [
    {"tracking_id": "PCTS-001", "status": "Delivered",  "weight_kg": 1.2, "charge": 50.0},
    {"tracking_id": "PCTS-002", "status": "In Transit", "weight_kg": 3.0, "charge": 90.0},
    {"tracking_id": "PCTS-003", "status": "Booked",     "weight_kg": 0.5, "charge": 50.0},
    {"tracking_id": "PCTS-004", "status": "Delivered",  "weight_kg": 7.5, "charge": 150.0},
]

# --- Find a parcel by tracking_id ---
def find_parcel(parcels_list, tracking_id):
    for p in parcels_list:
        if p["tracking_id"] == tracking_id:
            return p
    return None   # not found

found = find_parcel(parcels, "PCTS-002")
print("Found:", found)

not_found = find_parcel(parcels, "PCTS-999")
print("Not found:", not_found)

# --- Filter: get all delivered parcels ---
delivered = [p for p in parcels if p["status"] == "Delivered"]
print(f"\nDelivered parcels ({len(delivered)}):")
for p in delivered:
    print(f"  {p['tracking_id']} â€” â‚¹{p['charge']}")

# --- Aggregate: total revenue ---
total_revenue = sum(p["charge"] for p in parcels)
print(f"\nTotal Revenue: â‚¹{total_revenue}")

# --- Sort parcels by weight ---
sorted_by_weight = sorted(parcels, key=lambda p: p["weight_kg"])
print("\nParcels sorted by weight:")
for p in sorted_by_weight:
    print(f"  {p['tracking_id']} â€” {p['weight_kg']} kg")


print("\n=== PART 4: Nested Dictionaries ===\n")

# A dict inside a dict â€” useful for grouped data

customer = {
    "customer_id": 1,
    "full_name": "Kamalesh",
    "phone": "9876543210",
    "address": {
        "street": "12, Anna Nagar",
        "city": "Chennai",
        "pincode": "600040"
    }
}

print("City    :", customer["address"]["city"])
print("Pincode :", customer["address"]["pincode"])

