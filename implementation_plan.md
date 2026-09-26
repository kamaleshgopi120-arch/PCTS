# Implementation Plan

## What is an Implementation Plan?

An implementation plan breaks the entire project into small, ordered phases.
Each phase focuses on learning one thing and building one part of the system.

> **Rule:** Do not start a new phase until the current phase is fully understood and working.

---

## Phase Overview

| Phase | Name                                | Goal                                                     |
|-------|-------------------------------------|----------------------------------------------------------|
| 1     | Documentation and Design            | Understand the project completely before writing code    |
| 2     | UML and ER Diagrams                 | Visualize the system with standard diagrams              |
| 3     | Git and GitHub Setup                | Set up version control from the very beginning           |
| 4     | Python Fundamentals                 | Ensure Python basics are solid before using frameworks   |
| 5     | MySQL Setup and Raw SQL             | Learn the database independently before using an ORM     |
| 6     | PL/SQL Components                   | Implement stored procedures, functions, and triggers     |
| 7     | FastAPI Introduction                | Build a simple API to understand the framework           |
| 8     | Pydantic Validation                 | Understand how data is validated in FastAPI              |
| 9     | SQLAlchemy and Database Models      | Connect Python to MySQL using an ORM                     |
| 10    | User Authentication API             | Implement login, registration, and role-based access     |
| 11    | Customer Management API             | Implement CRUD operations for customers                  |
| 12    | Parcel Booking API                  | Implement parcel creation and Tracking ID generation     |
| 13    | Parcel Status and Tracking API      | Implement status updates and tracking endpoint           |
| 14    | MongoDB Integration                 | Connect to MongoDB and store tracking history events     |
| 15    | Delivery Management API             | Implement delivery assignment and status updates         |
| 16    | Payment Management API              | Implement payment recording and status management        |
| 17    | Reports API                         | Implement summary report endpoints                       |
| 18    | Exception Handling and Validation   | Harden the API against bad inputs and database errors    |
| 19    | Frontend — Static Pages             | Build the HTML pages and CSS styling                     |
| 20    | Frontend — JavaScript Integration   | Connect the HTML pages to the backend API                |
| 21    | Database Indexing                   | Add indexes to improve query performance                 |
| 22    | Testing                             | Write and run basic tests to verify the system works     |
| 23    | Final Documentation and Submission  | Polish all documentation and submit the project          |

---

## Detailed Phase Descriptions

---

### Phase 1 — Documentation and Design

**Goal:** Fully understand the system before touching any code.

**What you learn:**
- How to write a problem statement.
- How to define functional and non-functional requirements.
- How to plan a software project.

**Deliverables:**
- [ ] `problemStatement.md` — completed.
- [ ] `requirements.md` — completed.
- [ ] `context.md` — completed.
- [ ] `architecture.md` — completed.
- [x] `databaseDesign.md` — completed.
- [x] `edge_case.md` — completed.
- [x] `implementation_plan.md` — this file.
- [x] `README.md` — completed.

**Status:** ✅ Complete

---

### Phase 2 — UML and ER Diagrams

**Goal:** Create visual diagrams that represent the system structure and behavior.

**What you learn:**
- Use Case Diagram — what each user can do.
- Class Diagram — how data/objects are structured.
- State Diagram — how a parcel's status changes over time.
- ER Diagram — how database tables relate to each other.

**Deliverables:**
- [x] `docs/use-case-diagram.md` — Use Case Diagram image embedded.
- [x] `docs/class-diagram.md` — Class Diagram image embedded.
- [x] `docs/state-diagram.md` — State Diagram image embedded.
- [x] `docs/er-diagram.md` — ER Diagram image embedded.

**Tools to use:** draw.io (free, runs in browser at draw.io), or pen and paper scanned.

**Status:** ✅ Complete

---

### Phase 3 — Git and GitHub Setup

**Goal:** Set up version control so every change is tracked from the beginning.

**What you learn:**
- What is Git and why it matters.
- `git init`, `git add`, `git commit`, `git push`.
- How to create a GitHub repository.
- Writing a good commit message.

**Deliverables:**
- [x] Local Git repository initialized (`git init`).
- [x] `.gitignore` file created (excludes `venv/`, `__pycache__/`, `.env`, etc.).
- [x] `.gitattributes` file created (handles line endings on Windows).
- [x] Git identity configured (`user.name` and `user.email`).
- [x] First commit made — 18 files, 2300 insertions.
- [ ] GitHub repository created and remote pushed. *(Do manually — see README)*

