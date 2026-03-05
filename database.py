import sqlite3
from datetime import date

def init_db():
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    
    # Core Jobs Table [cite: 6, 9]
    cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        title TEXT, company TEXT, location TEXT, 
        posted_date TEXT, url TEXT, description TEXT, 
        score INTEGER DEFAULT 0, processed BOOLEAN DEFAULT 0, 
        last_seen DATE
    )''')

    # Reflection Log: Self-critique and lessons 
    cursor.execute('''CREATE TABLE IF NOT EXISTS reflection_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date DATE,
        phase TEXT, -- "scrape", "tailor", "overall"
        observation TEXT,
        critique TEXT,
        lesson TEXT,
        applied_count INTEGER DEFAULT 0
    )''')

    # Tailoring Patterns: Episodic memory for resume bullets 
    cursor.execute('''CREATE TABLE IF NOT EXISTS tailoring_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        before_snippet TEXT,
        after_snippet TEXT,
        outcome_quality INTEGER, -- 1-10
        created_at DATE
    )''')

    # Beliefs: Evolving data about recruiters/companies 
    cursor.execute('''CREATE TABLE IF NOT EXISTS beliefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT, 
        belief TEXT,
        confidence REAL,
        last_updated DATE
    )''')
    
    conn.commit()
    return conn