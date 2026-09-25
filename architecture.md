# System Architecture

## What is an Architecture Document?

The architecture document explains **how all the parts of the system fit together**.
It answers questions like:
- What layers does the system have?
- How does the frontend talk to the backend?
- Where is data stored?
- How does data flow from the user to the database and back?

---

## 1. Architectural Style

This project uses a **Three-Tier Architecture**:

```
┌──────────────────────────────────┐
│         Presentation Layer        │  ← What the user sees (HTML, CSS, JS)
├──────────────────────────────────┤
│         Application Layer         │  ← Business logic (FastAPI + Python)
├──────────────────────────────────┤
│           Data Layer              │  ← Databases (MySQL + MongoDB)
└──────────────────────────────────┘
```

| Tier                  | Technology Used          | Responsibility                              |
|-----------------------|--------------------------|---------------------------------------------|
| Presentation (Front)  | HTML, CSS, JavaScript    | Displays data; collects user input          |
| Application (Back)    | Python, FastAPI, Pydantic| Processes requests; applies business rules  |
| Data (Database)       | MySQL, MongoDB           | Stores and retrieves all data               |

---

## 2. Communication Style

The frontend and backend communicate using a **REST API** (Representational State Transfer).

This means:
- The frontend sends **HTTP requests** (GET, POST, PUT, DELETE) to the backend.
- The backend processes the request and sends back a **JSON response**.
- The frontend uses JavaScript to read the JSON and update the web page.

```
Browser (HTML + JS)  ──── HTTP Request (JSON) ────►  FastAPI (Python)
Browser (HTML + JS)  ◄─── HTTP Response (JSON) ────  FastAPI (Python)
```

---

## 3. Technology Stack Details

### Frontend (Presentation Layer)
- **HTML** — Defines the structure of each page (forms, tables, buttons).
- **CSS** — Styles the pages (colors, layout, fonts).
- **JavaScript** — Makes pages interactive (calls the API, displays results dynamically).

No frontend framework (like React or Vue) is used to keep things simple.

### Backend (Application Layer)
- **Python** — The programming language for all backend logic.
- **FastAPI** — A Python framework for building REST APIs quickly.
  - Automatically generates API documentation (Swagger UI at `/docs`).
  - Handles routing (e.g., `/api/parcels`, `/api/customers`).
- **Pydantic** — Validates data coming into the API.
  - If a required field is missing or the data type is wrong, Pydantic returns an error
    automatically before the data reaches the database.

### Main Database (Structured Data)
- **MySQL** — A popular relational database.
  - Stores all structured data: users, customers, parcels, deliveries, payments.
  - Data is organized in tables with rows and columns.
  - Relationships are enforced using Foreign Keys.
- **SQLAlchemy** — A Python library (ORM) that translates Python code into SQL queries.
  - Instead of writing `SELECT * FROM parcel WHERE id = 1`, you write Python objects.
  - Makes the code cleaner and less error-prone.

### Secondary Database (Unstructured Data)
- **MongoDB** — A NoSQL (document) database.
  - Used specifically to store **tracking history events**.
  - Each tracking event is a JSON-like document (not a table row).
  - MongoDB is flexible — each event can have slightly different fields.

### PL/SQL Component
- **Stored Procedures** — SQL code saved inside the database that can be called by name.
  - Example: A stored procedure to calculate delivery charge based on weight.
- **Triggers** — SQL code that automatically runs when a database event happens.
  - Example: A trigger that logs a history entry every time a parcel status is updated.
- **Functions** — SQL functions that return a computed value.
  - Example: A function that returns the total number of parcels delivered this month.

---

## 4. Data Flow

### Example: Customer Books a Parcel

```
Step 1: Customer fills in the booking form on the HTML page.

Step 2: JavaScript collects the form data and sends an HTTP POST
        request to: POST /api/parcels

Step 3: FastAPI receives the request.

Step 4: Pydantic validates the data (checks required fields, data types).

Step 5: FastAPI calls the parcel service (Python function).

Step 6: The service generates a unique Tracking ID.

Step 7: SQLAlchemy saves the parcel record to MySQL.

Step 8: A payment record (status: Pending) is also saved to MySQL.

Step 9: The first tracking event (status: Booked) is saved to MongoDB.

Step 10: FastAPI sends back a JSON response containing the Tracking ID.

Step 11: JavaScript reads the response and shows the Tracking ID to
         the customer on the page.
```

### Example: Customer Tracks a Parcel

```
Step 1: Customer enters Tracking ID in the tracking form.

Step 2: JavaScript sends: GET /api/track/{tracking_id}

Step 3: FastAPI receives the Tracking ID.

Step 4: SQLAlchemy fetches the parcel record from MySQL.

Step 5: MongoDB is queried for all history events for that Tracking ID.

Step 6: FastAPI combines both results and sends a JSON response.

Step 7: JavaScript displays the current status and history on the page.
```

---

## 5. Folder Structure (Planned)

When application code is written in later phases, it will be organized as:

```
PCTS/
├── docs/                      ← UML and ER diagrams
├── backend/
│   ├── main.py                ← FastAPI app entry point
│   ├── database.py            ← SQLAlchemy database connection
│   ├── mongo.py               ← MongoDB connection
│   ├── models/                ← SQLAlchemy table definitions
│   │   ├── user.py
│   │   ├── parcel.py
│   │   ├── delivery.py
│   │   └── payment.py
│   ├── schemas/               ← Pydantic request/response schemas
│   │   ├── parcel.py
│   │   └── user.py
│   ├── routes/                ← FastAPI route handlers (API endpoints)
│   │   ├── auth.py
│   │   ├── parcels.py
│   │   ├── customers.py
│   │   ├── delivery.py
│   │   └── payments.py
│   └── services/              ← Business logic functions
│       ├── parcel_service.py
│       └── tracking_service.py
├── frontend/
│   ├── index.html             ← Home / landing page
│   ├── login.html
│   ├── dashboard.html
│   ├── book_parcel.html
│   ├── track.html
│   └── css/
│       └── style.css
├── sql/
│   └── procedures.sql         ← PL/SQL stored procedures and triggers
├── problemStatement.md
├── requirements.md
├── context.md
├── architecture.md
├── databaseDesign.md
├── edge_case.md
├── implementation_plan.md
└── README.md
```

---

## 6. Security Considerations

| Concern              | Approach                                                          |
|----------------------|-------------------------------------------------------------------|
| Passwords            | Stored as hashed values (bcrypt); never stored as plain text.     |
| Role-based access    | Each API endpoint checks the user's role before allowing access.  |
| Input validation     | Pydantic validates all incoming data; rejects invalid requests.   |
| SQL Injection        | SQLAlchemy uses parameterized queries, preventing SQL injection.   |

---

## 7. Summary

| Component  | Technology        | Purpose                                      |
|------------|-------------------|----------------------------------------------|
| Frontend   | HTML, CSS, JS     | User interface                               |
| Backend    | FastAPI (Python)  | REST API and business logic                  |
| Validation | Pydantic          | Input validation                             |
| ORM        | SQLAlchemy        | Python ↔ MySQL bridge                       |
| Main DB    | MySQL             | Structured data storage                      |
| NoSQL DB   | MongoDB           | Flexible tracking history storage            |
| PL/SQL     | MySQL Procedures  | DBMS course requirement                      |
| Version Control | Git + GitHub | Code history and backup                     |