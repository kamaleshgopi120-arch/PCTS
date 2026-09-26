# =============================================================
# 01_variables_and_types.py
# Topic: Variables and Data Types
# =============================================================
# A variable is a name that holds a value.
# Python figures out the data type automatically (no need to declare it).
# This is called "dynamic typing".
# =============================================================

# --- Basic data types ---

# int (whole numbers)
parcel_id = 1
weight_grams = 1500

# float (decimal numbers)
weight_kg = 1.5
delivery_charge = 75.50

# str (text â€” always inside quotes)
tracking_id = "PCTS-20240925-0001"
customer_name = "Kamalesh"
status = "Booked"

# bool (True or False â€” capital T and F)
is_delivered = False
is_paid = True

# None (represents "no value" / empty)
delivered_at = None   # parcel not delivered yet, so timestamp is None

# --- Print values ---
print("=== Parcel Information ===")
print("Tracking ID  :", tracking_id)
print("Customer     :", customer_name)
print("Weight (kg)  :", weight_kg)
print("Charge (â‚¹)   :", delivery_charge)
print("Status       :", status)
print("Is Paid      :", is_paid)
print("Delivered At :", delivered_at)

# --- Check the type of any variable ---
print("\n=== Data Types ===")
print(type(tracking_id))      # <class 'str'>
print(type(weight_kg))        # <class 'float'>
print(type(parcel_id))        # <class 'int'>
print(type(is_delivered))     # <class 'bool'>
print(type(delivered_at))     # <class 'NoneType'>

# --- String operations ---
print("\n=== String Operations ===")

# f-string: embed variables directly inside a string (most modern way)
message = f"Parcel {tracking_id} is currently: {status}"
print(message)

# String methods
print(tracking_id.lower())        # pcts-20240925-0001
print(customer_name.upper())      # KAMALESH
print("  hello  ".strip())        # "hello" â€” removes whitespace from both ends
print(tracking_id.startswith("PCTS"))  # True
print(tracking_id.split("-"))     # ['PCTS', '20240925', '0001']

# --- Type conversion ---
print("\n=== Type Conversion ===")

weight_input = "2.5"    # user typed this in a form (it arrives as text)
weight_float = float(weight_input)   # convert to float before doing math
print(type(weight_float), weight_float)   # <class 'float'> 2.5

charge = weight_float * 30
print(f"Charge for {weight_float} kg = â‚¹{charge}")

# --- Constants (by convention, use ALL_CAPS names) ---
# Python doesn't have a true constant keyword, but naming in ALL_CAPS
# signals to other developers: "do not change this value."
MAX_WEIGHT_KG = 100.0
MIN_PASSWORD_LENGTH = 8
TRACKING_ID_PREFIX = "PCTS"

print("\nMax allowed parcel weight:", MAX_WEIGHT_KG, "kg")

