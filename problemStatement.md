# Problem Statement

## Project Title

**Parcel and Courier Tracking System (PCTS)**

---

## Background

In everyday life, people regularly send and receive parcels through courier companies.
Whether it is a document, a product purchased online, or a personal item — the parcel
must travel from the sender's location to the receiver's location, often passing through
multiple checkpoints along the way.

Traditional or manual courier management systems have several weaknesses:

- Parcel records are written on paper and can be lost or damaged.
- There is no easy way for a customer to find out where their parcel is.
- Assigning a delivery person to a parcel is done verbally or on paper, which causes confusion.
- Payment information is stored in separate notebooks or spreadsheets.
- When a parcel is lost or delayed, there is no history to trace back through.
- Administrators cannot generate reports easily because data is scattered.

These problems waste time, cause errors, and make customers unhappy.

---

## Problem Being Solved

This project will solve the above problems by building a **web-based Parcel and Courier
Tracking System** that:

1. Stores all parcel, customer, and delivery information in a structured database.
2. Gives every parcel a **unique Tracking ID** so customers can check its status anytime.
3. Lets administrators manage customers, parcels, delivery personnel, and payments from one place.
4. Keeps a full **history of every status change** a parcel goes through.
5. Allows delivery personnel to log in and view the parcels assigned to them.
6. Calculates delivery charges automatically based on parcel weight.
7. Records payment information and links it to the correct parcel.
8. Generates basic reports for parcels, deliveries, and payments.

---

## Who Will Use the System?

| User Role           | What They Do                                                        |
|---------------------|---------------------------------------------------------------------|
| **Customer**        | Books a parcel, receives a tracking ID, tracks the parcel status.   |
| **Administrator**   | Manages all data: customers, parcels, delivery personnel, payments. |
| **Delivery Person** | Logs in, views assigned parcels, updates delivery status.           |

---

## Main Objectives

1. Provide a centralized database to store all courier-related data.
2. Allow customers to book parcels through a simple web form.
3. Generate a unique Tracking ID for each parcel automatically.
4. Allow customers to track their parcel using the Tracking ID.
5. Allow administrators to assign parcels to delivery personnel.
6. Maintain a full tracking history (every status change with timestamp and location).
7. Store and manage payment information for each parcel.
8. Provide a basic reporting interface for administrators.
9. Use a relational database (MySQL) for structured data storage.
10. Use MongoDB to store tracking history logs (unstructured, flexible data).
11. Demonstrate PL/SQL concepts (stored procedures, triggers, functions) as required
    by the DBMS course.
12. Expose a REST API using FastAPI so the frontend can communicate with the backend.

---

## Scope

### What the system WILL do

- User login with different roles (Customer, Admin, Delivery Person).
- Parcel booking with automatic Tracking ID generation.
- Parcel status tracking with full history.
- Delivery assignment and status updates.
- Payment recording and status management.
- Basic admin reports for parcels, deliveries, and payments.

### What the system WILL NOT do

The following are intentionally excluded to keep the project manageable:

- Real-time GPS location tracking.
- Integration with actual payment gateways (e.g., Razorpay, Stripe).
- Email or SMS notifications to customers.
- Mobile application.
- Multi-branch or franchise management.

> These out-of-scope features are good ideas for future versions of the project.

---

## Expected Outcome

At the end of the project, we will have a working web application where:

- A customer can register, book a parcel, and track it using a Tracking ID.
- An admin can manage the entire system from a dashboard.
- A delivery person can see their assigned parcels and update delivery status.
- All structured data is stored in a MySQL database using SQLAlchemy.
- Tracking event history is stored in MongoDB.
- PL/SQL components are implemented to satisfy the DBMS laboratory requirement.
- The project is version-controlled using Git and hosted on GitHub.