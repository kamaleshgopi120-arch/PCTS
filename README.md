# Parcel and Courier Tracking System (PCTS)

A web-based system for managing parcel bookings, delivery assignments,
payment records, and real-time parcel tracking — built as a college DBMS project.

---

## Project Description

The Parcel and Courier Tracking System (PCTS) solves the problem of manual, paper-based
courier management. It provides a centralized platform where:

- Customers can book parcels and track them using a unique Tracking ID.
- Administrators can manage customers, parcels, delivery personnel, and payments.
- Delivery personnel can view assigned parcels and update delivery status.
- All data is stored in a proper database and accessible through a REST API.

---

## Technology Stack

| Category        | Technology                  |
|-----------------|-----------------------------|
| Language        | Python 3.x                  |
| Backend API     | FastAPI                     |
| Validation      | Pydantic                    |
| ORM             | SQLAlchemy                  |
| Main Database   | MySQL                       |
| NoSQL Database  | MongoDB (tracking history)  |
| DBMS Component  | PL/SQL (Stored Procedures, Triggers, Functions) |
| Frontend        | HTML, CSS, JavaScript       |
| Version Control | Git + GitHub                |

---

## User Roles

| Role              | Capabilities                                                |
|-------------------|-------------------------------------------------------------|
| **Customer**      | Register, book a parcel, track a parcel, view payments.     |
| **Administrator** | Manage all data: customers, parcels, deliveries, payments, reports. |
| **Delivery Person**| View assigned parcels, update delivery status.             |

---

## Core Features

- ✅ User registration and login with role-based access.
- ✅ Parcel booking with automatic Tracking ID generation.
- ✅ Parcel status tracking with full event history.
- ✅ Delivery assignment and status updates.
- ✅ Payment recording and management.
- ✅ Admin reports for parcels, deliveries, and payments.
- ✅ Tracking history stored in MongoDB (NoSQL).
- ✅ PL/SQL stored procedures, functions, and triggers.

---

## Project Structure

```
PCTS/
├── docs/                      ← UML and ER diagrams
│   ├── use-case-diagram
│   ├── class-diagram
│   ├── state-diagram
│   └── er-diagram
├── backend/                   ← FastAPI application (added in later phases)
├── frontend/                  ← HTML, CSS, JavaScript (added in later phases)
├── sql/                       ← PL/SQL scripts (added in Phase 6)
├── problemStatement.md        ← What problem this project solves
├── requirements.md            ← What the system must do
├── context.md                 ← Quick project reference
├── architecture.md            ← How the system is designed
├── databaseDesign.md          ← Database tables and relationships
├── edge_case.md               ← Edge cases and how to handle them
├── implementation_plan.md     ← Phase-by-phase build plan
└── README.md                  ← This file
```

---

## Documentation Index

| File                    | Purpose                                                        |
|-------------------------|----------------------------------------------------------------|
| [problemStatement.md](./problemStatement.md) | Background, problem being solved, objectives, and scope |
| [requirements.md](./requirements.md)         | Functional and non-functional requirements               |
| [context.md](./context.md)                   | Quick at-a-glance project reference                      |
| [architecture.md](./architecture.md)         | System design, layers, data flow                         |
| [databaseDesign.md](./databaseDesign.md)     | All table schemas and relationships                      |
| [edge_case.md](./edge_case.md)               | Known edge cases and how the system handles them         |
| [implementation_plan.md](./implementation_plan.md) | 23-phase plan for building the project             |

---

## Diagrams (docs/ folder)

| Diagram          | Description                                                      |
|------------------|------------------------------------------------------------------|
| Use Case Diagram | Shows what each user role can do in the system                   |
| Class Diagram    | Shows the data structure and relationships between objects       |
| State Diagram    | Shows all possible statuses of a parcel and valid transitions    |
| ER Diagram       | Shows database tables and how they relate to each other          |

---

## Current Status

> **Phase 1 — Documentation and Design** ✅ Complete
>
> **Phase 2 — UML and ER Diagrams** ✅ Complete
>
> All 4 diagrams are embedded in the `docs/` folder.
> Next: **Phase 3 — Git and GitHub Setup**

---

## Setup Instructions

*(Setup instructions will be added in Phase 3 — Git and GitHub Setup.)*

---

## License

This is a college project created for educational purposes.