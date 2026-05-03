#!/usr/bin/env python
"""Database migration script for password reset feature"""
from app import create_app, db

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        print('✓ Database tables created/updated successfully')