**Status:** ✅ Complete

---

### Phase 4 — Python Fundamentals

**Goal:** Make sure the Python skills needed for this project are solid.

**What you learn/review:**
- Variables, data types, conditionals, loops.
- Functions and return values.
- Dictionaries and lists.
- Classes and objects (basic OOP).
- Reading/writing files.
- Exception handling with `try-except`.
- Installing and using packages with `pip`.
- Virtual environments (`venv`).

**Deliverables:**
- [x] Python virtual environment (`venv`) created for the project.
- [x] `requirements.txt` file created with initial packages.
- [x] Small Python practice scripts written (`python_basics/01-07`).

**Status:** ✅ Complete

---

### Phase 5 — MySQL Setup and Raw SQL

**Goal:** Learn the database first using raw SQL before introducing SQLAlchemy.

**What you learn:**
- Installing MySQL on the local machine.
- Creating a database and connecting to it.
- Writing SQL: `CREATE TABLE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`.
- Primary keys, foreign keys, constraints.
- Joins between tables.

**Deliverables:**
- [x] MySQL installed and running (MySQL 8.0.46).
- [x] Database `pcts_db` created.
- [x] All tables from `databaseDesign.md` created using raw SQL (`sql/01_create_tables.sql`).
- [x] Sample data inserted manually to test the structure (`sql/02_sample_data.sql`).
- [x] SQL laboratory queries tested (`sql/03_basic_queries.sql`).
- [x] Python raw connection script verified (`python_basics/08_mysql_raw.py`).

**Status:** ✅ Complete

---

### Phase 6 — PL/SQL Components

**Goal:** Implement the stored procedures, functions, and triggers required for the
DBMS laboratory component.

**What you learn:**
- What a Stored Procedure is and how to write one.
- What a Stored Function is and how it differs from a procedure.
- What a Trigger is and when it fires.
- How to call stored procedures from Python.

**Deliverables:**
- [x] `sql/procedures.sql` file created.
- [x] `calculate_charge` function implemented.
- [x] `update_parcel_status` procedure implemented.
- [x] `trg_after_status_update` trigger implemented.
- [x] `get_monthly_report` procedure implemented.
- [x] All PL/SQL components tested in MySQL Workbench or MySQL CLI.
- [x] Python script `python_basics/09_plsql_procedures.py` verified.

**Status:** ✅ Complete

---

### Phase 7 — FastAPI Introduction

**Goal:** Build and run a simple FastAPI application to understand the framework.

**What you learn:**
- Installing FastAPI and Uvicorn.
- Creating a FastAPI app.
- Defining a GET endpoint.
- Running the app with `uvicorn`.
- Viewing auto-generated docs at `http://127.0.0.1:8000/docs`.

**Deliverables:**
- [x] `backend/main.py` created with a basic "Hello, PCTS!" endpoint.
- [x] App runs locally without errors (`backend/test_app.py` passes).
- [x] Interactive OpenAPI docs accessible at `/docs` and `/redoc`.

**Status:** ✅ Complete

---

### Phase 8 — Pydantic Validation

**Goal:** Understand how Pydantic validates data in FastAPI.

**What you learn:**
- Creating Pydantic models (schemas).
- Required vs optional fields.
- Data type enforcement.
- Custom validators.
- How FastAPI uses Pydantic automatically for request bodies.

**Deliverables:**
- [x] Pydantic schemas created for: User, Customer, Parcel (`backend/schemas/`).
- [x] Validation tested by sending invalid data to the API (and seeing errors) (`backend/test_schemas.py`).
- [x] Enforced edge cases from `edge_case.md` (EC-06, EC-10, EC-13, EC-15).

**Status:** ✅ Complete

---

### Phase 9 — SQLAlchemy and Database Models

**Goal:** Connect FastAPI to MySQL using SQLAlchemy.

**What you learn:**
- What an ORM is and why it is useful.
- Defining SQLAlchemy models (Python classes = database tables).
- Creating a database session.
- CRUD operations using SQLAlchemy (add, query, update, delete).

