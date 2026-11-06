-- ============================================================================
-- Parcel and Courier Tracking System (PCTS)
-- File: procedures.sql
-- Description: PL/SQL components (Stored Procedures, Stored Functions, Triggers)
-- Target DBMS: MySQL 8.0+
-- ============================================================================

USE pcts_db;

-- ============================================================================
-- BACKGROUND & CORE CONCEPTS FOR STUDENTS
-- ============================================================================
-- 1. What is a Stored Function?
--    A named program stored inside the database that takes input parameters,
--    performs calculations, and RETURNS A SINGLE VALUE.
--    Functions can be called directly inside SQL queries (e.g. SELECT calculate_charge(3.5)).
--
-- 2. What is a Stored Procedure?
--    A collection of SQL statements grouped together to perform complex business
--    logic (like updates across multiple tables). It is invoked using the CALL keyword.
--
-- 3. What is a Trigger?
--    A special database program that FIRES AUTOMATICALLY in response to an
--    event (INSERT, UPDATE, or DELETE) on a specific table.
--
-- 4. Why DELIMITER //?
--    By default, MySQL treats semicolon (;) as the end of a command.
--    Because our procedure bodies contain multiple semicolons, we temporarily change
--    the delimiter to // so MySQL reads the whole BEGIN ... END block as one unit.
-- ============================================================================


