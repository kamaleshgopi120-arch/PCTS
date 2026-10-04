# Sequence Diagram

## What is a Sequence Diagram?

A **Sequence Diagram** is an interaction diagram in the Unified Modeling Language (UML) that depicts **how objects, services, and actors collaborate over time** to carry out a specific scenario.

It emphasizes the **chronological sequence** of messages exchanged across system boundaries, showing:
- **Actors & Lifelines:** The entities participating in the interaction (Customer, Web Frontend, API Gateway, Databases).
- **Activation Bars:** The duration during which an entity is actively performing a computation.
- **Synchronous Calls (Solid arrows with filled heads):** Request-response calls where the caller waits for a result.
- **Asynchronous Calls (Solid arrows with open heads):** Fire-and-forget messages (e.g., logging an event to MongoDB).
- **Return Messages (Dashed arrows):** Data returned back up the stack.
- **Combined Fragments (Alt / Opt):** Conditional logic, exception handling, and transaction rollbacks.

In the Parcel and Courier Tracking System (PCTS), sequence diagrams capture the mission-critical workflows of **parcel booking**, **dual-database persistence (MySQL + MongoDB)**, **real-time parcel tracking**, and **delivery state transitions**.

---

## Participating Lifelines in PCTS

| Lifeline | Role & Responsibility in PCTS Architecture |
|---|---|
| **Customer / Actor** | Initiates requests via browser (signs in, inputs booking details, tracks parcels). |
| **Web UI (Frontend)** | Vanilla JS client running on the browser (`api.js`, `book_parcel.js`, `track.js`). Manages JWT bearer tokens and DOM updates. |
| **FastAPI Server** | ASGI Python application handling routing, Pydantic schema validation, and JWT RBAC authorization. |
| **MySQL (RDBMS)** | Relational engine handling ACID transactions, foreign keys, triggers, and relational tables (`parcel`, `payment`, `customer`). |
| **MongoDB (NoSQL)** | Append-only document collection (`tracking_events`) acting as an immutable audit trail and real-time status timeline. |

---

## Core Scenarios

### Scenario 1: Parcel Booking & Dual-Database Settlement (Primary Workflow)

This scenario models the complete parcel registration flow from form submission to confirmation.

```mermaid
sequenceDiagram
    autonumber
    actor Customer as 👤 Customer
    participant UI as 🖥️ Web UI (Browser)
    participant API as ⚡ FastAPI Server
    participant MySQL as 🐬 MySQL Database
    participant Mongo as 🍃 MongoDB Event Store

    Customer->>UI: Fills booking form (weight, dimensions, addresses)
    Customer->>UI: Clicks "Book Parcel & Pay"
    UI->>API: POST /api/parcels/book (Bearer JWT + JSON Payload)
    
    activate API
    API->>API: Validate Pydantic Schema (ParcelCreate)
    alt Invalid Payload (Negative weight, same source/dest)
        API-->>UI: 422 Unprocessable Entity (Field Errors)
        UI-->>Customer: Display validation alert
    else Valid Payload
        API->>API: Calculate Shipping Rate (Weight + Distance + Category)
        API->>MySQL: BEGIN TRANSACTION
        activate MySQL
        API->>MySQL: INSERT INTO parcel (tracking_id, status='Booked', ...)
        API->>MySQL: INSERT INTO payment (amount, status='Completed', ...)
        MySQL-->>API: Row IDs & Generated Tracking ID (e.g. PKG-2026-X84A)
        API->>MySQL: COMMIT
        deactivate MySQL
        
        Note over API,Mongo: Asynchronous Non-Blocking Event Dispatch
        API-)Mongo: insert_one({"tracking_id": "PKG-2026-X84A", "event": "BOOKED", "timestamp": ISODate()})
        activate Mongo
        Mongo-->>API: Acknowledged (WriteResult)
        deactivate Mongo
        
        API-->>UI: 201 Created (ParcelDetails + TrackingNumber)
        deactivate API
        UI-->>Customer: Display Booking Receipt & Printable Barcode
    end
```

---

### Scenario 2: Public Parcel Tracking & Audit Timeline Aggregation