**Deliverables:**
- [x] `backend/database.py` — database connection setup (engine, SessionLocal, Base, get_db).
- [x] `backend/models/` — all 7 table models created with foreign keys and relationships.
- [x] Basic CRUD and multi-table object graph traversal tested (`backend/test_database.py`).
- [x] Live database health endpoint `/db-health` added with `Depends(get_db)`.

**Status:** ✅ Complete

---

### Phase 10 — User Authentication API

**What you build:** `/api/auth/register` and `/api/auth/login` endpoints.

**What you learn:**
- Password hashing with `passlib` (bcrypt).
- JWT tokens (JSON Web Tokens) for session management.
- How to protect routes with role-based access.

**Deliverables:**
- [x] Register endpoint working (`POST /api/auth/register`).
- [x] Login endpoint returning a signed JWT token (`POST /api/auth/login`).
- [x] Protected routes requiring valid Bearer tokens (`GET /api/auth/me`).
- [x] Role-Based Access Control (RBAC) implemented (`GET /api/auth/admin-only` requiring admin role).
- [x] Automated test suite verified (`backend/test_auth.py`).

**Status:** ✅ Complete

---

### Phase 11 — Customer Management API

**What you build:** CRUD API endpoints for the `customer` table.

**Endpoints:**
- `GET /api/customers` — list all customers (Admin only, paginated).
- `GET /api/customers/{id}` — get one customer (Customer self-access or Admin).
- `PUT /api/customers/{id}` — update customer details.
- `DELETE /api/customers/{id}` — delete customer (Admin only, enforces EC-11 parcel integrity).

**Deliverables:**
- [x] All 4 CRUD endpoints working.
- [x] Query parameter filtering (city, search) and pagination (skip, limit).
- [x] Edge cases handled: EC-08 (not found), EC-10 (phone format), EC-11 (parcels exist).
- [x] Endpoints verified with automated test suite (`backend/test_customers.py`).

**Status:** ✅ Complete

---

### Phase 12 — Parcel Booking API

**What you build:** Parcel creation endpoint with Tracking ID generation.

**Endpoint:** `POST /api/parcels`

**Deliverables:**
- [x] Tracking ID generator implemented with collision resistance (format: `PCTS-YYYYMMDD-XXXX`, EC-16).
- [x] Delivery charge calculation logic matching official weight tiers.
- [x] `POST /api/parcels` endpoint working with atomic transactions (`parcel` + `parcel_status` + `payment`).
- [x] `GET /api/parcels` endpoint working (role-filtered: customer sees own, admin sees all, with filtering & pagination).
- [x] `GET /api/parcels/{id}` endpoint working with owner access control.
- [x] Automated test suite verified (`backend/test_parcels.py`).

**Status:** ✅ Complete

---

### Phase 13 — Parcel Status and Tracking API

**What you build:** Status update and tracking endpoints.

**Endpoints:**
- `GET /api/track/{tracking_id}` — public tracking endpoint (no auth required, normalizes whitespace & uppercase, EC-18, 19, 20).
- `PUT /api/parcels/{id}/status` — update parcel status (admin/delivery staff only).

**Deliverables:**
- [x] Public tracking endpoint working (`GET /api/track/{tracking_id}`).
- [x] Status update endpoint working (`PUT /api/parcels/{id}/status`, restricted to admin/delivery).
- [x] Database trigger `trg_after_status_update` verified recording audit rows in MySQL.
- [x] Automated test suite verified (`backend/test_tracking.py`).

**Status:** ✅ Complete

---

### Phase 14 — MongoDB Integration

**What you build:** Connection to MongoDB and storage of tracking history.

**What you learn:**
- Connecting to MongoDB from Python using `pymongo`.
- Inserting documents into a collection.
- Querying documents by `tracking_id`.

**Deliverables:**
- [ ] `backend/mongo.py` — MongoDB connection.
- [ ] Tracking event saved to MongoDB every time a status is updated.
- [ ] Tracking endpoint returns history from MongoDB.

**Status:** 🔲 Not Started

---

### Phase 15 — Delivery Management API

**What you build:** Delivery assignment and status update endpoints.

**Endpoints:**
- `POST /api/deliveries` — assign a parcel to a delivery person.
- `GET /api/deliveries/my` — delivery person views their assigned parcels.
- `PUT /api/deliveries/{id}/status` — delivery person updates status.

**Status:** 🔲 Not Started

---

### Phase 16 — Payment Management API

