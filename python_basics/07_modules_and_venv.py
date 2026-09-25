# =============================================================
# 07_modules_and_venv.py
# Topic: Modules, Imports, pip, and Virtual Environments
# =============================================================
# A MODULE is a Python file that contains reusable code.
# You IMPORT a module to use its functions, classes, and variables.
#
# There are 3 types of modules:
#   1. Built-in modules â€” come with Python (no install needed)
#   2. Third-party modules â€” installed via pip (e.g., FastAPI, SQLAlchemy)
#   3. Your own modules â€” .py files you write yourself
# =============================================================

print("=== PART 1: Built-in Modules ===\n")

# --- datetime: for working with dates and times ---
from datetime import datetime, date, timedelta

now = datetime.now()
print("Current datetime:", now)
print("Formatted       :", now.strftime("%Y-%m-%d %H:%M:%S"))
print("Date only       :", now.strftime("%Y%m%d"))   # used in Tracking ID

# Calculating a delivery deadline (3 days from now)
deadline = now + timedelta(days=3)
print("Delivery deadline:", deadline.strftime("%d %B %Y"))

# Comparing dates
booking_date = date(2024, 9, 20)
today = date.today()
days_since_booking = (today - booking_date).days
print(f"\nDays since booking: {days_since_booking} days")


# --- uuid: for generating unique IDs ---
import uuid

unique_id = uuid.uuid4()
print("\nRandom UUID      :", unique_id)
print("UUID as string   :", str(unique_id))
# We won't use uuid for our tracking ID (we use a custom format),
# but uuid is useful for session tokens, API keys, etc.


# --- random: for random numbers ---
import random

# Generate a random 4-digit sequence number
seq = random.randint(1000, 9999)
print(f"\nRandom sequence  : {seq}")

# Shuffle a list
statuses = ["Booked", "In Transit", "Delivered"]
random.shuffle(statuses)
print("Shuffled list    :", statuses)


# --- os: for working with the operating system ---
import os

print("\nCurrent directory:", os.getcwd())
print("PATH env variable:", os.environ.get("PATH", "Not set")[:60], "...")
# os.environ is how you'll read the DATABASE_URL from your .env file later


# --- json: for working with JSON data ---
import json

# Python dict â†’ JSON string (used when sending API responses)
parcel_dict = {
    "tracking_id": "PCTS-001",
    "status": "Booked",
    "charge": 75.0
}
json_string = json.dumps(parcel_dict, indent=2)
print("\nDict â†’ JSON:\n", json_string)

# JSON string â†’ Python dict (used when receiving API requests)
received_json = '{"tracking_id": "PCTS-002", "weight_kg": 3.5}'
parsed_dict = json.loads(received_json)
print("JSON â†’ Dict:", parsed_dict)
print("Type:", type(parsed_dict))


# --- hashlib: for hashing passwords ---
import hashlib

# In Phase 10, we'll use bcrypt (a third-party library).
# Here's a basic example to understand what hashing means:
password = "MySecret123"
hashed = hashlib.sha256(password.encode()).hexdigest()
print(f"\nOriginal : {password}")
print(f"SHA-256  : {hashed}")
print("(Hashing is one-way â€” you cannot get the original password back)")


print("\n=== PART 2: Importing Your Own Modules ===\n")

# When you write a function in another .py file, you can import it here.
# Example: if you have a file called "charge_calculator.py" with a function
# called "calculate_charge", you can do:
#
#   from charge_calculator import calculate_charge
#
# Or import the whole file as a module:
#   import charge_calculator
#   charge_calculator.calculate_charge(2.5)
#
# We'll use this pattern when we split the FastAPI app into multiple files.

print("Module import pattern:")
print("  from routes.parcels import router")
print("  from services.parcel_service import create_parcel")
print("  from models.parcel import Parcel")
print("  from schemas.parcel import ParcelCreate, ParcelResponse")
print("\nThese imports will be used starting in Phase 7 (FastAPI).")


print("\n=== PART 3: Virtual Environment and pip ===\n")

# =============================================================
# What is a Virtual Environment?
# =============================================================
# When you install a Python package with pip, it installs it
# GLOBALLY on your computer by default.
#
# Problem: If Project A needs FastAPI v0.95 and Project B needs
# FastAPI v0.115, installing globally causes a conflict.
#
# Solution: A virtual environment (venv) is a SEPARATE, ISOLATED
# Python installation just for ONE project.
# Each project has its own packages that don't interfere with otheRs.
#
# Commands:
#   Create:   python -m venv venv
#   Activate: venv\Scripts\activate      (Windows)
#             source venv/bin/activate   (Mac/Linux)
#   Install:  pip install fastapi
#   Freeze:   pip freeze > requirements.txt
#   Deactivate: deactivate
# =============================================================

print("Virtual environment is located at: d:\\PCTS\\venv\\")
print("(Created separately â€” see below)")

print("""
How to activate the virtual environment:
  1. Open a terminal/command prompt
  2. Navigate to the project:   cd d:\\PCTS
  3. Activate:                  venv\\Scripts\\activate
  4. Your prompt changes to:    (venv) PS D:\\PCTS>
  5. Now pip installs stay inside this project only.
""")

print("=== PART 4: requirements.txt ===\n")

print("""
requirements.txt lists all the packages your project needs.
Anyone can recreate your environment with:
  pip install -r requirements.txt

This is why we put 'venv/' in .gitignore â€” we never commit
the venv folder. Instead, we commit requirements.txt.
""")

