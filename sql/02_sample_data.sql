-- ============================================================================
-- Parcel and Courier Tracking System (PCTS)
-- File: 02_sample_data.sql
-- Description: Inserts realistic seed data into all 7 tables for testing.
-- Target DBMS: MySQL 8.0+
-- ============================================================================

USE pcts_db;

-- Clear previous data in reverse foreign-key order
DELETE FROM payment;
DELETE FROM delivery;
DELETE FROM parcel_status;
DELETE FROM parcel;
DELETE FROM delivery_person;
DELETE FROM customer;
DELETE FROM user;

-- Reset AUTO_INCREMENT counters to 1
ALTER TABLE user AUTO_INCREMENT = 1;
ALTER TABLE customer AUTO_INCREMENT = 1;
ALTER TABLE delivery_person AUTO_INCREMENT = 1;
ALTER TABLE parcel AUTO_INCREMENT = 1;
ALTER TABLE parcel_status AUTO_INCREMENT = 1;
ALTER TABLE delivery AUTO_INCREMENT = 1;
ALTER TABLE payment AUTO_INCREMENT = 1;

-- ============================================================================
-- 1. INSERT INTO `user`
-- ============================================================================
-- Passwords are dummy bcrypt/argon2 hashes for now. In Phase 8, we will
-- hash them using passlib/bcrypt in Python.
-- ============================================================================
INSERT INTO user (user_id, email, password_hash, role) VALUES
(1, 'admin@pcts.com', '$2b$12$JsjFyi3fAYV2rWbUulSlgeDgeiHK8YDVkj02cpmHkEy3pTDV5It1.', 'admin'),
(2, 'arun.kumar@gmail.com', '$2b$12$LxTSuBeDYUZ4mINzLKAfGuyOp5CUCSKdo1vwmYjYVg6vKJqRxXkgW', 'customer'),
(3, 'priya.sharma@yahoo.com', '$2b$12$Rz28iA7Akv0CloVr3rtAOu7enbiw3s6whNpfHB5vK9dzfkQ/xK/ry', 'customer'),
(4, 'ravi.delivery@pcts.com', '$2b$12$BYQoQrYpfh.ZzWBF7PrQUuyZxRN.YIR1t0Yp57xX3yfuvgLT1Ewn6', 'delivery');

-- ============================================================================
-- 2. INSERT INTO `customer`
-- ============================================================================
-- Arun Kumar (user_id 2) and Priya Sharma (user_id 3)
-- ============================================================================
INSERT INTO customer (customer_id, user_id, full_name, phone, address, city) VALUES
(1, 2, 'Arun Kumar', '9876543210', '12, 4th Main Road, Anna Nagar', 'Chennai'),
(2, 3, 'Priya Sharma', '9876543222', '45, Palm Avenue, Whitefield', 'Bengaluru');

-- ============================================================================
-- 3. INSERT INTO `delivery_person`
-- ============================================================================
-- Ravi Varma (user_id 4)
-- ============================================================================
INSERT INTO delivery_person (delivery_person_id, user_id, full_name, phone, vehicle_number, is_active) VALUES
(1, 4, 'Ravi Varma', '9876543333', 'TN-01-AB-1234', TRUE);

