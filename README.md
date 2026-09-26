# Parcel and Courier Tracking System (PCTS)

[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?style=flat&logo=python)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1.svg?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-8.0-47A248.svg?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Tests](https://img.shields.io/badge/Tests-16%2F16%20Passing%20(100%25)-success.svg)](backend/test_all.py)
[![License](https://img.shields.io/badge/Project-DBMS%20College%20Capstone-indigo.svg)](#license)

A modern, production-grade Parcel and Courier Tracking System (PCTS) engineered as a comprehensive Database Management Systems (DBMS) project. PCTS bridges high-concurrency relational data management with immutable NoSQL audit logging, wrapped in a high-performance FastAPI asynchronous backend and a sleek, glassmorphic dark-mode web application.

---

## 🌟 Architecture & Highlights

PCTS employs a **Hybrid Polyglot Database Architecture**:

```
                                  +------------------------------+
                                  |   Vanilla HTML5 / CSS3 / JS  |
                                  |     (Frontend User Portals)  |
                                  +--------------+---------------+
                                                 |
                                         HTTP / REST (JSON)
                                                 |
                                                 v
                                  +------------------------------+
                                  |      FastAPI ASGI Engine     |
                                  | (Pydantic v2 + JWT Security) |
                                  +-------+--------------+-------+
                                          |              |
                    SQLAlchemy 2.0 (Pool) |              | PyMongo (Async/Pool)
                                          v              v
                  +-------------------------------+   +-------------------------------+
                  |       MySQL 8.0 Server        |   |       MongoDB 8.0 NoSQL       |
                  |  - ACID Relational Entities   |   |  - Append-Only Event Store    |
                  |  - Stored Procedures & Trigs  |   |  - Chronological Checkpoints  |
                  |  - High-Speed B-Tree Indexes  |   |  - Compound Indexed History   |
                  +-------------------------------+   +-------------------------------+
```

1. **Relational MySQL 8.0 Engine (ACID Core):**
   - Stores structured operational entities: `user`, `customer`, `delivery_person`, `parcel`, `parcel_status`, `delivery`, and `payment`.
   - Native PL/SQL triggers (`trg_after_status_update`, `trg_after_parcel_booking`, `trg_prevent_delivered_status_reversal`).
   - Stored procedures (`ProcessMonthlyReport`, `AssignDeliveryAgent`, `RecordPaymentSettlement`).
   - B-Tree indexes optimizing queries from full-table scans to $O(\log N)$ index scans.
2. **NoSQL MongoDB 8.0 Event Store (Audit Trail):**
   - High-throughput, append-only collection (`tracking_history`) storing chronological checkpoint event logs.
   - Compound index `{ tracking_id: 1, timestamp: -1 }` enabling instantaneous timeline lookups.
   - Built-in fault tolerance: continues serving real-time MySQL state gracefully if MongoDB encounters network outages (EC-21 & EC-35).
3. **Enterprise REST API (FastAPI + Pydantic v2):**
   - Role-Based Access Control (RBAC) with bcrypt hashed credentials and cryptographically signed JWT Bearer tokens.
   - Centralized exception handling normalizing 42 critical business edge cases.
4. **Rich Vanilla Frontend Interface:**
   - 7 static pages built with standard HTML5, Vanilla CSS, and modern typography (`Outfit` + `Plus Jakarta Sans`).
   - Zero framework dependencies, pure modern JavaScript API integrations.

---

## 👥 User Roles & Permissions

| Role | Permissions & Portals | Access URL |
| :--- | :--- | :--- |
| **Public / Guest** | Real-time tracking by 8-character ID, view standard rate slabs, register. | [`/static/index.html`](http://localhost:8000/static/index.html), [`/static/track.html`](http://localhost:8000/static/track.html) |
| **Customer** | Book shipments with live tiered pricing preview, view personal parcel history. | [`/static/book_parcel.html`](http://localhost:8000/static/book_parcel.html) |
| **Administrator** | Live operations command center, KPI analytics, courier dispatch assignment. | [`/static/dashboard.html`](http://localhost:8000/static/dashboard.html) |
| **Delivery Agent** | Field workspace, active route queues, click-to-call, status milestone updates. | [`/static/delivery_dashboard.html`](http://localhost:8000/static/delivery_dashboard.html) |

---

## 🔑 Demo Login Credentials

For quick evaluation and grading, single-click presets are provided on the [Sign In Page](http://localhost:8000/static/login.html):

| Role | Email Address | Password | Profile Details |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@pcts.com` | `Admin@12345` | HQ Operations Manager |
| **Delivery Agent** | `ravi.delivery@pcts.com` | `Delivery@12345` | Ravi Varma (Zone: Mumbai Central, Bike) |
| **Customer** | `arun.kumar@gmail.com` | `Customer@12345` | Arun Kumar (Registered Sender) |

---

## 📦 Project Structure

```
PCTS/
├── backend/                        # FastAPI Backend Application
│   ├── main.py                     # ASGI Entrypoint & Router Orchestrator
│   ├── database.py                 # SQLAlchemy Engine & Session Pool
│   ├── mongo.py                    # MongoDB Connection & NoSQL Event Store
│   ├── security.py                 # Password Hashing & JWT Verification
│   ├── exceptions.py               # Centralized Global Exception Handlers
│   ├── models/                     # SQLAlchemy Relational Models (User, Parcel, etc.)
│   ├── schemas/                    # Pydantic v2 Request/Response Validation Models
│   ├── routers/                    # Modular API Endpoints
│   │   ├── auth.py                 # Authentication & User Management
│   │   ├── customers.py            # Customer Profiles
│   │   ├── parcels.py              # Parcel Booking & Rate Calculation
│   │   ├── tracking.py             # Public Parcel Tracking
│   │   ├── deliveries.py           # Courier Dispatch & Milestone Transitions
│   │   ├── payments.py             # Payment Settlement
│   │   └── reports.py              # Operational Analytics & Stored Procedures
│   └── test_*.py                   # 16 Automated Test Suites (test_all.py master)
├── frontend/                       # Vanilla Frontend Web Application
│   ├── index.html                  # Landing page & quick tracking search
│   ├── login.html                  # Unified authentication portal with presets
│   ├── register.html               # Customer self-registration
│   ├── book_parcel.html            # Parcel booking & live pricing calculator
│   ├── track.html                  # 5-stage progress wizard & MongoDB event logs
│   ├── dashboard.html              # Admin command center & agent assignment modal
│   ├── delivery_dashboard.html     # Courier agent field task workspace
│   ├── css/style.css               # Master design system (glassmorphism & tokens)
│   └── js/                         # Vanilla JavaScript API Clients & Modules
├── sql/                            # Database Initialization & PL/SQL Components
│   ├── 01_create_tables.sql        # Table DDL & Relational Constraints
│   ├── 02_sample_data.sql          # Seed Records & Test Fixtures
│   ├── 03_basic_queries.sql        # Standard Query Demonstrations
│   ├── procedures.sql              # Stored Procedures, Functions & Triggers
│   └── 05_indexes.sql              # B-Tree Indexes & Idempotent DDL
├── docs/                           # Documentation & Visual Architecture Models
│   ├── class-diagram.jpg/.md       # UML Class Diagram & Specifications
│   ├── er-diagram.jpg/.md          # Entity-Relationship (ER) Diagram
│   ├── state-diagram.jpg/.md       # Finite State Machine Transition Model
│   └── use-case-diagram.jpg/.md    # Actor & Use Case Specifications
├── architecture.md                 # System Design & Polyglot Database Decisions
├── databaseDesign.md               # Data Dictionary & Schema Specifications
├── edge_case.md                    # 42 Critical Edge Cases & Mitigation Matrix
├── implementation_plan.md          # 23-Phase Master Implementation Plan
├── problemStatement.md             # Business Problem & Project Objectives
├── requirements.md                 # Functional & Non-Functional Specifications
├── requirements.txt                # Python Dependencies
├── .env.example                    # Environment Configuration Template
└── README.md                       # Master Documentation
```

---

## 🚀 Setup & Local Installation

### Prerequisites
- **Python**: 3.12 or newer
- **MySQL**: 8.0 or newer (Running on `localhost:3306`)
- **MongoDB Community Server**: 8.0 or newer (Running on `localhost:27017`)

---

### Step 1: Clone Repository & Setup Virtual Environment

```bash
git clone https://github.com/your-username/PCTS.git
cd PCTS

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

### Step 2: Configure Environment Variables

Copy the provided `.env.example` to `.env`:

```bash
cp .env.example .env
```

Ensure your credentials in `.env` match your local database installation:
```ini
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=pcts_db

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=pcts_db

# JWT Security
SECRET_KEY=supersecretkey_change_in_production_pcts_2024_secure
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

### Step 3: Initialize Databases & Run SQL Migrations

Connect to MySQL and execute the database scripts in order:

```bash
mysql -u root -p < sql/01_create_tables.sql
mysql -u root -p < sql/02_sample_data.sql
mysql -u root -p < sql/procedures.sql
mysql -u root -p < sql/05_indexes.sql
```

*(MongoDB database and collections are created automatically on first connection).*

---

### Step 4: Run the FastAPI Application

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The system will start listening at:
- **Web Frontend:** [http://127.0.0.1:8000/static/index.html](http://127.0.0.1:8000/static/index.html)
- **Interactive OpenAPI Documentation (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Comprehensive Automated Testing

PCTS includes a Master Test Orchestrator executing **16 distinct test suites** covering unit, integration, edge case, and database verification:

### Run All 16 Test Suites:

```bash
python backend/test_all.py
```

### Test Suite Matrix Summary:

```text
=====================================================================================
                          PCTS TEST MATRIX SUMMARY REPORT
=====================================================================================
#    Test Suite / Component                               Time (s)     Status
-------------------------------------------------------------------------------------
1    Phase 07: FastAPI Core & System Endpoints               2.79s     [PASS]
2    Phase 08: Pydantic Schema Validation                    3.03s     [PASS]
3    Phase 09: SQLAlchemy Models & MySQL Pool                1.19s     [PASS]
4    Phase 10: Authentication, JWT & RBAC                    6.46s     [PASS]
5    Phase 11: Customer Management API                       3.75s     [PASS]
6    Phase 12: Parcel Booking & Pricing API                  3.06s     [PASS]
7    Phase 13: Public Parcel Tracking API                    3.16s     [PASS]
8    Phase 14: MongoDB NoSQL Event Store                     3.25s     [PASS]
9    Phase 15: Delivery Management API                       3.47s     [PASS]
10   Phase 16: Payment Settlement & Surcharges               3.46s     [PASS]
11   Phase 17: Reports & Analytics Procedures                2.83s     [PASS]
12   Phase 18: Centralized Exception Handling                2.43s     [PASS]
13   Phase 19: Frontend Static Pages & CSS System            3.32s     [PASS]
14   Phase 20: Frontend JavaScript Integration               7.82s     [PASS]
15   Phase 21: Database Indexing & EXPLAIN Plans             2.76s     [PASS]
16   Phase 22: Full Lifecycle E2E Integration                7.28s     [PASS]
-------------------------------------------------------------------------------------
Total Suites : 16
Passed       : 16 / 16 (100.0%)
Failed       : 0
Total Time   : ~60 seconds
=====================================================================================

[OK] ALL 16 TEST SUITES PASSED FLAWLESSLY! ZERO REGRESSIONS DETECTED. [OK]
```

---

## 📖 Architectural Documentation & Diagrams

| Document | Description | Direct Link |
| :--- | :--- | :--- |
| **System Architecture** | Polyglot persistence, layers, and data flow | [architecture.md](./architecture.md) |
| **Database Design** | Complete relational schemas, data dictionary, and keys | [databaseDesign.md](./databaseDesign.md) |
| **Edge Case Handling** | Analysis of all 42 edge cases and error responses | [edge_case.md](./edge_case.md) |
| **Implementation Plan** | Complete 23-phase engineering roadmap | [implementation_plan.md](./implementation_plan.md) |
| **UML Class Diagram** | Domain entities, attributes, and associations | [docs/class-diagram.md](./docs/class-diagram.md) |
| **ER Diagram** | Relational cardinalities and foreign key schemas | [docs/er-diagram.md](./docs/er-diagram.md) |
| **State Machine Diagram** | Finite state transitions for parcel lifecycle | [docs/state-diagram.md](./docs/state-diagram.md) |
| **Use Case Diagram** | User persona goals and authorization boundaries | [docs/use-case-diagram.md](./docs/use-case-diagram.md) |

---

## 🛡️ Edge Cases & Robustness Handled

PCTS rigorously handles real-world distributed systems conditions as defined in [`edge_case.md`](./edge_case.md):
- **Collision Resistance (EC-16):** Generates guaranteed unique tracking codes (`PCTS-YYYYMMDD-XXXX`) with automated collision retry.
- **Relational Integrity (EC-17, EC-28, EC-29):** Rejects orphaned bookings, invalid customers, or unassigned drivers.
- **State Machine Safeguards (EC-22, EC-23, EC-24):** Prohibits backwards milestone jumps or updating packages already in terminal `Delivered` state.
- **Atomic Rollbacks (EC-38):** Uses multi-table transactions to roll back midway failures cleanly without leaving orphaned records.
- **Fault-Tolerant NoSQL (EC-21, EC-35):** Returns real-time MySQL checkpoint data with non-blocking warnings when MongoDB is temporarily unreachable.
- **Database Outages (EC-34):** Detects connection pool exhaustion or database downtime and serves clean HTTP 503 Service Unavailable responses.

---

## 📜 License & Acknowledgments

Developed as a college Database Management Systems (DBMS) project. Built with FastAPI, MySQL, MongoDB, SQLAlchemy, and modern web standards.