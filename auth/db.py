import sqlite3

def get_connection():
    return sqlite3.connect("users.db", check_same_thread=False)

def create_users_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def create_upload_history_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upload_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            filename TEXT,
            filepath TEXT,
            upload_time TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_upload_history(email, filename, filepath):
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor()
    upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO upload_history (email, filename, filepath, upload_time) VALUES (?, ?, ?, ?)", 
                   (email, filename, filepath, upload_time))
    conn.commit()
    conn.close()

def get_upload_history(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filename, filepath, upload_time FROM upload_history WHERE email = ? ORDER BY upload_time DESC", 
                   (email,))
    data = cursor.fetchall()
    conn.close()
    return data
