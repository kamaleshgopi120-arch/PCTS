-- Run once against an existing PCTS database before starting the updated app.
-- New installations already create this column in sql/01_create_tables.sql.
ALTER TABLE parcel
    ADD COLUMN receiver_address VARCHAR(255) NULL AFTER receiver_phone;
