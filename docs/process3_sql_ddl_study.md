# Process 3: Study About SQL and DDL (Data Definition Language)
## Parcel and Courier Tracking System (PCTS) — DBMS Lab Study Guide

---

## 1. Introduction to SQL and DDL

### 1.1 What is SQL?
**SQL (Structured Query Language)** is the standard programming language used to interact with Relational Database Management Systems (RDBMS) like MySQL, PostgreSQL, and Oracle. SQL allows users to define database schemas, store and manipulate data, query datasets, and control system security.

### 1.2 Five Sub-Languages of SQL

| Category | Full Name | Commands | Primary Purpose |
|---|---|---|---|
| **DDL** | Data Definition Language | `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `RENAME` | Defines and modifies the structure of database objects (databases, tables, constraints, indexes). |
| **DML** | Data Manipulation Language | `INSERT`, `UPDATE`, `DELETE` | Manipulates data stored within existing relational tables. |
| **DQL** | Data Query Language | `SELECT` | Retrieves data matching specific conditions without modifying database state. |
| **DCL** | Data Control Language | `GRANT`, `REVOKE` | Manages permissions and user access rights. |
| **TCL** | Transaction Control Language | `COMMIT`, `ROLLBACK`, `SAVEPOINT` | Manages atomic transactions and database state consistency. |

---

## 2. Key Characteristics of DDL in MySQL

1. **Implicit Auto-Commit:** In MySQL (and standard RDBMS), executing a DDL command immediately terminates any active transaction and permanently commits all preceding changes. **DDL operations cannot be rolled back** using `ROLLBACK`.
2. **Metadata Modification:** DDL updates the internal MySQL system catalogs (e.g., `information_schema`).
3. **Storage Engine Integration:** DDL configures how physical data is stored on disk (e.g., `ENGINE=InnoDB` handles ACID compliance, row-level locking, and foreign key integrity).

---

## 3. Core DDL Commands Applied to PCTS

---

### Command 1: `CREATE DATABASE`

#### Explanation:
A **Database** (or Schema) is a logical namespace and storage container that encapsulates related tables, views, stored procedures, triggers, and indexes.

#### Syntax:
```sql
CREATE DATABASE [IF NOT EXISTS] database_name
    [CHARACTER SET charset_name]
    [COLLATE collation_name];
