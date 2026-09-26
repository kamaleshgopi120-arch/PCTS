-- ============================================================================
-- Parcel and Courier Tracking System (PCTS) — Phase 21: Database Indexing
-- File: sql/05_indexes.sql
-- Description: Creates performance-optimizing B-Tree indexes across relational tables.
-- Target DBMS: MySQL 8.0+
-- ============================================================================

-- ============================================================================
-- EDUCATIONAL THEORY: DATABASE INDEXING
-- ============================================================================
-- What is a Database Index?
-- - An index is an auxiliary data structure (typically a balanced B-Tree) that
--   allows the database engine to find specific rows in O(log N) time instead
--   of scanning every row in the table (O(N) Full Table Scan).
-- - Analogy: Just like the index at the back of a textbook points you directly
--   to the page number of a term without having to read every page of the book.
--
-- When to create an index:
-- 1. Columns frequently used in WHERE conditions (e.g. tracking_id, email, status).
-- 2. Columns used in JOIN conditions (e.g. parcel_id, customer_id).
-- 3. Columns used in ORDER BY or GROUP BY clauses to avoid expensive disk filesorts.
-- 4. High-cardinality columns (columns with many distinct values).
--
-- The Indexing Trade-off (Cost vs Benefit):
-- - Advantage: Tremendously accelerates SELECT read operations.
-- - Disadvantage: Adds slight overhead on INSERT, UPDATE, and DELETE statements
--   because the database engine must keep the B-Tree balanced on every write.
-- - Storage: Indexes occupy additional storage space in the InnoDB tablespace.
--
-- Clustered vs Secondary Indexes in InnoDB:
-- - The PRIMARY KEY is the Clustered Index (data rows are physically ordered by it).
-- - All other indexes are Secondary Indexes (leaf nodes store the Primary Key value).
-- ============================================================================

USE pcts_db;

DELIMITER $$

-- ============================================================================
-- HELPER PROCEDURE: AddIndexIfNotExists
-- Ensures idempotent execution (runs safely multiple times without errors)
-- ============================================================================
DROP PROCEDURE IF EXISTS AddIndexIfNotExists$$
CREATE PROCEDURE AddIndexIfNotExists(
    IN p_table VARCHAR(64),
    IN p_index VARCHAR(64),
    IN p_columns VARCHAR(255)
)
BEGIN
    DECLARE indexCount INT;
    SELECT COUNT(1) INTO indexCount
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = p_table
      AND index_name = p_index;

    IF indexCount = 0 THEN
        SET @sqlStatement = CONCAT('CREATE INDEX ', p_index, ' ON ', p_table, ' (', p_columns, ');');
        PREPARE stmt FROM @sqlStatement;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('CREATED: Index ', p_index, ' on table ', p_table) AS status;
    ELSE
        SELECT CONCAT('EXISTS: Index ', p_index, ' already exists on ', p_table) AS status;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- 1. PARCEL TABLE INDEXES
-- ============================================================================

-- Index 1.1: tracking_id
-- Crucial: Every public tracking request queries WHERE tracking_id = ?
-- Reduces search from full table scan to instant B-Tree index lookup.
CALL AddIndexIfNotExists('parcel', 'idx_parcel_tracking_id', 'tracking_id');

-- Index 1.2: customer_id
-- Crucial: Listing a customer's booked parcels (e.g. GET /api/parcels?customer_id=?)
CALL AddIndexIfNotExists('parcel', 'idx_parcel_customer_id', 'customer_id');

-- Index 1.3: Inter-city Route (source_city, destination_city)
-- Compound Index: Optimizes regional dispatch and transit query grouping.
CALL AddIndexIfNotExists('parcel', 'idx_parcel_route', 'source_city, destination_city');

-- Index 1.4: booked_at
-- Optimizes temporal / date-range filters for monthly and daily revenue reports.
CALL AddIndexIfNotExists('parcel', 'idx_parcel_booked_at', 'booked_at');


-- ============================================================================
-- 2. USER & AUTHENTICATION INDEXES
-- ============================================================================

-- Index 2.1: email
-- Crucial: Every login request executes SELECT * FROM user WHERE email = ?
CALL AddIndexIfNotExists('user', 'idx_user_email', 'email');

-- Index 2.2: role
-- Speeds up filtering users by role (admin, delivery, customer).
CALL AddIndexIfNotExists('user', 'idx_user_role', 'role');


-- ============================================================================
-- 3. CUSTOMER TABLE INDEXES
-- ============================================================================

-- Index 3.1: phone
-- Rapid lookup by mobile number when verifying customer bookings.
CALL AddIndexIfNotExists('customer', 'idx_customer_phone', 'phone');

-- Index 3.2: city
-- Optimizes demographic and city-level dispatch queries.
CALL AddIndexIfNotExists('customer', 'idx_customer_city', 'city');


-- ============================================================================
-- 4. PARCEL STATUS INDEXES
-- ============================================================================

-- Index 4.1: status
-- Speeds up status tab filters in Admin dashboard and pipeline reports.
CALL AddIndexIfNotExists('parcel_status', 'idx_parcel_status_status', 'status');

-- Index 4.2: Compound (status, updated_at)
-- Optimizes active parcel queries ordered by recency.
CALL AddIndexIfNotExists('parcel_status', 'idx_parcel_status_recency', 'status, updated_at');


-- ============================================================================
-- 5. DELIVERY MANAGEMENT INDEXES
-- ============================================================================

-- Index 5.1: Compound (delivery_person_id, assigned_at)
-- Crucial for delivery portal: Speeds up GET /api/deliveries/my ordered by assigned_at DESC.
-- Prevents expensive temporary filesort by providing pre-ordered B-Tree index.
CALL AddIndexIfNotExists('delivery', 'idx_delivery_agent_assigned', 'delivery_person_id, assigned_at');

-- Index 5.2: Compound (delivery_person_id, delivered_at)
-- Optimizes active vs completed task filtering in courier driver workspace.
CALL AddIndexIfNotExists('delivery', 'idx_delivery_agent_completed', 'delivery_person_id, delivered_at');


-- ============================================================================
-- 6. PAYMENT TABLE INDEXES
-- ============================================================================

-- Index 6.1: parcel_id
-- Optimizes relational joins between parcels and financial ledgers.
CALL AddIndexIfNotExists('payment', 'idx_payment_parcel_id', 'parcel_id');

-- Index 6.2: payment_status
-- Speeds up pending payments queries and revenue analytics.
CALL AddIndexIfNotExists('payment', 'idx_payment_status', 'payment_status');


-- ============================================================================
-- VERIFICATION: DISPLAY ALL ACTIVE INDEXES IN PCTS_DB
-- ============================================================================
SELECT
    table_name AS `Table`,
    index_name AS `Index`,
    GROUP_CONCAT(column_name ORDER BY seq_in_index SEPARATOR ', ') AS `Columns`,
    IF(non_unique = 0, 'YES', 'NO') AS `Unique`,
    index_type AS `Type`
FROM information_schema.statistics
WHERE table_schema = DATABASE()
GROUP BY table_name, index_name, non_unique, index_type
ORDER BY table_name, index_name;
