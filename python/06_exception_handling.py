# =============================================================
# 06_exception_handling.py
# Topic: try / except / else / finally â€” handling errors gracefully
# =============================================================
# An EXCEPTION is an error that happens while the program is running.
# Without handling it, Python stops the program and prints a traceback.
# With try/except, we catch the error and respond gracefully instead of crashing.
#
# Syntax:
#   try:
#       # code that might fail
#   except SomeError as e:
#       # what to do if that error happens
#   else:
#       # runs ONLY if no exception occurred
#   finally:
#       # runs ALWAYS â€” whether an error happened or not
# =============================================================

print("=== PART 1: Basic try/except ===\n")

# --- Without exception handling (this would crash) ---
# weight_kg = float("abc")   # ValueError: could not convert string to float

# --- With exception handling ---
def parse_weight(raw_input):
    """Safely converts a weight string to float."""
    try:
        weight = float(raw_input)
        if weight <= 0:
            raise ValueError("Weight must be greater than 0.")
        return weight
    except ValueError as e:
        print(f"  Invalid weight input: '{raw_input}' â†’ Error: {e}")
        return None

print("Testing weight parsing:")
print("  Result:", parse_weight("2.5"))      # 2.5
print("  Result:", parse_weight("abc"))      # None (invalid)
print("  Result:", parse_weight("-1"))       # None (invalid)
print("  Result:", parse_weight("0"))        # None (invalid)


print("\n=== PART 2: Multiple except blocks ===\n")

# Different exceptions need different handling.
# Catch the most specific exception first, general ones last.

def get_parcel_by_index(parcels_list, index_input):
    """Gets a parcel from a list using a user-provided index string."""
    try:
        index = int(index_input)       # might raise ValueError if not a number
        parcel = parcels_list[index]   # might raise IndexError if out of range
        return parcel
    except ValueError:
        print(f"  Error: '{index_input}' is not a valid number.")
        return None
    except IndexError:
        print(f"  Error: Index {index_input} is out of range.")
        return None

sample_parcels = [
    {"tracking_id": "PCTS-001", "status": "Booked"},
    {"tracking_id": "PCTS-002", "status": "Delivered"},
]

print("Testing list access:")
print(get_parcel_by_index(sample_parcels, "0"))     # PCTS-001
print(get_parcel_by_index(sample_parcels, "abc"))   # ValueError
print(get_parcel_by_index(sample_parcels, "99"))    # IndexError


print("\n=== PART 3: else and finally ===\n")

def process_payment(amount_input):
    """Processes a payment amount â€” simulates DB save."""
    try:
        amount = float(amount_input)
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        # Simulate saving to database (no actual DB yet)
        print(f"  Processing payment of â‚¹{amount}...")
    except ValueError as e:
        print(f"  Payment failed: {e}")
    else:
        # Runs ONLY if no exception was raised in try
        print("  Payment processed successfully.")
    finally:
        # Runs ALWAYS â€” even if there was an error
        # Good for closing connections, logging, cleanup
        print("  Payment processing attempt completed.")

process_payment("150.0")
print()
process_payment("abc")
print()
process_payment("-50")


print("\n=== PART 4: Raising Exceptions ===\n")

# You can raise your own exceptions using "raise".
# This is how you signal to calling code that something went wrong.

def validate_tracking_id(tracking_id):
    """
    Validates a PCTS tracking ID format.
    Must start with 'PCTS-' and be at least 10 characters long.
    """
    if not tracking_id:
        raise ValueError("Tracking ID cannot be empty.")
    if not tracking_id.startswith("PCTS-"):
        raise ValueError(f"Invalid Tracking ID format: '{tracking_id}'. Must start with 'PCTS-'.")
    if len(tracking_id) < 10:
        raise ValueError(f"Tracking ID too short: '{tracking_id}'.")
    return True

# Test it
test_ids = ["PCTS-20240925-0001", "", "ABCD-001", "PCTS-1"]
for tid in test_ids:
    try:
        validate_tracking_id(tid)
        print(f"  âœ“ Valid: '{tid}'")
    except ValueError as e:
        print(f"  âœ— Invalid: {e}")


print("\n=== PART 5: Custom Exception Classes ===\n")

# You can create your own exception types by inheriting from Exception.
# This lets you be precise about WHAT went wrong.

class PCTSError(Exception):
    """Base exception class for all PCTS-specific erroRs."""
    pass

class ParcelNotFoundError(PCTSError):
    """Raised when a parcel cannot be found by its tracking ID."""
    def __init__(self, tracking_id):
        self.tracking_id = tracking_id
        super().__init__(f"Parcel not found: '{tracking_id}'")

class InvalidStatusError(PCTSError):
    """Raised when an invalid status transition is attempted."""
    def __init__(self, current, attempted):
        super().__init__(
            f"Cannot change status from '{current}' to '{attempted}'."
        )

class DuplicateEmailError(PCTSError):
    """Raised when a user tries to register with an existing email."""
    def __init__(self, email):
        super().__init__(f"Email already registered: '{email}'")


# --- Using custom exceptions ---
def find_parcel(tracking_id, parcel_db):
    parcel = parcel_db.get(tracking_id)
    if parcel is None:
        raise ParcelNotFoundError(tracking_id)
    return parcel

parcel_db = {
    "PCTS-001": {"status": "Delivered"},
    "PCTS-002": {"status": "In Transit"},
}

test_ids = ["PCTS-001", "PCTS-999"]
for tid in test_ids:
    try:
        p = find_parcel(tid, parcel_db)
        print(f"  Found: {tid} â†’ {p['status']}")
    except ParcelNotFoundError as e:
        print(f"  Error: {e}")
    except PCTSError as e:
        # Catch any other PCTS error (parent class)
        print(f"  PCTS Error: {e}")


print("\n=== PART 6: Exception Handling Pattern in PCTS ===\n")

# This is the pattern we'll use in every FastAPI route later:
# 1. Try to do the operation
# 2. Catch specific errors and return appropriate responses
# 3. Always ensure cleanup happens in finally

def simulate_api_update_status(tracking_id, new_status):
    """
    Simulates what a FastAPI route will do when updating parcel status.
    Returns a response dict instead of raising exceptions to the user.
    """
    VALID_STATUSES = [
        "Booked", "Picked Up", "In Transit", "At Warehouse",
        "Out for Delivery", "Delivered", "Failed Delivery", "Returned"
    ]
    parcel_db = {"PCTS-001": {"status": "In Transit"}}

    try:
        # Step 1: validate tracking ID
        validate_tracking_id(tracking_id)

        # Step 2: find the parcel
        parcel = find_parcel(tracking_id, parcel_db)

        # Step 3: validate new status
        if new_status not in VALID_STATUSES:
            raise InvalidStatusError(parcel["status"], new_status)

        # Step 4: apply update
        parcel["status"] = new_status
        return {"success": True, "message": f"Status updated to '{new_status}'"}

    except (ParcelNotFoundError, InvalidStatusError, ValueError) as e:
        return {"success": False, "error": str(e)}
    finally:
        pass   # In real code: close DB session here

# Test the simulation
print(simulate_api_update_status("PCTS-001", "Out for Delivery"))  # success
print(simulate_api_update_status("PCTS-999", "Delivered"))          # not found
print(simulate_api_update_status("PCTS-001", "Flying"))             # invalid status
print(simulate_api_update_status("", "Booked"))                     # empty ID

