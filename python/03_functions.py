# =============================================================
# 03_functions.py
# Topic: Functions â€” defining, calling, parameters, return values
# =============================================================
# A function is a reusable block of code that does ONE specific job.
# Instead of writing the same logic again and again, you write it once
# inside a function and call it whenever you need it.
#
# Syntax:
#   def function_name(parameter1, parameter2):
#       # code
#       return value
# =============================================================

print("=== PART 1: Basic Functions ===\n")

# --- Example 1: A function with no parameters ---
def show_welcome():
    """Prints a welcome message for the PCTS system."""
    print("Welcome to the Parcel and Courier Tracking System!")
    print("Track your parcel anytime using your Tracking ID.\n")

show_welcome()   # calling the function


# --- Example 2: A function with parameters ---
def greet_customer(name):
    """Greets a customer by name."""
    print(f"Hello, {name}! How can we help you today?")

greet_customer("Kamalesh")
greet_customer("Priya")


# --- Example 3: A function that RETURNS a value ---
def calculate_charge(weight_kg):
    """
    Calculates delivery charge based on parcel weight.
    Returns the charge as a float.
    """
    if weight_kg <= 0:
        return 0.0
    elif weight_kg <= 1:
        return 50.0
    elif weight_kg <= 5:
        return round(weight_kg * 30, 2)
    elif weight_kg <= 20:
        return round(weight_kg * 20, 2)
    else:
        return round(weight_kg * 15, 2)

# Calling the function and using its return value
charge = calculate_charge(3.5)
print(f"\nCharge for 3.5 kg: â‚¹{charge}")

charge2 = calculate_charge(0.8)
print(f"Charge for 0.8 kg: â‚¹{charge2}")


print("\n=== PART 2: Default Parameters ===\n")

# --- Default parameter: used when the caller doesn't provide that argument ---
def create_status_message(tracking_id, status="Booked", location="Origin"):
    """Creates a tracking status message."""
    return f"[{tracking_id}] Status: {status} | Location: {location}"

# All arguments provided:
msg1 = create_status_message("PCTS-001", "In Transit", "Mumbai Sorting Center")
print(msg1)

# Only tracking_id provided â€” defaults are used:
msg2 = create_status_message("PCTS-002")
print(msg2)

# tracking_id and status provided â€” location uses default:
msg3 = create_status_message("PCTS-003", "Picked Up")
print(msg3)


print("\n=== PART 3: Keyword Arguments ===\n")

# When calling a function, you can specify arguments by name.
# This makes the code more readable and order doesn't matter.
msg4 = create_status_message(
    location="Delhi Warehouse",
    status="At Warehouse",
    tracking_id="PCTS-004"
)
print(msg4)


print("\n=== PART 4: Functions Calling Functions ===\n")

# Functions can call other functions inside them.

def generate_tracking_id(date_str, sequence_number):
    """Generates a tracking ID in format PCTS-YYYYMMDD-XXXX."""
    padded_number = str(sequence_number).zfill(4)   # pad to 4 digits: 1 â†’ 0001
    return f"PCTS-{date_str}-{padded_number}"

def book_parcel(customer_name, weight_kg, date_str, sequence_number):
    """
    Simulates booking a parcel.
    Returns a dict with tracking_id and charge.
    """
    tracking_id = generate_tracking_id(date_str, sequence_number)
    charge = calculate_charge(weight_kg)    # calling another function

    print(f"Parcel booked for {customer_name}")
    print(f"  Tracking ID : {tracking_id}")
    print(f"  Weight      : {weight_kg} kg")
    print(f"  Charge      : â‚¹{charge}")

    return {
        "tracking_id": tracking_id,
        "charge": charge,
        "customer": customer_name
    }

result = book_parcel("Kamalesh", 2.5, "20240925", 1)
print(f"\nReturn value from book_parcel(): {result}")


print("\n=== PART 5: *args â€” variable number of arguments ===\n")

# Sometimes you don't know how many arguments will be passed.
# *args collects all positional arguments into a tuple.

def log_tracking_events(*events):
    """Logs multiple tracking events at once."""
    print(f"Logging {len(events)} event(s):")
    for event in events:
        print(f"  â†’ {event}")

log_tracking_events("Booked")
log_tracking_events("Booked", "Picked Up", "In Transit")


print("\n=== PART 6: Docstrings ===\n")

# A docstring is a description written right after the def line, inside triple quotes.
# It explains what the function does. You can read it with help().

def validate_phone(phone):
    """
    Validates a phone number.
    - Must contain only digits.
    - Must be exactly 10 digits long.
    Returns True if valid, False otherwise.
    """
    return phone.isdigit() and len(phone) == 10

print(validate_phone("9876543210"))   # True
print(validate_phone("98765ABC10"))   # False
print(validate_phone("98765"))        # False

# Read the docstring:
help(validate_phone)

