import sqlite3
from werkzeug.security import generate_password_hash
from pathlib import Path

# ================================
# Correct DB Path Setup
# ================================
BASE = Path(__file__).parent
DB = BASE / 'instance' / 'portfolio.db'
DB.parent.mkdir(parents=True, exist_ok=True)

# Connect
con = sqlite3.connect(DB)
cur = con.cursor()

# ================================
# ADMIN TABLE
# ================================
cur.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    pfp TEXT
)
""")

# Insert default admin account
cur.execute("SELECT COUNT(*) FROM admin")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO admin (username, password_hash, pfp)
        VALUES (?, ?, ?)
    """, (
        'admin',
        generate_password_hash('admin123'),
        '/static/uploads/default_pfp.png'
    ))


# ================================
# PROJECTS TABLE
# ================================
cur.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    link TEXT,
    img_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")


# ================================
# SKILLS TABLE (NEW)
# ================================
cur.execute("""
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    percentage INTEGER NOT NULL
)
""")


# ================================
# EXPERIENCE TABLE (NEW)
# ================================
cur.execute("""
CREATE TABLE IF NOT EXISTS experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    years INTEGER NOT NULL
)
""")


# Insert default experience only if empty
cur.execute("SELECT COUNT(*) FROM experience")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO experience (id, years)
        VALUES (1, 2)
    """)


# ================================
# Save + Close
# ================================
con.commit()
con.close()

print("Database initialized successfully!")
