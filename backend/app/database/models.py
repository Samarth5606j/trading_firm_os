import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "paper_trading.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Isolated currency cash vaults table
    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY,
            inr_cash REAL,
            usd_cash REAL,
            total_trades INTEGER
        )
    """)
    
    # 2. Executed orders ledger table
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            action TEXT,
            quantity INTEGER,
            executed_price REAL,
            stop_loss REAL,
            take_profit REAL,
            fee REAL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Seed portfolio balances if brand new
    c.execute("SELECT COUNT(*) FROM portfolio")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO portfolio (id, inr_cash, usd_cash, total_trades) 
            VALUES (1, 100000.0, 10000.0, 0)
        """)

    conn.commit()
    conn.close()