This scenario depicts how any customer or guest retrieves parcel details and its chronological movement history.

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Guest / Customer
    participant UI as 🖥️ Web UI (track.html)
    participant API as ⚡ FastAPI Server
    participant MySQL as 🐬 MySQL DB
    participant Mongo as 🍃 MongoDB Audit Store

    User->>UI: Enter Tracking ID (e.g. PKG-2026-X84A)
    UI->>API: GET /api/tracking/public/{tracking_id}
    activate API
    
    API->>MySQL: SELECT * FROM parcel WHERE tracking_id = ?
    activate MySQL
    MySQL-->>API: Parcel Row (Sender, Receiver, Current Status, Destination)
    deactivate MySQL
    
    alt Parcel Not Found in MySQL
        API-->>UI: 404 Not Found {"detail": "Tracking ID does not exist"}
        UI-->>User: Show "Invalid Tracking ID" Error Badge
    else Parcel Found
        API->>Mongo: find({"tracking_id": ?}).sort({"timestamp": 1})
        activate Mongo
        Mongo-->>API: Array of Status Events [Booked, Picked Up, In Transit...]
        deactivate Mongo
        
        API->>API: Assemble Unified Tracking Payload (Metadata + Timeline)
        API-->>UI: 200 OK (JSON with current_status & timeline events)
        deactivate API
        UI-->>User: Render Interactive Visual Stepper & Geolocation Map
    end
```

---

### Scenario 3: Delivery Status Update & State Machine Transition

This scenario traces how an authenticated Delivery Agent updates the state of a parcel upon physical handoff.

```mermaid
sequenceDiagram
    autonumber
    actor Agent as 🚚 Delivery Agent
    participant UI as 🖥️ Delivery App
    participant API as ⚡ FastAPI Server
    participant MySQL as 🐬 MySQL DB
    participant Mongo as 🍃 MongoDB Audit Store

    Agent->>UI: Selects Parcel -> Changes status to "Delivered"
    Agent->>UI: Enters Recipient Signature & Delivery Notes
    UI->>API: PUT /api/deliveries/{delivery_id}/status (Bearer Token, new_status="Delivered")
    
    activate API
    API->>API: Verify Agent JWT & Role Permission
    API->>MySQL: SELECT status FROM parcel WHERE parcel_id = ?
    activate MySQL
    MySQL-->>API: Current Status = "Out for Delivery"
    deactivate MySQL

    API->>API: Evaluate State Transition Rules (Out for Delivery -> Delivered: Valid)
    
    API->>MySQL: BEGIN TRANSACTION
    activate MySQL
    API->>MySQL: UPDATE parcel SET status = 'Delivered', updated_at = NOW()
    API->>MySQL: UPDATE delivery SET status = 'Delivered', delivered_at = NOW()
    MySQL-->>API: Affected Rows = 1
    API->>MySQL: COMMIT
    deactivate MySQL
    
    API-)Mongo: insert_one({"tracking_id": "...", "status": "DELIVERED", "remarks": "Signed by recipient"})
    
    API-->>UI: 200 OK {"message": "Delivery completed successfully"}
    deactivate API
    UI-->>Agent: Show Success Checkmark & Update Agent Route Queue
```

---

## Detailed Message Catalog

| Msg # | Sender | Receiver | Message Name | Parameters / Content | Response / Side Effect |
|---|---|---|---|---|---|
| **1** | Customer | Web UI | `Submit Booking` | Weight, category, source city, destination city, sender & receiver info | UI validates non-empty inputs |
| **2** | Web UI | FastAPI | `POST /api/parcels/book` | `Authorization: Bearer <jwt>`, JSON parcel payload | API begins processing |
| **3** | FastAPI | Internal | `Validate Schema` | `ParcelCreate` Pydantic model | Rejects with 422 if invalid |
| **4** | FastAPI | MySQL | `BEGIN TRANSACTION` | SQL isolation level Read Committed | Starts transactional boundary |
| **5** | FastAPI | MySQL | `INSERT INTO parcel` | Tracking ID, sender ID, receiver details, dimensions, shipping cost | Generates new relational row |
| **6** | FastAPI | MySQL | `INSERT INTO payment` | `amount`, `payment_method`, `payment_status` | Relational payment row created |
| **7** | FastAPI | MySQL | `COMMIT` | Transaction confirmation | Locks released, changes persisted |
| **8** | FastAPI | MongoDB | `insert_one()` | `tracking_id`, `event_type`, `location`, `timestamp` | Audit timeline document stored |
| **9** | FastAPI | Web UI | `201 Created` | Complete parcel object with generated Tracking Number | UI transitions to confirmation screen |

---

## Visual Diagram

The high-resolution UML Sequence Diagram rendered below illustrates the core **Parcel Booking & Asynchronous Dual-Store Settlement** workflow:

![UML Sequence Diagram — Parcel Booking Workflow](./sequence-diagram.jpg)

---

## Status

✅ **Completed and Verified in Documentation Suite.**
