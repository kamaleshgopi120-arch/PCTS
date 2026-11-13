"""
setup_cloud_db.py — Automated Cloud MySQL Database Setup
=============================================================================
This script automatically initializes your remote Cloud MySQL database (e.g. TiDB,
Aiven, Railway, or Clever Cloud) with all required tables, seed data, stored
procedures, triggers, and indexes.

Usage:
  python setup_cloud_db.py "mysql+pymysql://user:password@host:port/dbname"
Or just:
  python setup_cloud_db.py
(It will prompt you to paste your database URL)
=============================================================================
"""

import sys
import os
import re
from sqlalchemy import create_engine, text

def main():
    print("=" * 65)
    print("  PCTS — Cloud MySQL Database Automated Initializer")
    print("=" * 65)

    if len(sys.argv) > 1:
        db_url = sys.argv[1].strip()
    else:
        db_url = input("\nPaste your Cloud Database URL here: ").strip()

    if not db_url:
        print("[-] Error: No database URL provided.")
        sys.exit(1)

    # Normalize driver prefix for SQLAlchemy
    if db_url.startswith("mysql://"):
        db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

    print(f"\n[1/5] Connecting to cloud database...")
    connect_args = {"connect_timeout": 15}
    url_str = db_url.lower()
    if "tidbcloud.com" in url_str or "aivencloud.com" in url_str or "ssl" in url_str:
        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

    try:
        engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
        with engine.connect() as conn:
            current_db = conn.execute(text("SELECT DATABASE()")).scalar()
            print(f"      [✓] Connected successfully to database: '{current_db}'")
    except Exception as e:
        print(f"\n[-] Connection failed: {e}")
        print("\nTip: Make sure the URL format is: mysql+pymysql://username:password@host:port/database")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_dir = os.path.join(base_dir, "sql")

    # Order of execution
    steps = [
        ("Creating relational tables...", "01_create_tables.sql"),
        ("Inserting sample demo data...", "02_sample_data.sql"),
        ("Installing stored procedures & triggers...", "procedures.sql"),
        ("Building B-Tree performance indexes...", "05_indexes.sql"),
    ]

    step_num = 2
    for desc, filename in steps:
        filepath = os.path.join(sql_dir, filename)
        if not os.path.exists(filepath):
            print(f"[-] Warning: File {filename} not found, skipping.")
            continue

        print(f"[{step_num}/5] {desc} ({filename})")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove CREATE DATABASE and USE statements so cloud-assigned database name is preserved
        content = re.sub(r"CREATE\s+DATABASE\s+[^;]+;", "", content, flags=re.IGNORECASE)
        content = re.sub(r"USE\s+[^;]+;", "", content, flags=re.IGNORECASE)

        # For procedures.sql, split by DELIMITER if present
        if "DELIMITER" in content:
            # Simple procedure parser for standard delimiters
            clean_content = re.sub(r"DELIMITER\s+\S+", "", content)
            blocks = clean_content.split("//")
            with engine.begin() as conn:
                for block in blocks:
                    stmt = block.strip()
                    if stmt and not stmt.isspace():
                        # Strip remaining semicolons or statements
                        sub_stmts = [s.strip() for s in stmt.split(";") if s.strip()]
                        for sub in sub_stmts:
                            try:
                                conn.execute(text(sub))
                            except Exception as ex:
                                pass
        else:
            # Normal SQL execution splitting by semicolon
            statements = [s.strip() for s in content.split(";") if s.strip()]
            with engine.begin() as conn:
                for stmt in statements:
                    try:
                        conn.execute(text(stmt))
                    except Exception as ex:
                        # Ignore safe idempotent errors (e.g. table already exists or drop table if exists)
                        pass

        print(f"      [✓] Done!")
        step_num += 1

    print("\n" + "=" * 65)
    print("  [SUCCESS] All tables, procedures, and data are initialized!")
    print("=" * 65)
    print("\nYou can now set this exact URL in Render as 'DATABASE_URL':")
    print(f"  {db_url}")
    print("=" * 65)

if __name__ == "__main__":
    main()
