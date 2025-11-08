#!/usr/bin/env python3
"""
Migration Script: Add bar_staff_1 and bar_staff_2 columns to events table

This script adds the missing bar_staff columns to the events table.
Run this script to fix the "no such column: e.bar_staff_1" error.

Usage:
    python migrate_add_bar_staff_columns.py
"""

import sqlite3
import sys
import os

def migrate():
    # Determine database path
    db_path = "db/database.db"

    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at {db_path}")
        print("Please run this script from the db-service directory")
        sys.exit(1)

    print(f"Connecting to database: {db_path}")

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"\nExisting columns in events table: {column_names}")

        # Add bar_staff_1 column if it doesn't exist
        if 'bar_staff_1' not in column_names:
            print("\n[MIGRATION] Adding column: bar_staff_1")
            cursor.execute("ALTER TABLE events ADD COLUMN bar_staff_1 TEXT")
            print("✓ Column bar_staff_1 added successfully")
        else:
            print("\n✓ Column bar_staff_1 already exists")

        # Add bar_staff_2 column if it doesn't exist
        if 'bar_staff_2' not in column_names:
            print("[MIGRATION] Adding column: bar_staff_2")
            cursor.execute("ALTER TABLE events ADD COLUMN bar_staff_2 TEXT")
            print("✓ Column bar_staff_2 added successfully")
        else:
            print("✓ Column bar_staff_2 already exists")

        # Commit changes
        conn.commit()

        # Verify migration
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        print(f"\nFinal columns in events table: {column_names}")

        if 'bar_staff_1' in column_names and 'bar_staff_2' in column_names:
            print("\n✓✓✓ Migration completed successfully! ✓✓✓")
        else:
            print("\n✗✗✗ Migration failed! ✗✗✗")
            sys.exit(1)

        # Close connection
        conn.close()

    except sqlite3.Error as e:
        print(f"\nERROR: Database error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Add bar_staff columns to events table")
    print("=" * 60)
    migrate()
