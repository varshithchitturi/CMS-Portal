import sys
import os
sys.path.append('.')

from database import db
import traceback

def test_create_complaint():
    print("Testing create_complaint function...")
    
    try:
        # Test with sample data
        user_id = 1  # Assuming there's a user with ID 1
        title = "Test complaint"
        description = "Test description for debugging"
        category = "Technical"
        priority = "Medium"
        
        print(f"Attempting to create complaint with user_id: {user_id}")
        
        # Check if user exists first
        user = db.get_user_by_id(user_id)
        if not user:
            print("❌ User with ID 1 doesn't exist. Let's check available users...")
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username FROM users LIMIT 5")
            users = cursor.fetchall()
            print("Available users:", users)
            if users:
                user_id = users[0][0]
                print(f"Using user_id: {user_id}")
            else:
                print("No users found in database!")
                conn.close()
                return
            conn.close()
        
        # Try to create the complaint
        ticket_id, complaint_id = db.create_complaint(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            auto_assign=True
        )
        
        print(f"✅ Success! Created ticket: {ticket_id}, complaint_id: {complaint_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        
        # Try to examine the database state
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Check table schema again
            cursor.execute("PRAGMA table_info(complaints)")
            columns = cursor.fetchall()
            print("\nCurrent table schema:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Check if there are any database locks
            cursor.execute("PRAGMA database_list")
            databases = cursor.fetchall()
            print("\nDatabase list:")
            for db_info in databases:
                print(f"  {db_info}")
            
            conn.close()
            
        except Exception as db_error:
            print(f"Failed to examine database: {db_error}")

if __name__ == "__main__":
    test_create_complaint()
