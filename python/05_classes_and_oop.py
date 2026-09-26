# =============================================================
# 05_classes_and_oop.py
# Topic: Classes and Object-Oriented Programming (OOP)
# =============================================================
# A CLASS is a blueprint for creating objects.
# An OBJECT is one instance created from that blueprint.
#
# Real-world analogy:
#   Class = "Parcel Form" (the blank template)
#   Object = one filled-in form (a specific parcel)
#
# OOP key concepts:
#   1. Class â€” the blueprint
#   2. Object â€” an instance of the class
#   3. Attribute â€” data stored inside the object
#   4. Method â€” a function that belongs to the class
#   5. __init__ â€” the constructor (called when object is created)
#   6. self â€” refers to the current object itself
# =============================================================

print("=== PART 1: Basic Class ===\n")

class Parcel:
    """
    Represents a parcel in the PCTS system.
    This is the blueprint for creating parcel objects.
    """

    # __init__ is the constructor.
    # It runs automatically when you do: p = Parcel(...)
    # "self" always refers to the specific object being created.
    def __init__(self, tracking_id, sender_name, receiver_name,
                 source_city, destination_city, weight_kg):
        # Attributes â€” stored data for this specific parcel
        self.tracking_id = tracking_id
        self.sender_name = sender_name
        self.receiver_name = receiver_name
        self.source_city = source_city
        self.destination_city = destination_city
        self.weight_kg = weight_kg
        self.status = "Booked"      # default status when created
        self.charge = self._calculate_charge()   # auto-calculated

    # Methods â€” actions this object can perform
    def _calculate_charge(self):
        """Private method (starts with _). Called internally only."""
        if self.weight_kg <= 1:
            return 50.0
        elif self.weight_kg <= 5:
            return round(self.weight_kg * 30, 2)
        elif self.weight_kg <= 20:
            return round(self.weight_kg * 20, 2)
        else:
            return round(self.weight_kg * 15, 2)

    def update_status(self, new_status):
        """Updates the parcel status."""
        valid_statuses = [
            "Booked", "Picked Up", "In Transit", "At Warehouse",
            "Out for Delivery", "Delivered", "Failed Delivery", "Returned"
        ]
        if new_status not in valid_statuses:
            print(f"Error: '{new_status}' is not a valid status.")
            return False
        self.status = new_status
        print(f"Status updated to: {self.status}")
        return True

    def display(self):
        """Prints all parcel information in a readable format."""
        print(f"  Tracking ID  : {self.tracking_id}")
        print(f"  Sender       : {self.sender_name}")
        print(f"  Receiver     : {self.receiver_name}")
        print(f"  Route        : {self.source_city} â†’ {self.destination_city}")
        print(f"  Weight       : {self.weight_kg} kg")
        print(f"  Charge       : â‚¹{self.charge}")
        print(f"  Status       : {self.status}")

    def __str__(self):
        """
        Special method â€” called when you print() the object.
        Without this, print(parcel) shows something like: <Parcel object at 0x...>
        """
        return f"Parcel({self.tracking_id}, {self.status})"


# --- Creating objects (instances) ---
parcel1 = Parcel(
    tracking_id="PCTS-001",
    sender_name="Kamalesh",
    receiver_name="Priya",
    source_city="Chennai",
    destination_city="Mumbai",
    weight_kg=2.5
)

parcel2 = Parcel("PCTS-002", "Ravi", "Suresh", "Delhi", "Bangalore", 8.0)

# --- Using the objects ---
print("Parcel 1 details:")
parcel1.display()

print("\nParcel 2 details:")
parcel2.display()

print(f"\nprint(parcel1) â†’ {parcel1}")    # uses __str__

# --- Calling methods ---
print()
parcel1.update_status("Picked Up")
parcel1.update_status("In Transit")
parcel1.update_status("Flying")     # invalid â€” should print error

print(f"\nFinal status of parcel1: {parcel1.status}")


print("\n=== PART 2: Class with Class Variables ===\n")

class Customer:
    """Represents a customer in the PCTS system."""

    # Class variable â€” shared by ALL Customer objects
    total_customers = 0

    def __init__(self, customer_id, full_name, phone, city):
        self.customer_id = customer_id
        self.full_name = full_name
        self.phone = phone
        self.city = city
        self.parcels = []    # each customer starts with an empty parcel list

        # Every time a customer is created, increment the class variable
        Customer.total_customers += 1

    def add_parcel(self, parcel):
        """Adds a parcel to this customer's list."""
        self.parcels.append(parcel)
        print(f"Parcel {parcel.tracking_id} added for {self.full_name}")

    def get_parcel_count(self):
        return len(self.parcels)

    def __str__(self):
        return f"Customer({self.customer_id}, {self.full_name})"


c1 = Customer(1, "Kamalesh", "9876543210", "Chennai")
c2 = Customer(2, "Priya", "9123456789", "Mumbai")

print(f"Total customers created: {Customer.total_customers}")   # 2

c1.add_parcel(parcel1)
c1.add_parcel(parcel2)
print(f"{c1.full_name} has {c1.get_parcel_count()} parcel(s)")


print("\n=== PART 3: Inheritance ===\n")

# =============================================================
# Inheritance: A child class inherits all attributes and methods
# from a parent class, and can add or override them.
# =============================================================

class User:
    """Base class for all users (parent)."""

    def __init__(self, user_id, email, role):
        self.user_id = user_id
        self.email = email
        self.role = role

    def login(self):
        print(f"{self.role.capitalize()} '{self.email}' logged in.")

    def logout(self):
        print(f"'{self.email}' logged out.")

    def __str__(self):
        return f"User({self.user_id}, {self.email}, {self.role})"


class AdminUser(User):
    """Admin user â€” inherits from User, adds admin-specific features."""

    def __init__(self, user_id, email):
        # Call the parent class __init__ using super()
        super().__init__(user_id, email, role="admin")

    def delete_customer(self, customer):
        """Admin-only action."""
        print(f"Admin deleted customer: {customer.full_name}")


class DeliveryUser(User):
    """Delivery person â€” inherits from User, adds delivery-specific features."""

    def __init__(self, user_id, email, vehicle_number):
        super().__init__(user_id, email, role="delivery")
        self.vehicle_number = vehicle_number

    def update_delivery_status(self, parcel, new_status):
        """Delivery person updates parcel status."""
        parcel.update_status(new_status)
        print(f"Updated by delivery user {self.email}")


# --- Using inherited classes ---
admin = AdminUser(user_id=1, email="admin@pcts.com")
delivery_person = DeliveryUser(user_id=2, email="driver@pcts.com", vehicle_number="TN01AB1234")

admin.login()           # inherited from User
admin.delete_customer(c1)   # AdminUser-specific

delivery_person.login()     # inherited from User
delivery_person.update_delivery_status(parcel1, "Out for Delivery")  # DeliveryUser-specific

print(f"\nadmin    â†’ {admin}")
print(f"delivery â†’ {delivery_person}")

# Check inheritance
print(f"\nIs admin an AdminUser? {isinstance(admin, AdminUser)}")
print(f"Is admin a User?       {isinstance(admin, User)}")
print(f"Is admin a DeliveryUser? {isinstance(admin, DeliveryUser)}")