-- ============================================================================
-- STEP 1: AUDIT LOG TABLE FOR TRIGGER
-- ============================================================================
-- To demonstrate triggers, we need a table where changes are automatically logged.
-- Whenever `parcel_status` changes, our trigger will write a record here.
-- ============================================================================
CREATE TABLE IF NOT EXISTS parcel_status_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    parcel_id INT NOT NULL,
    old_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    old_location VARCHAR(100),
    new_location VARCHAR(100),
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(50) DEFAULT 'SYSTEM',
    CONSTRAINT fk_audit_parcel
        FOREIGN KEY (parcel_id) REFERENCES parcel(parcel_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


-- ============================================================================
-- COMPONENT 1: STORED FUNCTION `calculate_charge`
-- ============================================================================
-- Requirement:
--   Weight <= 1.00 kg:      Rs. 50.00 flat
--   1.01 kg to 5.00 kg:     Rs. 30.00 per kg
--   5.01 kg to 20.00 kg:    Rs. 20.00 per kg
--   Above 20.00 kg:         Rs. 15.00 per kg
--
-- DETERMINISTIC: Always returns the exact same result for the exact same input.
-- NO SQL: Does not query or modify any tables; purely computational.
-- ============================================================================
DROP FUNCTION IF EXISTS calculate_charge;

DELIMITER //

CREATE FUNCTION calculate_charge(p_weight DECIMAL(6,2))
RETURNS DECIMAL(10,2)
DETERMINISTIC
NO SQL
BEGIN
    DECLARE v_charge DECIMAL(10,2);

    -- Edge case: Negative or zero weight
    IF p_weight IS NULL OR p_weight <= 0.00 THEN
        SET v_charge = 0.00;

    -- Tier 1: 0 to 1 kg (Flat rate)
    ELSEIF p_weight <= 1.00 THEN
        SET v_charge = 50.00;

    -- Tier 2: 1.01 to 5.00 kg (Rs. 30 per kg)
    ELSEIF p_weight <= 5.00 THEN
        SET v_charge = ROUND(p_weight * 30.00, 2);

    -- Tier 3: 5.01 to 20.00 kg (Rs. 20 per kg)
    ELSEIF p_weight <= 20.00 THEN
        SET v_charge = ROUND(p_weight * 20.00, 2);

    -- Tier 4: Above 20 kg (Rs. 15 per kg)
    ELSE
        SET v_charge = ROUND(p_weight * 15.00, 2);
    END IF;

    RETURN v_charge;
END //

DELIMITER ;


-- ============================================================================
-- COMPONENT 2: TRIGGER `trg_after_status_update`
-- ============================================================================
-- Fires AFTER an UPDATE on the `parcel_status` table.
-- Concepts taught:
--   - `OLD`: Refers to the row values BEFORE the update.
--   - `NEW`: Refers to the row values AFTER the update.
--   - Automates data auditing without relying on application code to remember!
-- ============================================================================
DROP TRIGGER IF EXISTS trg_after_status_update;

DELIMITER //

CREATE TRIGGER trg_after_status_update
AFTER UPDATE ON parcel_status
FOR EACH ROW
BEGIN
    -- Only log if status or location actually changed
    IF (OLD.status <> NEW.status) OR (OLD.location <> NEW.location) OR (OLD.location IS NULL AND NEW.location IS NOT NULL) THEN
        INSERT INTO parcel_status_audit (
            parcel_id,
            old_status,
            new_status,
            old_location,
            new_location,
            changed_at,
            changed_by
        ) VALUES (
            NEW.parcel_id,
            OLD.status,
            NEW.status,
            OLD.location,
            NEW.location,
            NOW(),
            CURRENT_USER()
        );
    END IF;
END //

DELIMITER ;


-- ============================================================================
-- COMPONENT 3: STORED PROCEDURE `update_parcel_status`
-- ============================================================================
-- Updates a parcel's status and location by its human-readable `tracking_id`.
-- Also updates `delivery.delivered_at = NOW()` when status becomes 'Delivered'.
-- Uses transactions with error handling.
-- ============================================================================
DROP PROCEDURE IF EXISTS update_parcel_status;

DELIMITER //

CREATE PROCEDURE update_parcel_status(
    IN p_tracking_id VARCHAR(20),
    IN p_new_status VARCHAR(30),
    IN p_location VARCHAR(100),
    OUT p_rows_affected INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_parcel_id INT DEFAULT NULL;
    DECLARE v_current_status VARCHAR(30) DEFAULT NULL;
    DECLARE v_transition_allowed BOOLEAN DEFAULT FALSE;

    -- Exit handler for unexpected SQL exceptions
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_rows_affected = 0;
        SET p_message = 'ERROR: Database error occurred while updating status.';
    END;

    START TRANSACTION;

    -- 1. Lock the parcel and current status while validating the transition.
    SELECT parcel_id INTO v_parcel_id
    FROM parcel
    WHERE tracking_id = p_tracking_id
    FOR UPDATE;

    -- 2. Validate that the parcel exists
    IF v_parcel_id IS NULL THEN
        ROLLBACK;
        SET p_rows_affected = 0;
        SET p_message = CONCAT('ERROR: Parcel with tracking ID ', p_tracking_id, ' not found.');
    ELSE
        SELECT status INTO v_current_status
        FROM parcel_status
        WHERE parcel_id = v_parcel_id
        FOR UPDATE;

        IF v_current_status IS NULL THEN
            ROLLBACK;
            SET p_rows_affected = 0;
            SET p_message = 'ERROR: Parcel has no current status record.';
        ELSEIF p_new_status IS NULL OR p_new_status NOT IN (
            'Booked', 'Picked Up', 'In Transit', 'At Warehouse',
            'Out for Delivery', 'Delivered', 'Failed Delivery', 'Returned'
        ) THEN
            ROLLBACK;
            SET p_rows_affected = 0;
            SET p_message = 'ERROR: Invalid parcel status.';
        ELSEIF p_location IS NULL OR CHAR_LENGTH(TRIM(p_location)) < 2 THEN
            ROLLBACK;
            SET p_rows_affected = 0;
            SET p_message = 'ERROR: A valid location is required.';
        ELSE
            SET v_transition_allowed = CASE
                WHEN v_current_status = 'Booked' AND p_new_status = 'Picked Up' THEN TRUE
                WHEN v_current_status = 'Picked Up' AND p_new_status = 'In Transit' THEN TRUE
                WHEN v_current_status = 'In Transit' AND p_new_status = 'At Warehouse' THEN TRUE
                WHEN v_current_status = 'At Warehouse' AND p_new_status = 'Out for Delivery' THEN TRUE
                WHEN v_current_status = 'Out for Delivery' AND p_new_status IN ('Delivered', 'Failed Delivery') THEN TRUE
                WHEN v_current_status = 'Failed Delivery' AND p_new_status = 'Returned' THEN TRUE
                ELSE FALSE
            END;

            IF NOT v_transition_allowed THEN
                ROLLBACK;
                SET p_rows_affected = 0;
                SET p_message = CONCAT(
                    'ERROR: Invalid status transition from ',
                    v_current_status,
                    ' to ',
                    p_new_status,
                    '.'
                );
            ELSE
                -- Updating parcel_status fires `trg_after_status_update`.
                UPDATE parcel_status
                SET status = p_new_status,
                    location = p_location,
                    updated_at = NOW()
                WHERE parcel_id = v_parcel_id;

                IF p_new_status = 'Delivered' THEN
                    UPDATE delivery
                    SET delivered_at = NOW()
                    WHERE parcel_id = v_parcel_id AND delivered_at IS NULL;
                END IF;

                COMMIT;
                SET p_rows_affected = 1;
                SET p_message = CONCAT('SUCCESS: Status of ', p_tracking_id, ' updated to ', p_new_status);
            END IF;
        END IF;
    END IF;
END //

DELIMITER ;


-- ============================================================================
-- COMPONENT 4: STORED PROCEDURE `get_monthly_report`
-- ============================================================================
-- Generates an executive summary for a given month and year:
-- 1. Total parcels booked in that month.
-- 2. Total revenue generated in that month.
-- 3. Average parcel weight in kg.
-- 4. Breakdown of parcels grouped by current status.
-- ============================================================================
DROP PROCEDURE IF EXISTS get_monthly_report;

DELIMITER //

CREATE PROCEDURE get_monthly_report(
    IN p_year INT,
    IN p_month INT
)
BEGIN
    -- Result Set 1: High-Level Overview Metrics
    SELECT
        p_year AS report_year,
        p_month AS report_month,
        COUNT(p.parcel_id) AS total_parcels_booked,
        COALESCE(SUM(p.charge), 0.00) AS total_revenue,
        COALESCE(ROUND(AVG(p.weight_kg), 2), 0.00) AS average_weight_kg
    FROM parcel p
    WHERE YEAR(p.booked_at) = p_year AND MONTH(p.booked_at) = p_month;

    -- Result Set 2: Breakdown by Status
    SELECT
        ps.status AS parcel_status,
        COUNT(*) AS count_in_status,
        ROUND(COALESCE(SUM(p.charge), 0), 2) AS revenue_for_status
    FROM parcel p
    INNER JOIN parcel_status ps ON p.parcel_id = ps.parcel_id
    WHERE YEAR(p.booked_at) = p_year AND MONTH(p.booked_at) = p_month
    GROUP BY ps.status
    ORDER BY count_in_status DESC;

    -- Result Set 3: Breakdown by Destination City
    SELECT
        p.destination_city,
        COUNT(*) AS parcel_count,
        ROUND(SUM(p.charge), 2) AS city_revenue
    FROM parcel p
    WHERE YEAR(p.booked_at) = p_year AND MONTH(p.booked_at) = p_month
    GROUP BY p.destination_city
    ORDER BY parcel_count DESC;
END //

DELIMITER ;


-- ============================================================================
-- VERIFICATION & SELF-TEST QUERIES
-- ============================================================================

-- Test 1: Verify calculate_charge across all 4 weight tiers
SELECT
    0.80 AS weight, calculate_charge(0.80) AS charge_tier1,
    3.50 AS weight, calculate_charge(3.50) AS charge_tier2,
    12.00 AS weight, calculate_charge(12.00) AS charge_tier3,
    25.00 AS weight, calculate_charge(25.00) AS charge_tier4;

-- Test 2: Call update_parcel_status procedure
CALL update_parcel_status(
    'PCTS-20240925-0002',
    'Out for Delivery',
    'Puducherry Central Depot',
    @affected,
    @msg
);
SELECT @affected AS affected_rows, @msg AS output_message;

-- Test 3: Check if Trigger logged the change into parcel_status_audit
SELECT * FROM parcel_status_audit ORDER BY audit_id DESC LIMIT 5;

-- Test 4: Call get_monthly_report for September 2024
CALL get_monthly_report(2024, 9);
