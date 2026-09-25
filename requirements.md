# Requirements

## What is a Requirements Document?

A requirements document lists everything the system **must do** (functional requirements)
and the **quality standards** it must meet (non-functional requirements). It is written
before any code is written so the entire team agrees on what is being built.

---

## 1. Functional Requirements

Functional requirements describe the **features and actions** the system must support.

---

### 1.1 User Authentication

| ID    | Requirement                                                           |
|-------|-----------------------------------------------------------------------|
| FR-01 | Users must be able to register with a name, email, and password.      |
| FR-02 | Users must be able to log in using email and password.                |
| FR-03 | The system must support three roles: Admin, Customer, Delivery Person.|
| FR-04 | Each role must only be able to access pages meant for that role.      |
| FR-05 | Users must be able to log out.                                        |

---

### 1.2 Customer Management (Admin Only)

| ID    | Requirement                                                           |
|-------|-----------------------------------------------------------------------|
| FR-06 | Admin can view a list of all registered customers.                    |
| FR-07 | Admin can view detailed information of a specific customer.           |
| FR-08 | Admin can update a customer's information (name, phone, address).     |
| FR-09 | Admin can delete a customer record.                                   |
| FR-10 | Admin can search for a customer by name or email.                     |

---

### 1.3 Parcel Management

| ID    | Requirement                                                                      |
|-------|----------------------------------------------------------------------------------|
| FR-11 | A customer can book a new parcel by filling in sender, receiver, and parcel info.|
| FR-12 | The system must automatically generate a unique Tracking ID when a parcel is booked.|
| FR-13 | Parcel information must include: sender name, receiver name, receiver phone,      |
|       | source city, destination city, parcel type, weight, and description.             |
| FR-14 | The system must calculate delivery charges based on parcel weight.               |
| FR-15 | Admin can view all parcels in the system.                                        |
| FR-16 | Admin can view the details of a specific parcel.                                 |
| FR-17 | Admin can update parcel details before it is dispatched.                         |

---

### 1.4 Parcel Tracking

| ID    | Requirement                                                                        |
|-------|------------------------------------------------------------------------------------|
| FR-18 | Any user (including unregistered users) can track a parcel using its Tracking ID. |
| FR-19 | The tracking page must display the current status of the parcel.                   |
| FR-20 | The tracking page must display the full history of status changes.                 |
| FR-21 | Each tracking history entry must include: status, location, date, and time.        |
| FR-22 | Admin can update the status of any parcel.                                         |
| FR-23 | Every status update must automatically create a new tracking history entry.        |

Parcel status values (in order):
1. `Booked` — Parcel has been registered.
2. `Picked Up` — Parcel collected from sender.
3. `In Transit` — Parcel is moving between locations.
4. `At Warehouse` — Parcel is held at an intermediate warehouse.
5. `Out for Delivery` — Parcel is with the delivery person.
6. `Delivered` — Parcel has been delivered to the receiver.
7. `Failed Delivery` — Delivery attempt was unsuccessful.
8. `Returned` — Parcel returned to sender.

---

### 1.5 Delivery Management

| ID    | Requirement                                                                    |
|-------|--------------------------------------------------------------------------------|
| FR-24 | Admin can add, view, and manage delivery personnel.                            |
| FR-25 | Admin can assign a parcel to a delivery person.                                |
| FR-26 | A delivery person can log in and view all parcels assigned to them.            |
| FR-27 | A delivery person can update the status of their assigned parcel.              |
| FR-28 | A parcel that has already been delivered cannot be re-assigned.                |

---

### 1.6 Payment Management

| ID    | Requirement                                                                    |
|-------|--------------------------------------------------------------------------------|
| FR-29 | When a parcel is booked, a payment record is automatically created.            |
| FR-30 | Payment information must include: amount, payment method, and payment status.  |
| FR-31 | Payment status can be: `Pending`, `Paid`, or `Failed`.                        |
| FR-32 | Admin can view and update payment status.                                      |
| FR-33 | A customer can view their own payment details.                                 |

---

### 1.7 Reports (Admin Only)

| ID    | Requirement                                                           |
|-------|-----------------------------------------------------------------------|
| FR-34 | Admin can view a summary of all parcels grouped by status.            |
| FR-35 | Admin can view a summary of all payments grouped by payment status.   |
| FR-36 | Admin can view a list of all deliveries made by each delivery person. |

---

## 2. Non-Functional Requirements

Non-functional requirements describe **how well** the system must work.

| Category          | Requirement                                                                            |
|-------------------|----------------------------------------------------------------------------------------|
| **Performance**   | API responses for normal requests should be fast and not keep the user waiting.        |
| **Security**      | Passwords must be stored using hashing (not plain text).                               |
| **Security**      | API endpoints must be protected so only the correct role can access them.              |
| **Reliability**   | The system must store data consistently and prevent duplicate Tracking IDs.            |
| **Usability**     | The interface must be simple and easy to understand for a first-time user.             |
| **Maintainability**| Code must be organized into clear modules (routes, models, services, schemas).        |
| **Scalability**   | The system must be structured so that new features can be added without rewriting it.  |

---

## 3. Technology Requirements

| Category   | Technology                  | Purpose                                              |
|------------|-----------------------------|------------------------------------------------------|
| Language   | Python 3.x                  | Backend programming language                         |
| Framework  | FastAPI                      | Building the REST API                                |
| Validation | Pydantic                     | Validating request and response data                 |
| ORM        | SQLAlchemy                   | Communicating with MySQL from Python                 |
| Database   | MySQL                        | Storing structured data (customers, parcels, etc.)   |
| NoSQL DB   | MongoDB                      | Storing tracking history logs                        |
| PL/SQL     | MySQL Stored Procedures / Triggers | DBMS laboratory requirement                    |
| Frontend   | HTML, CSS, JavaScript        | Building the web interface                           |
| Version Control | Git + GitHub            | Tracking code changes and collaboration              |

---

## 4. Hardware Requirements

| Item             | Minimum Requirement                  |
|------------------|--------------------------------------|
| Computer/Laptop  | Any modern laptop or desktop         |
| RAM              | 4 GB minimum (8 GB recommended)      |
| Storage          | At least 5 GB free disk space        |
| Internet         | Required for GitHub and package installation |

---

## 5. Constraints

- This is a college project. Complex features like real payment processing are excluded.
- The project must be completable by a single developer learning phase by phase.
- All tools used must be free and open-source.