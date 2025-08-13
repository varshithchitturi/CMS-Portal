import sqlite3
import os

def check_database_schema():
    db_path = "complaints.db"
    
    if not os.path.exists(db_path):
        print("Database file doesn't exist!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if complaints table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='complaints'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("Complaints table doesn't exist!")
        conn.close()
        return
    
    # Get table info
    cursor.execute("PRAGMA table_info(complaints)")
    columns = cursor.fetchall()
    
    print("Complaints table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - Primary Key: {bool(col[5])}")
    
    # Check if user_id column exists
    column_names = [col[1] for col in columns]
    if 'user_id' not in column_names:
        print("\n❌ ERROR: user_id column is missing from complaints table!")
        print("Available columns:", column_names)
    else:
        print("\n✅ user_id column exists in complaints table")
    
    # Check sample data
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]
    print(f"\nTotal complaints in database: {count}")
    
    conn.close()

if __name__ == "__main__":
    check_database_schema()
