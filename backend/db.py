import os
import sqlite3
from pathlib import Path

# Check if we're in production (Railway sets DATABASE_URL)
DATABASE_URL = os.getenv("DATABASE_URL")
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_PATH = None
else:
    DB_PATH = Path(__file__).parent / "standupbot.db"

PLACEHOLDER = "%s" if USE_POSTGRES else "?"


def get_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor
    else:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def get_db_connection():
    """Get a direct database connection (not a generator)"""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor
    else:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor
    else:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
    
    # For PostgreSQL, use cursor; for SQLite, use conn directly
    if USE_POSTGRES:
        cur = conn.cursor()
        exec = cur.execute
    else:
        exec = conn.execute
    
    exec(
        f"""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """ if USE_POSTGRES else """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            avatar_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    exec(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            deadline DATE,
            standup_closes_at TIME DEFAULT '21:00',
            leader_id INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """ if USE_POSTGRES else """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            deadline DATE,
            standup_closes_at TIME DEFAULT '21:00',
            leader_id INTEGER NOT NULL REFERENCES users(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    exec(
        """
        CREATE TABLE IF NOT EXISTS project_members (
            id SERIAL PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id),
            user_id INTEGER REFERENCES users(id),
            email TEXT,
            role TEXT NOT NULL DEFAULT 'Member',
            status TEXT NOT NULL CHECK(status IN ('invited','active','declined','removed')) DEFAULT 'invited',
            invite_token TEXT UNIQUE,
            invite_type TEXT CHECK(invite_type IN ('email','link')),
            joined_at TIMESTAMP,
            is_first_standup BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """ if USE_POSTGRES else """
        CREATE TABLE IF NOT EXISTS project_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id),
            user_id INTEGER REFERENCES users(id),
            email TEXT,
            role TEXT NOT NULL DEFAULT 'Member',
            status TEXT NOT NULL CHECK(status IN ('invited','active','declined','removed')) DEFAULT 'invited',
            invite_token TEXT UNIQUE,
            invite_type TEXT CHECK(invite_type IN ('email','link')),
            joined_at DATETIME,
            is_first_standup BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    exec(
        """
        CREATE TABLE IF NOT EXISTS standups (
            id SERIAL PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id),
            member_id INTEGER NOT NULL REFERENCES project_members(id),
            date DATE NOT NULL,
            did TEXT NOT NULL,
            will_do TEXT NOT NULL,
            blocker TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, member_id, date)
        )
        """ if USE_POSTGRES else """
        CREATE TABLE IF NOT EXISTS standups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id),
            member_id INTEGER NOT NULL REFERENCES project_members(id),
            date DATE NOT NULL,
            did TEXT NOT NULL,
            will_do TEXT NOT NULL,
            blocker TEXT,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, member_id, date)
        )
        """
    )
    
    exec(
        """
        CREATE TABLE IF NOT EXISTS briefs (
            id SERIAL PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id),
            date DATE NOT NULL,
            content TEXT NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            submissions_count INTEGER NOT NULL,
            total_active_members INTEGER NOT NULL
        )
        """ if USE_POSTGRES else """
        CREATE TABLE IF NOT EXISTS briefs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(id),
            date DATE NOT NULL,
            content TEXT NOT NULL,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            submissions_count INTEGER NOT NULL,
            total_active_members INTEGER NOT NULL
        )
        """
    )
    
    if USE_POSTGRES:
        cur.close()
    
    conn.commit()
    conn.close()


init_db()