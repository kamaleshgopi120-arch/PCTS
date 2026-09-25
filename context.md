# Project Context

## What is a Context Document?

The context document is a quick reference that anyone — including you, six months from now —
can read to immediately understand **what the project is, why it exists, who uses it,
and what technologies it uses**. Think of it as the "at a glance" summary of the project.

---

## Project Name

**Parcel and Courier Tracking System (PCTS)**

---

## Project Type

College DBMS (Database Management System) Project
with a full-stack web application component.

---

## Purpose

To build a web-based system that manages all operations of a courier company:

- Booking parcels.
- Assigning parcels to delivery personnel.
- Tracking parcel status and history.
- Managing customer and payment information.
- Generating basic reports.

---

## Why This Project Exists

Manual courier management is error-prone and slow. This project replaces paper-based
or disconnected systems with a single, centralized web application backed by a proper
database, making data accurate, searchable, and traceable.

---

## User Roles

| Role              | Description                                                         |
|-------------------|---------------------------------------------------------------------|
| **Customer**      | Registers, books parcels, and tracks them using a Tracking ID.      |
| **Administrator** | Has full control: manages all users, parcels, deliveries, payments. |
| **Delivery Person** | Logs in to view assigned parcels and update delivery status.      |

---

## Core Features

| Feature                   | Description                                              |
|---------------------------|----------------------------------------------------------|
| User Authentication       | Login / logout with role-based access                    |
| Parcel Booking            | Customer submits parcel details to create a booking      |
| Tracking ID Generation    | Auto-generated unique ID assigned to every parcel        |
| Parcel Tracking           | Track current status and full history using Tracking ID  |
| Delivery Assignment       | Admin assigns a parcel to a delivery person              |
| Status Updates            | Delivery person updates status; history is recorded      |
| Payment Management        | Payment record created with each booking; status managed |
| Reports                   | Admin views summaries of parcels, deliveries, payments   |

---

## Technology Stack

| Layer          | Technology                | Why It Is Used                                                    |
|----------------|---------------------------|-------------------------------------------------------------------|
| Backend        | Python + FastAPI          | Python is beginner-friendly; FastAPI makes building APIs easy     |
| Validation     | Pydantic                  | Validates data coming into and going out of the API               |
| ORM            | SQLAlchemy                | Lets us write Python instead of raw SQL to interact with MySQL    |
| Main Database  | MySQL                     | Reliable relational database for structured data                  |
| NoSQL Database | MongoDB                   | Stores flexible tracking history logs (documents, not rows)       |
| PL/SQL         | MySQL Stored Procedures / Triggers | Required for the DBMS laboratory component             |
| Frontend       | HTML, CSS, JavaScript     | Builds the web pages the user sees and interacts with             |
| Version Control| Git + GitHub              | Tracks every code change; enables collaboration and backup        |

---

## How the System Works (Simple Flow)

```
Customer opens the website
        ↓
Fills in parcel booking form (HTML page)
        ↓
Browser sends data to the FastAPI backend (HTTP POST request)
        ↓
Pydantic validates the incoming data
        ↓
FastAPI calls the business logic (Python functions)
        ↓
SQLAlchemy saves the parcel to MySQL database
        ↓
MongoDB saves the first tracking event (status: Booked)
        ↓
Tracking ID is returned to the customer
        ↓
Customer uses Tracking ID to check parcel status (HTML page)
        ↓
FastAPI fetches data from MySQL (parcel info) + MongoDB (history)
        ↓
Data is displayed to the customer
```

---

## Development Philosophy

- **Learn as you build.** Each phase introduces one concept at a time.
- **Keep it simple.** Do not add features that are not in the requirements.
- **Understand before moving on.** Every component should be understood before the next phase starts.
- **Clean code.** Use readable variable names, comments, and consistent formatting.
- **Version control everything.** Every meaningful change goes through Git.

---

## Project Structure (Planned)

```
PCTS/
├── docs/                   ← UML and ER diagrams
├── problemStatement.md     ← What problem this project solves
├── requirements.md         ← What the system must do
├── context.md              ← This file — quick project reference
├── architecture.md         ← How the system is designed
├── databaseDesign.md       ← Database tables and relationships
├── edge_case.md            ← What can go wrong and how to handle it
├── implementation_plan.md  ← Phase-by-phase build plan
└── README.md               ← Project overview for GitHub
```

Application code will be added in later phases.

---

## Current Phase

**Phase 1 — Documentation and Design**
All documentation files are being created and reviewed.
No application code has been written yet.