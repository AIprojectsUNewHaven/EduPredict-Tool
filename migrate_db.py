#!/usr/bin/env python3
"""
Database Migration Script for EduPredict Pro
Migrates from username-based to email-based authentication
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = 'edupredict.db'

def migrate_database():
    """Migrate existing database to email-based schema."""
    
    if not os.path.exists(DB_PATH):
        print("No existing database found. Fresh install - no migration needed.")
        return
    
    print(f"Found existing database: {DB_PATH}")
    print("Checking schema...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if email column exists
    cursor.execute("PRAGMA table_info(user)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'email' in columns:
        print("✓ Database already migrated (email column exists)")
        conn.close()
        return
    
    print("\nMigrating database schema...")
    print("-" * 50)
    
    # Backup old data
    cursor.execute("SELECT id, username, password_hash, is_admin, created_at, last_login FROM user")
    old_users = cursor.fetchall()
    
    print(f"Found {len(old_users)} user(s) to migrate")
    
    # Create new user table with email
    cursor.execute("""
        CREATE TABLE user_new (
            id INTEGER PRIMARY KEY,
            email VARCHAR(120) UNIQUE NOT NULL,
            username VARCHAR(80) UNIQUE,
            password_hash VARCHAR(120) NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    
    # Migrate users
    migrated = 0
    for user in old_users:
        user_id, username, password_hash, is_admin, created_at, last_login = user
        
        # Generate email from username
        if username == 'admin':
            email = 'admin@edupredict.local'
        else:
            email = f'{username}@edupredict.local'
        
        cursor.execute("""
            INSERT INTO user_new (id, email, username, password_hash, is_admin, created_at, last_login, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, email, username, password_hash, is_admin, created_at, last_login, 1))
        
        print(f"  Migrated: {username} → {email}")
        migrated += 1
    
    # Drop old table and rename new one
    cursor.execute("DROP TABLE user")
    cursor.execute("ALTER TABLE user_new RENAME TO user")
    
    # Create index on email
    cursor.execute("CREATE INDEX idx_user_email ON user(email)")
    
    # Migrate forecast_history and activity_log (they reference user.id, which hasn't changed)
    print("\n✓ User table migrated successfully")
    
    conn.commit()
    conn.close()
    
    print("-" * 50)
    print(f"Migration complete! {migrated} user(s) migrated.")
    print("\nNew login credentials:")
    print("  Admin: admin@edupredict.local / admin123")
    print("  Other users: <username>@edupredict.local / <original_password>")
    print("\nYou can now log in with email addresses!")

if __name__ == '__main__':
    migrate_database()
