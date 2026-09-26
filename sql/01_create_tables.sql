-- ============================================================================
-- Parcel and Courier Tracking System (PCTS)
-- File: 01_create_tables.sql
-- Description: Creates the database and all 7 relational tables with constraints.
-- Target DBMS: MySQL 8.0+
-- ============================================================================

-- ============================================================================
-- STEP 1: CREATE AND SELECT THE DATABASE
-- ============================================================================
-- A database is a container that holds tables, views, procedures, and triggers.
-- "IF NOT EXISTS" prevents an error if the database was already created earlier.
CREATE DATABASE IF NOT EXISTS pcts_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Switch our active session to use this database.
USE pcts_db;

-- ============================================================================
-- STEP 2: DROP EXISTING TABLES (CLEAN SLATE)
-- ============================================================================
-- Why drop in reverse order?
-- Foreign Key dependencies: A parent table (e.g. `user`) cannot be dropped
-- while child tables (e.g. `customer`) still refer to it.
-- We drop child tables first, then parent tables.
-- ============================================================================
DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS delivery;
DROP TABLE IF EXISTS parcel_status;
DROP TABLE IF EXISTS parcel;
DROP TABLE IF EXISTS delivery_person;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS user;

-- ============================================================================
-- TABLE 1: `user` (Authentication & Core Identity)
-- ============================================================================
-- Role: Stores login credentials and system roles.
-- Concepts taught:
--   - PRIMARY KEY: Uniquely identifies each record. Cannot be NULL.
--   - AUTO_INCREMENT: MySQL automatically assigns 1, 2, 3...
--   - UNIQUE: Ensures no two users can register with the exact same email.
--   - ENUM: Restricts the column value to a specific set of allowed strings.
--   - CURRENT_TIMESTAMP: Automatically records the exact registration time.
-- ============================================================================
CREATE TABLE user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('customer', 'admin', 'delivery') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 2: `customer` (Customer Profile)
-- ============================================================================
-- Role: Holds personal and contact details for customers.
-- Relationship: 1-to-1 with `user` (each customer has one user account).
-- Concepts taught:
--   - FOREIGN KEY: Ensures `user_id` must already exist in the `user` table.
--   - UNIQUE on foreign key: Enforces 1-to-1 relationship.
--   - ON DELETE CASCADE: If the user account is deleted, their customer profile
--     is automatically cleaned up.
-- ============================================================================
CREATE TABLE customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(50),
    CONSTRAINT fk_customer_user
        FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 3: `delivery_person` (Courier Staff Profile)
-- ============================================================================
-- Role: Details of delivery staff assigned to transport parcels.
-- Relationship: 1-to-1 with `user`.
-- Concepts taught:
--   - BOOLEAN (alias for TINYINT(1) in MySQL): Flag for staff availability.
--   - DEFAULT TRUE: By default, a newly registered delivery agent is active.
-- ============================================================================
CREATE TABLE delivery_person (
    delivery_person_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    vehicle_number VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_delivery_person_user
        FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 4: `parcel` (Core Business Entity)
-- ============================================================================
-- Role: Central table representing a shipment booked by a customer.
-- Relationship: Many-to-1 with `customer`.
-- Concepts taught:
--   - tracking_id VARCHAR(20) UNIQUE: Human-readable reference (e.g. PCTS-20240925-0001).
--   - DECIMAL(6,2): Exact fixed-point numeric for weights (up to 9999.99 kg).
--     Never use FLOAT for weights or money because float has precision rounding errors.
--   - DECIMAL(10,2): Exact financial representation for charges (up to 99,999,999.99).
--   - ON DELETE RESTRICT: Prevents deleting a customer if they have active parcels.
-- ============================================================================
CREATE TABLE parcel (
    parcel_id INT AUTO_INCREMENT PRIMARY KEY,
    tracking_id VARCHAR(20) NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    sender_name VARCHAR(100) NOT NULL,
    sender_phone VARCHAR(15) NOT NULL,
    receiver_name VARCHAR(100) NOT NULL,
    receiver_phone VARCHAR(15) NOT NULL,
    source_city VARCHAR(50) NOT NULL,
    destination_city VARCHAR(50) NOT NULL,
    parcel_type VARCHAR(50) NOT NULL,
    weight_kg DECIMAL(6,2) NOT NULL,
    description TEXT,
    charge DECIMAL(10,2) NOT NULL,
    booked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_parcel_customer
        FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 5: `parcel_status` (Current Status Cache)
-- ============================================================================
-- Role: Holds the current/latest status of each parcel for high-speed queries.
-- Note: Audit trail and timeline history are stored in MongoDB.
-- Relationship: 1-to-1 with `parcel`.
-- Concepts taught:
--   - UNIQUE on parcel_id: Guarantees exactly one current status per parcel.
--   - ON UPDATE CURRENT_TIMESTAMP: MySQL automatically refreshes `updated_at`
--     whenever this row is updated.
-- ============================================================================
CREATE TABLE parcel_status (
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    parcel_id INT NOT NULL UNIQUE,
    status VARCHAR(30) NOT NULL,
    location VARCHAR(100),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_status_parcel
        FOREIGN KEY (parcel_id) REFERENCES parcel(parcel_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 6: `delivery` (Delivery Assignment)
-- ============================================================================
-- Role: Maps a parcel to the delivery person responsible for delivering it.
-- Relationship:
--   - 1-to-1 with `parcel` (one active delivery record per parcel).
--   - Many-to-1 with `delivery_person` (one person handles many parcels).
-- Concepts taught:
--   - delivered_at DATETIME NULL: Nullable column. It remains NULL until the parcel
--     is physically delivered.
-- ============================================================================
CREATE TABLE delivery (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    parcel_id INT NOT NULL UNIQUE,
    delivery_person_id INT NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    delivered_at DATETIME NULL,
    CONSTRAINT fk_delivery_parcel
        FOREIGN KEY (parcel_id) REFERENCES parcel(parcel_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_delivery_person
        FOREIGN KEY (delivery_person_id) REFERENCES delivery_person(delivery_person_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 7: `payment` (Payment Records)
-- ============================================================================
-- Role: Tracks billing, payment method, and settlement status for each parcel.
-- Relationship: 1-to-1 with `parcel`.
-- Concepts taught:
--   - ENUM('Pending', 'Paid', 'Failed') with DEFAULT 'Pending': Default state.
--   - paid_at DATETIME NULL: Only populated once payment succeeds.
-- ============================================================================
CREATE TABLE payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    parcel_id INT NOT NULL UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(30),
    payment_status ENUM('Pending', 'Paid', 'Failed') NOT NULL DEFAULT 'Pending',
    paid_at DATETIME NULL,
    CONSTRAINT fk_payment_parcel
        FOREIGN KEY (parcel_id) REFERENCES parcel(parcel_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- VERIFICATION COMMAND
-- ============================================================================
-- List all tables created in the database:
SHOW TABLES;
