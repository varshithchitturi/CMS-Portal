import sqlite3
from datetime import datetime
import uuid

class NotificationSystem:
    def __init__(self, db_path="complaints.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Initialize database with notifications table"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        conn.close()
    
    def create_notification(self, user_id, title, message, notification_type="info"):
        """Create a new notification for a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        notification_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO notifications 
            (id, user_id, title, message, type, created_at) 
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (notification_id, user_id, title, message, notification_type)
        )
        
        conn.commit()
        conn.close()
        return notification_id
    
    def create_broadcast(self, title, message, notification_type="info", exclude_ids=None):
        """Create a notification for all users, optionally excluding specific users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all user IDs
        if exclude_ids:
            cursor.execute("SELECT id FROM users WHERE id NOT IN (%s)" % ','.join('?'*len(exclude_ids)), exclude_ids)
        else:
            cursor.execute("SELECT id FROM users")
        
        user_ids = [row[0] for row in cursor.fetchall()]
        
        # Create notification for each user
        notification_ids = []
        for user_id in user_ids:
            notification_id = self.create_notification(user_id, title, message, notification_type)
            notification_ids.append(notification_id)
        
        return notification_ids
    
    def create_admin_notification(self, title, message, notification_type="info"):
        """Create a notification for all admin users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all admin user IDs
        cursor.execute("SELECT id FROM users WHERE is_admin = TRUE")
        admin_ids = [row[0] for row in cursor.fetchall()]
        
        # Create notification for each admin
        notification_ids = []
        for admin_id in admin_ids:
            notification_id = self.create_notification(admin_id, title, message, notification_type)
            notification_ids.append(notification_id)
        
        return notification_ids
    
    def create_agent_notification(self, agent_id, title, message, notification_type="info"):
        """Create a notification for a specific agent
        
        Note: Since agents are not linked to user accounts in the current schema,
        this method will store agent notifications separately or skip them.
        In a production system, you'd want to either:
        1. Link agents to user accounts, or
        2. Create a separate agent notification system
        """
        # For now, we'll skip agent notifications since agents don't have user_id
        # This prevents the "no such column: user_id" error
        # TODO: Implement proper agent notification system
        return None
    
    def get_notifications(self, user_id, limit=50, only_unread=False):
        """Get notifications for a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, title, message, type, is_read, created_at FROM notifications WHERE user_id = ?"
        params = [user_id]
        
        if only_unread:
            query += " AND is_read = FALSE"
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                "id": row[0],
                "title": row[1],
                "message": row[2],
                "type": row[3],
                "read": bool(row[4]),
                "time": format_timestamp(row[5])
            })
        
        conn.close()
        return notifications
    
    def mark_as_read(self, notification_id):
        """Mark a notification as read"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = ?", (notification_id,))
        conn.commit()
        conn.close()
    
    def mark_all_as_read(self, user_id):
        """Mark all notifications as read for a specific user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    
    def delete_notification(self, notification_id):
        """Delete a specific notification"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
        conn.commit()
        conn.close()
    
    def get_unread_count(self, user_id):
        """Get the number of unread notifications for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = FALSE", (user_id,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def delete_old_notifications(self, days=30):
        """Delete notifications older than specified days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM notifications WHERE created_at < datetime('now', '-' || ? || ' days')", (days,))
        conn.commit()
        conn.close()

def format_timestamp(timestamp):
    """Format timestamp into a human-readable string"""
    try:
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        diff = now - dt
        
        if diff.days > 30:
            return dt.strftime("%b %d, %Y")
        elif diff.days > 0:
            return f"{diff.days} {'day' if diff.days == 1 else 'days'} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
        else:
            return "Just now"
    except:
        return timestamp