**What you build:** Payment viewing and status update endpoints.

**Endpoints:**
- `GET /api/payments/{parcel_id}` — view payment for a parcel.
- `PUT /api/payments/{id}` — update payment status.

**Status:** 🔲 Not Started

---

### Phase 17 — Reports API

**What you build:** Summary report endpoints for the admin.

**Endpoints:**
- `GET /api/reports/parcels` — parcels grouped by status.
- `GET /api/reports/payments` — payments grouped by status.
- `GET /api/reports/deliveries` — deliveries per delivery person.

**Status:** 🔲 Not Started

---

### Phase 18 — Exception Handling and Validation

**Goal:** Ensure the API handles all edge cases from `edge_case.md` gracefully.

**What you learn:**
- FastAPI exception handlers.
- Custom `HTTPException` responses.
- Database transaction rollback on failure.

**Status:** 🔲 Not Started

---

### Phase 19 — Frontend: Static Pages

**What you build:** HTML pages for every screen of the application.

**Pages:**
- `index.html` — Home / landing page.
- `login.html` — Login form.
- `register.html` — Registration form.
- `book_parcel.html` — Parcel booking form.
- `track.html` — Parcel tracking page.
- `dashboard.html` — Admin dashboard.
- `delivery_dashboard.html` — Delivery person dashboard.

**Status:** 🔲 Not Started

---

### Phase 20 — Frontend: JavaScript Integration

**Goal:** Connect the HTML pages to the FastAPI backend.

**What you learn:**
- `fetch()` API in JavaScript.
- Sending GET and POST requests from the browser.
- Displaying API response data in the HTML.
- Storing JWT token in `localStorage`.

**Status:** 🔲 Not Started

---

### Phase 21 — Database Indexing

**Goal:** Add indexes to improve query performance for commonly searched fields.

**What you learn:**
- What a database index is and how it works.
- When to add an index (fields used in WHERE clauses frequently).

**Indexes to add:**
- `parcel.tracking_id` — searched frequently.
- `customer.email` — searched on login.
- `payment.parcel_id` — joined frequently.

**Status:** 🔲 Not Started

---

### Phase 22 — Testing

**Goal:** Verify that all the main features work correctly.

**What you learn:**
- Using FastAPI's built-in test client.
- Writing basic test cases.
- Testing edge cases and error responses.

**Status:** 🔲 Not Started

---

### Phase 23 — Final Documentation and Submission

**Goal:** Polish and finalize everything for submission.

**Deliverables:**
- [ ] All documentation files reviewed and updated.
- [ ] README finalized with setup instructions.
- [ ] All diagrams finalized.
- [ ] Final commit pushed to GitHub.
- [ ] Project presented and submitted.

**Status:** 🔲 Not Started

---

## Progress Tracker

| Phase | Name                            | Status         |
|-------|---------------------------------|----------------|
| 1     | Documentation and Design        | ✅ Complete     |
| 2     | UML and ER Diagrams             | ✅ Complete     |
| 3     | Git and GitHub Setup            | ✅ Complete     |
| 4     | Python Fundamentals             | ✅ Complete     |
| 5     | MySQL Setup and Raw SQL         | ✅ Complete     |
| 6     | PL/SQL Components               | ✅ Complete     |
| 7     | FastAPI Introduction            | ✅ Complete     |
| 8     | Pydantic Validation             | ✅ Complete     |
| 9     | SQLAlchemy and Models           | ✅ Complete     |
| 10    | User Authentication API         | ✅ Complete     |
| 11    | Customer Management API         | ✅ Complete     |
| 12    | Parcel Booking API              | ✅ Complete     |
| 13    | Parcel Status and Tracking API  | ✅ Complete     |
| 14    | MongoDB Integration             | 🔲 Not Started |
| 15    | Delivery Management API         | 🔲 Not Started |
| 16    | Payment Management API          | 🔲 Not Started |
| 17    | Reports API                     | 🔲 Not Started |
| 18    | Exception Handling              | 🔲 Not Started |
| 19    | Frontend: Static Pages          | 🔲 Not Started |
| 20    | Frontend: JS Integration        | 🔲 Not Started |
| 21    | Database Indexing               | 🔲 Not Started |
| 22    | Testing                         | 🔲 Not Started |
| 23    | Final Documentation             | 🔲 Not Started |