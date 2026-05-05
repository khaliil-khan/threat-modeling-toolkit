#!/usr/bin/env python
"""
Migrate data from SQLite to PostgreSQL.

Usage:
    python migrate_to_postgres.py

Requires DATABASE_URL env var pointing to your PostgreSQL instance.
Will read from the local SQLite database (instance/threats.db) and
write all data to the PostgreSQL database.

Example:
    export DATABASE_URL="postgresql://threats_user:threats_pass@localhost:5432/threats_db"
    python migrate_to_postgres.py
"""
import os
import sys
import sqlite3
from datetime import datetime

# Ensure DATABASE_URL is set
pg_url = os.environ.get('DATABASE_URL')
if not pg_url or 'postgresql' not in pg_url:
    print('ERROR: Set DATABASE_URL to your PostgreSQL connection string.')
    print('Example: export DATABASE_URL="postgresql://user:pass@host:5432/dbname"')
    sys.exit(1)

SQLITE_PATH = os.path.join('instance', 'threats.db')
if not os.path.exists(SQLITE_PATH):
    print(f'ERROR: SQLite database not found at {SQLITE_PATH}')
    sys.exit(1)

# Set the DATABASE_URL so the Flask app connects to PostgreSQL
os.environ['DATABASE_URL'] = pg_url
os.environ['APP_ENV'] = 'production'
os.environ.setdefault('SECRET_KEY', 'migration-temp-key')

from app import create_app, db
from app.models import User, ThreatModel, Threat, DFDData

def migrate():
    """Transfer all data from SQLite to PostgreSQL."""
    app = create_app()

    # Connect to SQLite source
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    with app.app_context():
        # Create all tables in PostgreSQL
        db.create_all()
        print('PostgreSQL tables created.')

        cursor = sqlite_conn.cursor()

        # --- Migrate Users ---
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        user_count = 0
        for row in users:
            existing = User.query.filter_by(username=row['username']).first()
            if existing:
                continue
            user = User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                password_hash=row['password_hash'],
                role=row['role'] if 'role' in row.keys() else 'user',
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
            )
            db.session.add(user)
            user_count += 1
        db.session.commit()
        print(f'  Migrated {user_count} users.')

        # --- Migrate Threat Models ---
        cursor.execute('SELECT * FROM threat_models')
        models = cursor.fetchall()
        model_count = 0
        for row in models:
            existing = db.session.get(ThreatModel, row['id'])
            if existing:
                continue
            model = ThreatModel(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                methodology=row['methodology'] if 'methodology' in row.keys() else 'STRIDE',
                status=row['status'] if 'status' in row.keys() else 'Active',
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                user_id=row['user_id'],
            )
            db.session.add(model)
            model_count += 1
        db.session.commit()
        print(f'  Migrated {model_count} threat models.')

        # --- Migrate Threats ---
        cursor.execute('SELECT * FROM threats')
        threats = cursor.fetchall()
        threat_count = 0
        for row in threats:
            existing = db.session.get(Threat, row['id'])
            if existing:
                continue
            threat = Threat(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                stride_category=row['stride_category'] if 'stride_category' in row.keys() else None,
                damage=row['damage'],
                reproducibility=row['reproducibility'],
                exploitability=row['exploitability'],
                affected_users=row['affected_users'],
                discoverability=row['discoverability'],
                dread_score=row['dread_score'],
                risk_level=row['risk_level'],
                countermeasure=row['countermeasure'] if 'countermeasure' in row.keys() else None,
                status=row['status'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                model_id=row['model_id'],
            )
            db.session.add(threat)
            threat_count += 1
        db.session.commit()
        print(f'  Migrated {threat_count} threats.')

        # --- Migrate DFD Data ---
        try:
            cursor.execute('SELECT * FROM dfd_data')
            dfd_rows = cursor.fetchall()
            dfd_count = 0
            for row in dfd_rows:
                existing = db.session.get(DFDData, row['id'])
                if existing:
                    continue
                dfd = DFDData(
                    id=row['id'],
                    model_id=row['model_id'],
                    canvas_json=row['canvas_json'],
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow(),
                )
                db.session.add(dfd)
                dfd_count += 1
            db.session.commit()
            print(f'  Migrated {dfd_count} DFD records.')
        except sqlite3.OperationalError:
            print('  No DFD data table found, skipping.')

        # Reset PostgreSQL sequences to avoid ID conflicts
        _reset_sequences(db)

        print('\nMigration complete!')
        print(f'Total: {user_count} users, {model_count} models, {threat_count} threats')

    sqlite_conn.close()


def _reset_sequences(db):
    """Reset PostgreSQL auto-increment sequences after bulk insert."""
    tables = ['users', 'threat_models', 'threats', 'dfd_data']
    for table in tables:
        try:
            db.session.execute(db.text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
            ))
        except Exception:
            pass
    db.session.commit()


if __name__ == '__main__':
    print('=' * 50)
    print('SQLite → PostgreSQL Migration')
    print('=' * 50)
    print(f'Source: {SQLITE_PATH}')
    print(f'Target: {pg_url.split("@")[1] if "@" in pg_url else pg_url}')
    print()

    confirm = input('Proceed with migration? (yes/no): ').strip().lower()
    if confirm != 'yes':
        print('Aborted.')
        sys.exit(0)

    migrate()
