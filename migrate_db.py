#!/usr/bin/env python
"""
Database migration script.

Handles:
- Creating new tables
- Renaming reset_token column to reset_token_hash (if upgrading from old schema)
"""
import sqlite3
import os
from app import create_app, db

SQLITE_PATH = os.path.join('instance', 'threats.db')


def migrate_sqlite_columns():
    """Handle SQLite-specific column migrations (SQLite doesn't support ALTER COLUMN)."""
    if not os.path.exists(SQLITE_PATH):
        return

    conn = sqlite3.connect(SQLITE_PATH)
    cursor = conn.cursor()

    # Check if old 'reset_token' column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}

    if 'reset_token' in columns and 'reset_token_hash' not in columns:
        print('Migrating: renaming reset_token → reset_token_hash...')
        # SQLite doesn't support RENAME COLUMN before 3.25.0, so we recreate
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(120) NOT NULL UNIQUE,
                password_hash VARCHAR(256) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                created_at DATETIME,
                reset_token_hash VARCHAR(256),
                reset_token_expiry DATETIME
            )
        """)
        cursor.execute("""
            INSERT INTO users_new (id, username, email, password_hash, role, created_at, reset_token_hash, reset_token_expiry)
            SELECT id, username, email, password_hash, role, created_at, NULL, reset_token_expiry
            FROM users
        """)
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        conn.commit()
        print('  Done. Old reset tokens cleared (users will need to request new ones).')

    conn.close()


if __name__ == '__main__':
    print('=' * 50)
    print('Database Migration')
    print('=' * 50)

    # First handle SQLite-specific migrations
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///threats.db')
    if 'sqlite' in database_url:
        migrate_sqlite_columns()

    # Then create/update all tables via SQLAlchemy
    app = create_app()
    with app.app_context():
        db.create_all()
        print('Database tables created/updated successfully.')
