# Edge Cases

## What is an Edge Case?

An edge case is an unusual or unexpected situation that can happen while using the system.
If the system does not handle edge cases properly, it can crash, store bad data, or confuse
the user.

This document lists known edge cases for each part of the system and describes how the
system should respond to each one.

> **Rule:** For every edge case, the system should either:
> - Reject the bad input with a clear, human-readable error message, OR
> - Handle it gracefully without crashing or losing data.

---

## 1. Authentication Edge Cases

| ID    | Situation                                     | How the System Should Respond                         |
|-------|-----------------------------------------------|-------------------------------------------------------|
| EC-01 | User tries to log in with wrong password.     | Return: "Invalid email or password." (do not reveal which one is wrong) |
| EC-02 | User tries to log in with an email that does not exist. | Same message: "Invalid email or password."    |
| EC-03 | User submits the login form with empty fields.| Return: "Email and password are required."           |
| EC-04 | User tries to access an admin page without being an admin. | Return: 403 Forbidden — "You do not have permission to access this page." |
| EC-05 | User tries to register with an email that already exists. | Return: "This email is already registered."   |
| EC-06 | User submits a password shorter than the minimum length. | Return: "Password must be at least 8 characters." |
| EC-07 | A logged-out user tries to access a protected page. | Redirect to the login page.                    |

---

## 2. Customer Management Edge Cases

| ID    | Situation                                          | How the System Should Respond                    |
|-------|----------------------------------------------------|--------------------------------------------------|
| EC-08 | Admin tries to view a customer that does not exist.| Return: 404 Not Found — "Customer not found."   |
| EC-09 | Admin submits a customer form with a missing required field. | Return a validation error listing the missing fields. |
| EC-10 | Admin enters an invalid phone number (e.g., letters). | Return: "Phone number must contain only digits." |
| EC-11 | Admin deletes a customer who has existing parcels. | Return: "Cannot delete customer with existing parcels." (do not delete) |

---

## 3. Parcel Booking Edge Cases

| ID    | Situation                                           | How the System Should Respond                        |
|-------|-----------------------------------------------------|------------------------------------------------------|
| EC-12 | Customer submits a booking with a missing required field (e.g., no destination city). | Return a clear validation error. |
| EC-13 | Customer enters a parcel weight of 0 or a negative number. | Return: "Parcel weight must be greater than 0." |
| EC-14 | Customer enters a parcel weight that is not a number (e.g., "abc"). | Return: "Parcel weight must be a valid number." |
| EC-15 | Source city and destination city are the same.      | Return: "Source and destination cities cannot be the same." |
| EC-16 | The system fails to generate a unique Tracking ID (collision). | Retry with a new ID; log the event. If retries fail, return a 500 error. |
| EC-17 | A parcel booking is submitted for a customer ID that does not exist. | Return: 400 Bad Request — "Customer not found." |

---

## 4. Parcel Tracking Edge Cases

| ID    | Situation                                             | How the System Should Respond                            |
|-------|-------------------------------------------------------|----------------------------------------------------------|
| EC-18 | User searches with an empty Tracking ID field.        | Return: "Please enter a Tracking ID."                    |
| EC-19 | User enters a Tracking ID that does not exist.        | Return: "No parcel found with this Tracking ID."         |
| EC-20 | User enters a Tracking ID with spaces or special characters. | Strip whitespace and normalize the ID before searching. |
| EC-21 | MongoDB is unavailable when tracking history is requested. | Return the current status from MySQL, and show a warning: "Tracking history is temporarily unavailable." |

---

## 5. Status Update Edge Cases

| ID    | Situation                                               | How the System Should Respond                               |
|-------|---------------------------------------------------------|-------------------------------------------------------------|
| EC-22 | Admin tries to set a parcel to a status that does not exist. | Return: "Invalid status value."                         |
| EC-23 | Admin tries to update a parcel that is already `Delivered`. | Return: "Cannot update status of a delivered parcel."   |
| EC-24 | Admin tries to move a parcel backward in status (e.g., from `Delivered` back to `Booked`). | Return: "Invalid status transition." |
| EC-25 | A delivery person tries to update a parcel not assigned to them. | Return: 403 Forbidden — "You are not assigned to this parcel." |

Valid status transitions (in order):
```
Booked → Picked Up → In Transit → At Warehouse → Out for Delivery → Delivered
                                                                  ↘ Failed Delivery → Returned
```

---

## 6. Delivery Assignment Edge Cases

| ID    | Situation                                                   | How the System Should Respond                       |
|-------|-------------------------------------------------------------|-----------------------------------------------------|
| EC-26 | Admin tries to assign a parcel that is already assigned.    | Return: "This parcel is already assigned to a delivery person." |
| EC-27 | Admin tries to assign a parcel that is already delivered.   | Return: "Cannot assign a delivered parcel."         |
| EC-28 | Admin tries to assign to a delivery person who does not exist or is inactive. | Return: "Delivery person not found or inactive." |
| EC-29 | Admin tries to assign a parcel that does not exist.         | Return: 404 Not Found — "Parcel not found."        |

---

## 7. Payment Edge Cases

| ID    | Situation                                               | How the System Should Respond                               |
|-------|---------------------------------------------------------|-------------------------------------------------------------|
| EC-30 | Admin tries to record a payment for a parcel that already has a `Paid` status. | Return: "Payment already completed for this parcel." |
| EC-31 | Payment amount is zero or negative.                     | Return: "Payment amount must be greater than 0."            |
| EC-32 | Payment is submitted for a parcel ID that does not exist.| Return: 404 Not Found — "Parcel not found."                |
| EC-33 | Admin tries to view a payment record that does not exist.| Return: 404 Not Found — "Payment record not found."        |

---

## 8. Database Edge Cases

| ID    | Situation                                      | How the System Should Respond                                |
|-------|------------------------------------------------|--------------------------------------------------------------|
| EC-34 | MySQL database connection fails at startup.    | Log the error; show a "Service Unavailable" page (503).     |
| EC-35 | MongoDB connection fails.                      | Continue serving requests that don't need MongoDB; log the error and show a warning for tracking history. |
| EC-36 | A unique constraint violation (e.g., duplicate email). | Catch the database error and return a friendly message: "This value already exists." |
| EC-37 | A foreign key constraint violation.            | Catch the database error and return: "Referenced record not found." |
| EC-38 | A transaction fails midway (e.g., parcel saved but payment not). | Roll back the entire transaction; return a 500 error and log the failure. |

---

## 9. General / Input Validation Edge Cases

| ID    | Situation                                          | How the System Should Respond                             |
|-------|----------------------------------------------------|-----------------------------------------------------------|
| EC-39 | A text field receives an extremely long string.    | Pydantic/database length constraint returns an error.     |
| EC-40 | A user sends a request with the wrong data type (e.g., text where a number is expected). | Pydantic validation returns: 422 Unprocessable Entity. |
| EC-41 | A user sends a completely malformed JSON body.     | FastAPI returns: 422 Unprocessable Entity automatically.  |
| EC-42 | An API endpoint is called with missing query parameters. | Return: 422 Unprocessable Entity with details.        |

---

## Summary

The key principle for all edge cases:

> **Never crash. Never lose data. Always tell the user what went wrong in a clear,
> simple message.**

When writing code, every function that touches the database should be wrapped in a
`try-except` block. Validation should be done with Pydantic before data reaches the
database layer.