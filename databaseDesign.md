# Database Design

## What is a Database Design Document?

This document describes:
- What tables exist in the database.
- What columns (fields) each table has.
- What type of data each column stores.
- How tables are related to each other (relationships).
- What constraints are applied (e.g., unique values, required values).

This is written before any database is created, so it acts as a blueprint.

---

## 1. Overview of Tables

| Table              | Description                                               |
|--------------------|-----------------------------------------------------------|
| `user`             | Stores login credentials and role for every user          |
| `customer`         | Stores personal details of customers                      |
| `delivery_person`  | Stores details of delivery personnel                      |
| `parcel`           | Stores parcel booking details                             |
| `parcel_status`    | Stores the current status of each parcel                  |
| `delivery`         | Links parcels to delivery personnel (assignment record)   |
| `payment`          | Stores payment information for each parcel                |

MongoDB (NoSQL) stores **tracking history** separately — see Section 3.

---

## 2. Table Definitions (MySQL — Relational)

---

### 2.1 `user` Table

Stores login credentials. Every person who uses the system has one row here.

| Column        | Data Type      | Constraint      | Description                              |
|---------------|----------------|-----------------|------------------------------------------|
| `user_id`     | INT            | PRIMARY KEY, AUTO_INCREMENT | Unique ID for each user     |
| `email`       | VARCHAR(100)   | UNIQUE, NOT NULL | Login email address                     |
| `password_hash` | VARCHAR(255) | NOT NULL        | Hashed password (never plain text)       |
| `role`        | ENUM           | NOT NULL        | One of: `customer`, `admin`, `delivery`  |
| `created_at`  | DATETIME       | DEFAULT NOW()   | When the account was created             |

---

### 2.2 `customer` Table

Stores personal details of customers. Linked to `user` with a foreign key.

| Column        | Data Type     | Constraint            | Description                         |
|---------------|---------------|-----------------------|-------------------------------------|
| `customer_id` | INT           | PRIMARY KEY, AUTO_INCREMENT | Unique ID for each customer   |
| `user_id`     | INT           | FOREIGN KEY → `user.user_id`, UNIQUE | Link to login account  |
| `full_name`   | VARCHAR(100)  | NOT NULL              | Customer's full name                |
| `phone`       | VARCHAR(15)   | NOT NULL              | Contact phone number                |
| `address`     | VARCHAR(255)  |                       | Customer's home address             |
| `city`        | VARCHAR(50)   |                       | City                                |

---

### 2.3 `delivery_person` Table

Stores details of delivery personnel. Also linked to `user`.

| Column             | Data Type     | Constraint                            | Description                    |
|--------------------|---------------|---------------------------------------|--------------------------------|
| `delivery_person_id` | INT         | PRIMARY KEY, AUTO_INCREMENT           | Unique ID                      |
| `user_id`          | INT           | FOREIGN KEY → `user.user_id`, UNIQUE  | Link to login account          |
| `full_name`        | VARCHAR(100)  | NOT NULL                              | Full name                      |
| `phone`            | VARCHAR(15)   | NOT NULL                              | Contact number                 |
| `vehicle_number`   | VARCHAR(20)   |                                       | Vehicle plate number           |
| `is_active`        | BOOLEAN       | DEFAULT TRUE                          | Whether the person is active   |

---

### 2.4 `parcel` Table

The central table. Every booked parcel has one row here.

| Column             | Data Type     | Constraint                              | Description                              |
|--------------------|---------------|-----------------------------------------|------------------------------------------|
| `parcel_id`        | INT           | PRIMARY KEY, AUTO_INCREMENT             | Unique parcel ID                         |
| `tracking_id`      | VARCHAR(20)   | UNIQUE, NOT NULL                        | Auto-generated tracking code (e.g. `PCTS-20240925-0001`) |
| `customer_id`      | INT           | FOREIGN KEY → `customer.customer_id`   | Customer who booked the parcel           |
| `sender_name`      | VARCHAR(100)  | NOT NULL                                | Name of the person sending the parcel    |
| `sender_phone`     | VARCHAR(15)   | NOT NULL                                | Sender's phone number                    |
| `receiver_name`    | VARCHAR(100)  | NOT NULL                                | Name of the person receiving the parcel  |
| `receiver_phone`   | VARCHAR(15)   | NOT NULL                                | Receiver's phone number                  |
| `source_city`      | VARCHAR(50)   | NOT NULL                                | City where parcel is picked up           |
| `destination_city` | VARCHAR(50)   | NOT NULL                                | City where parcel is delivered           |
| `parcel_type`      | VARCHAR(50)   | NOT NULL                                | Type (e.g., Document, Electronics, Fragile) |
| `weight_kg`        | DECIMAL(6,2)  | NOT NULL                                | Weight in kilograms                      |
| `description`      | TEXT          |                                         | Optional description of parcel contents  |
| `charge`           | DECIMAL(10,2) | NOT NULL                                | Delivery charge (calculated from weight) |
| `booked_at`        | DATETIME      | DEFAULT NOW()                           | When the parcel was booked               |

---

### 2.5 `parcel_status` Table

Stores the **current** status of each parcel. Updated every time the status changes.

