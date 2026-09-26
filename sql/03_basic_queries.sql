-- ============================================================================
-- Parcel and Courier Tracking System (PCTS)
-- File: 03_basic_queries.sql
-- Description: Essential SQL practice queries for the DBMS laboratory component.
-- Target DBMS: MySQL 8.0+
-- ============================================================================

USE pcts_db;

-- ============================================================================
-- 1. BASIC SELECTION AND PROJECTION
-- ============================================================================
-- Retrieve specific columns rather than SELECT * to reduce network overhead.
SELECT tracking_id, sender_name, receiver_name, weight_kg, charge
FROM parcel;

-- ============================================================================
-- 2. FILTERING DATA WITH `WHERE`
-- ============================================================================
-- Query A: Parcels weighing strictly more than 2.0 kg
SELECT tracking_id, parcel_type, weight_kg, charge
FROM parcel
WHERE weight_kg > 2.00;

-- Query B: Parcels originating from 'Chennai' or going to 'Chennai'
SELECT tracking_id, source_city, destination_city
FROM parcel
WHERE source_city = 'Chennai' OR destination_city = 'Chennai';

-- Query C: Pattern matching with LIKE (Find parcels with 'Care' or 'Degree' in description)
SELECT tracking_id, description
FROM parcel
WHERE description LIKE '%Care%' OR description LIKE '%Degree%';

-- Query D: Check for NULL values (Find active deliveries that have NOT been delivered yet)
SELECT delivery_id, parcel_id, assigned_at
FROM delivery
WHERE delivered_at IS NULL;

-- Query E: IN operator (Find payments that are either 'Paid' or 'Pending')
SELECT payment_id, parcel_id, amount, payment_status
FROM payment
WHERE payment_status IN ('Paid', 'Pending');

-- ============================================================================
-- 3. SORTING AND PAGINATION (`ORDER BY`, `LIMIT`, `OFFSET`)
-- ============================================================================
-- Top 3 most expensive parcels (highest charge first)
SELECT tracking_id, receiver_name, weight_kg, charge
FROM parcel
ORDER BY charge DESC
LIMIT 3;

-- Pagination example: Page 2 with 2 parcels per page (LIMIT 2 OFFSET 2)
SELECT parcel_id, tracking_id, sender_name, destination_city
FROM parcel
ORDER BY parcel_id ASC
LIMIT 2 OFFSET 2;

-- ============================================================================
-- 4. AGGREGATE FUNCTIONS AND GROUPING (`COUNT`, `SUM`, `AVG`, `GROUP BY`, `HAVING`)
-- ============================================================================
-- Query A: Overall statistics of all booked parcels
SELECT
    COUNT(*) AS total_parcels,
    SUM(charge) AS total_revenue_expected,
    AVG(charge) AS average_charge,
    MIN(weight_kg) AS lightest_parcel_kg,
    MAX(weight_kg) AS heaviest_parcel_kg
FROM parcel;

-- Query B: Revenue and parcel count grouped by Destination City
SELECT
    destination_city,
    COUNT(*) AS total_parcels,
    SUM(charge) AS total_city_revenue
FROM parcel
GROUP BY destination_city
ORDER BY total_city_revenue DESC;

-- Query C: Grouping with HAVING clause
-- Find customers who booked MORE THAN 2 parcels
SELECT
    customer_id,
    COUNT(*) AS parcel_count,
    SUM(charge) AS total_spent
FROM parcel
GROUP BY customer_id
HAVING COUNT(*) > 2;

-- ============================================================================
-- 5. RELATIONAL JOINS
-- ============================================================================
-- Query A: INNER JOIN between `customer` and `parcel`
-- Retrieves customer details along with each parcel they booked.
SELECT
    c.full_name AS customer_name,
    c.phone AS customer_phone,
    p.tracking_id,
    p.parcel_type,
    p.destination_city,
    p.charge
FROM customer c
INNER JOIN parcel p ON c.customer_id = p.customer_id
ORDER BY c.full_name;

-- Query B: LEFT JOIN between `parcel` and `delivery`
-- Shows ALL parcels, even those not yet assigned to any delivery person!
-- Unassigned parcels will have NULL for delivery fields.
SELECT
    p.tracking_id,
    p.receiver_name,
    p.destination_city,
    d.delivery_id,
    d.assigned_at,
    d.delivered_at
FROM parcel p
LEFT JOIN delivery d ON p.parcel_id = d.parcel_id;

-- Query C: MASTER 6-TABLE JOIN (College DBMS Showcase Query)
-- Joins Customer, Parcel, Parcel Status, Delivery, Delivery Person, and Payment
SELECT
    p.tracking_id,
    c.full_name AS customer_name,
    p.receiver_name,
    p.destination_city,
    ps.status AS current_status,
    ps.location AS current_location,
    COALESCE(dp.full_name, 'Not Assigned') AS delivery_agent,
    COALESCE(dp.phone, 'N/A') AS agent_contact,
    pay.amount,
    pay.payment_status
FROM parcel p
INNER JOIN customer c ON p.customer_id = c.customer_id
INNER JOIN parcel_status ps ON p.parcel_id = ps.parcel_id
LEFT JOIN delivery d ON p.parcel_id = d.parcel_id
LEFT JOIN delivery_person dp ON d.delivery_person_id = dp.delivery_person_id
INNER JOIN payment pay ON p.parcel_id = pay.parcel_id
ORDER BY p.parcel_id ASC;

-- ============================================================================
-- 6. SUBQUERIES (NESTED QUERIES)
-- ============================================================================
-- Query A: Scalar Subquery
-- Find all parcels whose weight is strictly greater than the average weight of all parcels
SELECT
    tracking_id,
    parcel_type,
    weight_kg,
    charge
FROM parcel
WHERE weight_kg > (SELECT AVG(weight_kg) FROM parcel);

-- Query B: Subquery with IN
-- Find all customers who have at least one parcel currently 'Delivered'
SELECT customer_id, full_name, phone, city
FROM customer
WHERE customer_id IN (
    SELECT p.customer_id
    FROM parcel p
    INNER JOIN parcel_status ps ON p.parcel_id = ps.parcel_id
    WHERE ps.status = 'Delivered'
);

-- ============================================================================
-- 7. DATA MODIFICATION QUERIES (UPDATE & DELETE)
-- ============================================================================
-- Update parcel status when delivery progresses
UPDATE parcel_status
SET status = 'Out for Delivery', location = 'Vellore Destination Hub'
WHERE parcel_id = 2;

-- Record payment completion
UPDATE payment
SET payment_status = 'Paid', paid_at = NOW(), payment_method = 'Cash'
WHERE parcel_id = 1;

-- Verify the updates
SELECT ps.parcel_id, p.tracking_id, ps.status, ps.location, pay.payment_status, pay.paid_at
FROM parcel_status ps
INNER JOIN parcel p ON ps.parcel_id = p.parcel_id
INNER JOIN payment pay ON p.parcel_id = pay.parcel_id
WHERE ps.parcel_id IN (1, 2);