```

#### PCTS Implementation:
```sql
-- 1. Create the database with UTF-8 character encoding
CREATE DATABASE IF NOT EXISTS pcts_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 2. Select the database for active session usage
USE pcts_db;
```

#### Technical Notes:
- `IF NOT EXISTS`: Idempotent guard condition preventing errors if the database is already initialized.
- `utf8mb4`: Standard 4-byte UTF-8 encoding capable of storing all international character sets, symbols, and emojis.
- `utf8mb4_unicode_ci`: Case-insensitive collation following Unicode sorting algorithms.

---

### Command 2: `CREATE TABLE`

#### Explanation:
The `CREATE TABLE` statement defines a relational table by specifying column names, data types, default values, and column/table-level integrity constraints.

#### Key Constraints in DDL:
- `PRIMARY KEY`: Uniquely identifies each record. Automatically enforces `UNIQUE` and `NOT NULL`.
- `AUTO_INCREMENT`: Automatically assigns monotonically increasing integer keys (1, 2, 3...).
- `NOT NULL`: Rejects missing or null values for required attributes.
- `UNIQUE`: Prohibits duplicate values in a column or composite set of columns.
- `DEFAULT`: Supplies a fallback value when none is explicitly provided during insertion.
- `CHECK`: Validates that column data satisfies a boolean expression (e.g., `weight > 0`).
- `FOREIGN KEY`: Establishes referential integrity between child and parent tables:
  - `ON DELETE CASCADE`: Deletes child rows automatically when the parent row is deleted.
  - `ON UPDATE CASCADE`: Propagates primary key changes from parent to child rows.

#### Real Schema Examples from PCTS:

#### 1. The `user` Table (Identity & Authentication):
```sql
CREATE TABLE user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('customer', 'admin', 'delivery') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
```

#### 2. The `customer` Table (1-to-1 Profile Extension):
```sql
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
```

#### 3. The `parcel` Table (Core Entity with Referential Links):
```sql
CREATE TABLE parcel (
    parcel_id INT AUTO_INCREMENT PRIMARY KEY,
    tracking_id VARCHAR(30) NOT NULL UNIQUE,
    sender_id INT NOT NULL,
    receiver_name VARCHAR(100) NOT NULL,
    receiver_phone VARCHAR(15) NOT NULL,
    receiver_address VARCHAR(255) NOT NULL,
    source_city VARCHAR(50) NOT NULL,
    destination_city VARCHAR(50) NOT NULL,
    weight DECIMAL(6, 2) NOT NULL,
    category ENUM('Standard', 'Express', 'Fragile', 'Document') DEFAULT 'Standard',
    shipping_cost DECIMAL(10, 2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_parcel_sender
        FOREIGN KEY (sender_id) REFERENCES customer(customer_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT chk_parcel_weight
        CHECK (weight > 0.00)
) ENGINE=InnoDB;
```

---

### Command 3: `ALTER TABLE`

#### Explanation:
The `ALTER TABLE` command modifies the structure of an existing relational table without deleting or recreating the table, thereby preserving existing records.

#### Operations supported:
1. Adding new columns (`ADD COLUMN`)
2. Modifying column datatypes or constraints (`MODIFY COLUMN`)
3. Renaming columns (`RENAME COLUMN` or `CHANGE COLUMN`)
4. Dropping existing columns (`DROP COLUMN`)
5. Adding/dropping constraints and indexes (`ADD CONSTRAINT`, `DROP CONSTRAINT`)

#### Practical PCTS Demonstrations:

```sql
-- 1. ADD a new column: Add alternate contact number to customer table
ALTER TABLE customer
    ADD COLUMN alternate_phone VARCHAR(15) NULL AFTER phone;

-- 2. ADD a new column with DEFAULT: Add customer loyalty discount tier
ALTER TABLE customer
    ADD COLUMN loyalty_tier ENUM('Bronze', 'Silver', 'Gold') DEFAULT 'Bronze';

-- 3. MODIFY an existing column: Increase recipient address length from 255 to 500 characters
ALTER TABLE parcel
    MODIFY COLUMN receiver_address VARCHAR(500) NOT NULL;

-- 4. ADD a CHECK constraint: Ensure shipping costs cannot be negative or zero
ALTER TABLE parcel
    ADD CONSTRAINT chk_shipping_cost_positive
    CHECK (shipping_cost > 0.00);

-- 5. ADD an INDEX via DDL: Optimize search performance on source and destination cities
ALTER TABLE parcel
    ADD INDEX idx_parcel_route (source_city, destination_city);

-- 6. DROP an INDEX via DDL:
ALTER TABLE parcel
    DROP INDEX idx_parcel_route;

-- 7. RENAME a column: Rename 'address' to 'street_address'
ALTER TABLE customer
    RENAME COLUMN address TO street_address;

-- 8. DROP a column safely: Remove the loyalty_tier column
ALTER TABLE customer
    DROP COLUMN loyalty_tier;
```

---

### Command 4: `DROP TABLE` & `DROP DATABASE`

#### Explanation:
The `DROP TABLE` command permanently deletes a table's schema definition, all contained rows, constraints, triggers, and secondary indexes from disk.

#### Critical Concept: Foreign Key Dependency Order
In an RDBMS, relational tables form a **Directed Acyclic Graph (DAG)** of parent-child foreign key dependencies:
```
       user
      ┌──┴──┐
      ▼     ▼
  customer  delivery_person
      │           │
      ▼           ▼
   parcel ────> delivery
   ┌──┴──┐
   ▼     ▼
status payment
```
- **Rule:** A parent table cannot be dropped while active child foreign keys reference it.
- **Dropping Order:** Always drop child tables first, moving upward to parent tables:

```sql
-- Safe Dropping Sequence for PCTS:
DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS delivery;
DROP TABLE IF EXISTS parcel_status;
DROP TABLE IF EXISTS parcel;
DROP TABLE IF EXISTS delivery_person;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS user;
```

#### Dropping the Database:
```sql
-- Permanently deletes the database and all enclosed objects
DROP DATABASE IF EXISTS pcts_db;
```

---

## 4. DDL vs DML Comparison Matrix

| Feature | DDL (`CREATE`, `ALTER`, `DROP`, `TRUNCATE`) | DML (`INSERT`, `UPDATE`, `DELETE`) |
|---|---|---|
| **Target** | Database schema and structure | Table records / row data |
| **Transaction Rollback** | Cannot be rolled back (Implicit Auto-Commit) | Can be rolled back via `ROLLBACK` |
| **Locks Acquired** | Exclusive Table / Metadata Lock (MDL) | Row-level locks in InnoDB |
| **Triggers** | Does not fire DML triggers | Fires row-level `BEFORE` / `AFTER` triggers |
| **Resource Cost** | Minimal I/O, updates metadata | Proportional to number of rows modified |

---

## 5. Summary of Schema Verification Commands

After executing DDL statements, verify database objects using these commands:

| Command | Output / Purpose |
|---|---|
| `SHOW DATABASES;` | Lists all databases on the MySQL server instance. |
| `USE pcts_db;` | Switches session to the PCTS database. |
| `SHOW TABLES;` | Lists all 7 relational tables in `pcts_db`. |
| `DESCRIBE parcel;` | Shows column names, datatypes, nullability, keys, and default values. |
| `SHOW CREATE TABLE parcel;` | Displays the exact DDL statement used to construct the table, including foreign keys. |
| `SHOW INDEX FROM parcel;` | Displays all primary and secondary B-Tree indexes created on the table. |