| Column        | Data Type   | Constraint                         | Description                              |
|---------------|-------------|----------------------------------  |------------------------------------------|
| `status_id`   | INT         | PRIMARY KEY, AUTO_INCREMENT        | Unique ID                                |
| `parcel_id`   | INT         | FOREIGN KEY → `parcel.parcel_id`, UNIQUE | One status row per parcel          |
| `status`      | VARCHAR(30) | NOT NULL                           | Current status (e.g., `Booked`, `In Transit`) |
| `location`    | VARCHAR(100)|                                    | Current physical location of the parcel  |
| `updated_at`  | DATETIME    | DEFAULT NOW()                      | Last updated time                        |

> **Note:** The full history of status changes is stored in **MongoDB** (see Section 3).
> This table only holds the latest/current status for quick lookups.

---

### 2.6 `delivery` Table

Records which delivery person is assigned to which parcel.

| Column              | Data Type | Constraint                                          | Description                     |
|---------------------|-----------|-----------------------------------------------------|---------------------------------|
| `delivery_id`       | INT       | PRIMARY KEY, AUTO_INCREMENT                         | Unique ID                       |
| `parcel_id`         | INT       | FOREIGN KEY → `parcel.parcel_id`, UNIQUE            | One assignment per parcel       |
| `delivery_person_id`| INT       | FOREIGN KEY → `delivery_person.delivery_person_id`  | Assigned delivery person        |
| `assigned_at`       | DATETIME  | DEFAULT NOW()                                       | When the assignment was made    |
| `delivered_at`      | DATETIME  |                                                     | When parcel was actually delivered (nullable) |

---

### 2.7 `payment` Table

Stores payment information for each parcel.

| Column           | Data Type     | Constraint                         | Description                               |
|------------------|---------------|------------------------------------|-------------------------------------------|
| `payment_id`     | INT           | PRIMARY KEY, AUTO_INCREMENT        | Unique ID                                 |
| `parcel_id`      | INT           | FOREIGN KEY → `parcel.parcel_id`, UNIQUE | One payment per parcel              |
| `amount`         | DECIMAL(10,2) | NOT NULL                           | Payment amount (same as parcel charge)    |
| `payment_method` | VARCHAR(30)   |                                    | e.g., `Cash`, `Online`, `Card`           |
| `payment_status` | ENUM          | NOT NULL                           | One of: `Pending`, `Paid`, `Failed`      |
| `paid_at`        | DATETIME      |                                    | When payment was made (nullable)          |

---

## 3. MongoDB Collection — Tracking History

MongoDB stores **every status change event** as a document.

### Collection Name: `tracking_history`

### Example Document:

```json
{
  "_id": "ObjectId(...)",
  "tracking_id": "PCTS-20240925-0001",
  "status": "In Transit",
  "location": "Mumbai Sorting Center",
  "updated_by": "admin",
  "timestamp": "2024-09-25T10:30:00Z",
  "notes": "Parcel transferred to outbound truck"
}
```

### Fields:

| Field         | Type     | Description                                         |
|---------------|----------|-----------------------------------------------------|
| `_id`         | ObjectId | Auto-generated unique ID by MongoDB                 |
| `tracking_id` | String   | The parcel's Tracking ID (links to MySQL parcel)    |
| `status`      | String   | The new status applied at this point                |
| `location`    | String   | Where the parcel was at this moment                 |
| `updated_by`  | String   | Username of who made the update                     |
| `timestamp`   | DateTime | When this status change happened                    |
| `notes`       | String   | Optional remarks (e.g., "Driver could not deliver") |

---

## 4. Relationships Between Tables

```
user ──────────────── customer (1 user : 1 customer)
user ──────────────── delivery_person (1 user : 1 delivery person)
customer ───────────── parcel (1 customer : many parcels)
parcel ─────────────── parcel_status (1 parcel : 1 current status)
parcel ─────────────── delivery (1 parcel : 1 delivery assignment)
delivery ────────────── delivery_person (many deliveries : 1 delivery person)
parcel ─────────────── payment (1 parcel : 1 payment)
```

---

## 5. Charge Calculation Rule

Delivery charges will be calculated based on weight:

| Weight Range        | Charge (per kg) |
|---------------------|-----------------|
| 0 – 1 kg            | ₹50 flat        |
| 1.01 – 5 kg         | ₹30 per kg      |
| 5.01 – 20 kg        | ₹20 per kg      |
| Above 20 kg         | ₹15 per kg      |

This logic will be implemented both in Python (service layer) and as a MySQL Stored
Procedure (PL/SQL component).

---

## 6. PL/SQL Components (MySQL)

These will be created in a separate `sql/procedures.sql` file during the PL/SQL phase.

| Component           | Type              | Purpose                                                 |
|---------------------|-------------------|---------------------------------------------------------|
| `calculate_charge`  | Stored Function   | Accepts weight, returns delivery charge                 |
| `update_parcel_status` | Stored Procedure | Updates parcel status and triggers history log (MySQL) |
| `trg_after_status_update` | Trigger    | Fires after `parcel_status` is updated; logs the change |
| `get_monthly_report`| Stored Procedure  | Returns count of parcels grouped by status for a month  |

---

## 7. Database: MySQL (Relational) vs MongoDB (NoSQL)

| Aspect         | MySQL (Relational)                        | MongoDB (NoSQL)                           |
|----------------|-------------------------------------------|-------------------------------------------|
| What is stored | Users, parcels, payments, delivery info   | Tracking history events (one per update)  |
| Structure      | Fixed table columns                       | Flexible JSON-like documents              |
| Why used here  | Structured, related data with constraints | History logs grow unpredictably; flexible |
| Queried by     | SQL (via SQLAlchemy)                      | PyMongo or Motor (Python drivers)         |