-- ============================================================================
-- 4. INSERT INTO `parcel`
-- ============================================================================
-- Pricing Rule Breakdown:
--   - 0.80 kg  (<= 1kg):   Rs. 50 flat               = Rs. 50.00
--   - 2.50 kg  (1.01-5kg): 2.50 kg * Rs. 30/kg       = Rs. 75.00
--   - 8.00 kg  (5.01-20kg):8.00 kg * Rs. 20/kg       = Rs. 160.00
--   - 25.00 kg (> 20kg):   25.00 kg * Rs. 15/kg      = Rs. 375.00
--   - 1.50 kg  (1.01-5kg): 1.50 kg * Rs. 30/kg       = Rs. 45.00
-- ============================================================================
INSERT INTO parcel (
    parcel_id, tracking_id, customer_id, sender_name, sender_phone,
    receiver_name, receiver_phone, source_city, destination_city,
    parcel_type, weight_kg, description, charge, booked_at
) VALUES
(
    1, 'PCTS-20240925-0001', 1,
    'Arun Kumar', '9876543210', 'Kavita Nair', '9876540001',
    'Chennai', 'Bengaluru', 'Document', 0.80,
    'University Degree Certificates and Transcripts', 50.00, '2024-09-25 09:15:00'
),
(
    2, 'PCTS-20240925-0002', 1,
    'Arun Kumar', '9876543210', 'Suresh Babu', '9876540002',
    'Chennai', 'Puducherry', 'Electronics', 2.50,
    'Wireless Headphones and Tablet Charger', 75.00, '2024-09-25 10:30:00'
),
(
    3, 'PCTS-20240925-0003', 2,
    'Priya Sharma', '9876543222', 'Deepak Verma', '9876540003',
    'Bengaluru', 'Chennai', 'Fragile', 8.00,
    'Handmade Ceramic Dinner Set - Handle with Care', 160.00, '2024-09-25 11:45:00'
),
(
    4, 'PCTS-20240925-0004', 2,
    'Priya Sharma', '9876543222', 'Ananya Sen', '9876540004',
    'Bengaluru', 'Hyderabad', 'General', 25.00,
    'Carton of Reference Textbooks and Journals', 375.00, '2024-09-25 14:00:00'
),
(
    5, 'PCTS-20240925-0005', 1,
    'Arun Kumar', '9876543210', 'Manoj Krishnan', '9876540005',
    'Chennai', 'Madurai', 'Clothing', 1.50,
    'Festive Silk Sarees Gift Package', 45.00, '2024-09-25 16:20:00'
);

-- ============================================================================
-- 5. INSERT INTO `parcel_status` (Current Status for each parcel)
-- ============================================================================
INSERT INTO parcel_status (status_id, parcel_id, status, location, updated_at) VALUES
(1, 1, 'Booked', 'Chennai Central Booking Office', '2024-09-25 09:15:00'),
(2, 2, 'In Transit', 'Vellore Highway Sorting Hub', '2024-09-25 14:40:00'),
(3, 3, 'Out for Delivery', 'Chennai South Delivery Depot', '2024-09-26 08:30:00'),
(4, 4, 'Delivered', 'Hyderabad Banjara Hills Hub', '2024-09-26 11:15:00'),
(5, 5, 'Booked', 'Chennai Central Booking Office', '2024-09-25 16:20:00');

-- ============================================================================
-- 6. INSERT INTO `delivery` (Courier Assignments)
-- ============================================================================
-- Ravi Varma (delivery_person_id 1) handles:
--   - Parcel 3 (currently Out for Delivery, not delivered yet -> delivered_at is NULL)
--   - Parcel 4 (successfully Delivered -> delivered_at is populated)
-- ============================================================================
INSERT INTO delivery (delivery_id, parcel_id, delivery_person_id, assigned_at, delivered_at) VALUES
(1, 3, 1, '2024-09-26 08:00:00', NULL),
(2, 4, 1, '2024-09-26 07:30:00', '2024-09-26 11:15:00');

-- ============================================================================
-- 7. INSERT INTO `payment` (Billing and Settlement Records)
-- ============================================================================
INSERT INTO payment (payment_id, parcel_id, amount, payment_method, payment_status, paid_at) VALUES
(1, 1, 50.00, 'Cash', 'Pending', NULL),
(2, 2, 75.00, 'UPI', 'Paid', '2024-09-25 10:32:00'),
(3, 3, 160.00, 'Credit Card', 'Paid', '2024-09-25 11:47:00'),
(4, 4, 375.00, 'Net Banking', 'Paid', '2024-09-25 14:05:00'),
(5, 5, 45.00, 'UPI', 'Failed', NULL);

-- ============================================================================
-- SUMMARY VERIFICATION
-- ============================================================================
SELECT 'user' AS table_name, COUNT(*) AS row_count FROM user
UNION ALL
SELECT 'customer', COUNT(*) FROM customer
UNION ALL
SELECT 'delivery_person', COUNT(*) FROM delivery_person
UNION ALL
SELECT 'parcel', COUNT(*) FROM parcel
UNION ALL
SELECT 'parcel_status', COUNT(*) FROM parcel_status
UNION ALL
SELECT 'delivery', COUNT(*) FROM delivery
UNION ALL
SELECT 'payment', COUNT(*) FROM payment;
