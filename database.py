import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta
import os

class Database:
    def __init__(self, db_path="complaints.db"):
        self.db_path = db_path
        self.init_db()
    
    def recreate_database(self):
        """Recreate the entire database with fresh schema"""
        import os
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.init_db()
    
    def get_connection(self):
        # Always create a fresh connection to avoid cached schema issues
        conn = sqlite3.connect(self.db_path)
        # Ensure foreign keys are enabled
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def migrate_database(self, cursor):
        """Handle database migrations for schema updates"""
        try:
            # Check if complaints table exists and has correct columns
            cursor.execute("PRAGMA table_info(complaints)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns and len(columns) > 0:
                # Old schema detected, need to migrate
                print("Migrating database schema...")
                
                # Drop old tables and recreate with correct schema
                cursor.execute("DROP TABLE IF EXISTS complaints")
                cursor.execute("DROP TABLE IF EXISTS chat_history")
                cursor.execute("DROP TABLE IF EXISTS admin_actions")
                cursor.execute("DROP TABLE IF EXISTS agent_responses")
                
                print("Old tables dropped, will recreate with correct schema")
                
        except Exception as e:
            print(f"Migration check failed, proceeding with normal init: {e}")
    
    def init_db(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if we need to migrate existing tables
        self.migrate_database(cursor)
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Complaints table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT DEFAULT 'Registered',
                assigned_to TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolution_notes TEXT,
                estimated_resolution_time TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Chat history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id TEXT,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Admin actions log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                target_id TEXT,
                description TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
        ''')
        
        # Agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                specialization TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'Active',
                assigned_tickets INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Agent responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                agent_id INTEGER NOT NULL,
                response_text TEXT NOT NULL,
                response_type TEXT DEFAULT 'Update',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents (id),
                FOREIGN KEY (ticket_id) REFERENCES complaints (ticket_id)
            )
        ''')
        
        # Create default admin user
        self.create_default_admin()
        
        # Create default agents
        self.create_default_agents()
        
        conn.commit()
        conn.close()
    
    def create_default_admin(self):
        """Create default admin users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if leena admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'leena'")
        if not cursor.fetchone():
            # Create leena admin user
            password_hash = hashlib.sha256("12345678".encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', ("leena", "leenageepalem@gmail.com", password_hash, "Leena Geepalem", True))
        
        # Check if default admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            # Create default admin user
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, is_admin)
                VALUES (?, ?, ?, ?, ?)
            ''', ("admin", "admin@complaint-system.com", password_hash, "System Administrator", True))
        
        conn.commit()
        conn.close()
    
    def create_default_agents(self):
        """Create default agents"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        agents = [
            {
                'name': 'G. Leena',
                'email': 'leena.g@support.com',
                'phone': '+91-9876543210',
                'specialization': 'Technical Support',
                'description': 'Senior Technical Specialist with expertise in system troubleshooting, connectivity issues, and software problems. 5+ years experience in resolving complex technical challenges.'
            },
            {
                'name': 'B. Balu',
                'email': 'balu.b@support.com',
                'phone': '+91-9876543211',
                'specialization': 'Billing & Finance',
                'description': 'Billing Specialist with comprehensive knowledge of payment processing, refunds, and financial inquiries. Expert in resolving billing disputes and account management.'
            },
            {
                'name': 'K. Rahul',
                'email': 'rahul.k@support.com',
                'phone': '+91-9876543212',
                'specialization': 'Customer Service',
                'description': 'Customer Service Expert specializing in general inquiries, service complaints, and customer satisfaction. Excellent communication skills and problem-solving abilities.'
            },
            {
                'name': 'R. Charshima',
                'email': 'charshima.r@support.com',
                'phone': '+91-9876543213',
                'specialization': 'Product Support',
                'description': 'Product Specialist with deep knowledge of product features, defects, and quality issues. Experienced in handling product-related complaints and improvements.'
            },
            {
                'name': 'Lakshmi',
                'email': 'lakshmi@support.com',
                'phone': '+91-9876543214',
                'specialization': 'Escalation Management',
                'description': 'Senior Escalation Manager handling critical and urgent issues. Expert in complex problem resolution and customer relationship management.'
            }
        ]
        
        for agent in agents:
            # Check if agent already exists
            cursor.execute("SELECT id FROM agents WHERE email = ?", (agent['email'],))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO agents (name, email, phone, specialization, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (agent['name'], agent['email'], agent['phone'], agent['specialization'], agent['description']))
        
        conn.commit()
        conn.close()
    
    def get_best_agent_for_category(self, category, priority):
        """Get the best available agent for a specific category and priority"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Category to specialization mapping
        category_mapping = {
            'Technical': 'Technical Support',
            'Billing': 'Billing & Finance', 
            'Service': 'Customer Service',
            'Product': 'Product Support',
            'General': 'Escalation Management'  # Default fallback
        }
        
        specialization = category_mapping.get(category, 'Escalation Management')
        
        # For urgent/high priority, try to find agent with lowest workload in specialization
        if priority in ['Urgent', 'High']:
            cursor.execute('''
                SELECT name, assigned_tickets
                FROM agents
                WHERE specialization = ? AND status = 'Active'
                ORDER BY assigned_tickets ASC, name ASC
                LIMIT 1
            ''', (specialization,))
        else:
            # For medium/low priority, use round-robin assignment
            cursor.execute('''
                SELECT name, assigned_tickets
                FROM agents
                WHERE specialization = ? AND status = 'Active'
                ORDER BY assigned_tickets ASC, RANDOM()
                LIMIT 1
            ''', (specialization,))
        
        agent = cursor.fetchone()
        
        # If no agent found in specialization, assign to escalation manager
        if not agent:
            cursor.execute('''
                SELECT name, assigned_tickets
                FROM agents
                WHERE specialization = 'Escalation Management' AND status = 'Active'
                ORDER BY assigned_tickets ASC
                LIMIT 1
            ''')
            agent = cursor.fetchone()
        
        conn.close()
        
        return agent[0] if agent else None
    
    def get_category_workload_stats(self):
        """Get workload statistics by category"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get agent workload by specialization
        cursor.execute('''
            SELECT a.specialization, a.name, a.assigned_tickets,
                   COUNT(c.id) as active_tickets
            FROM agents a
            LEFT JOIN complaints c ON a.name = c.assigned_to AND c.status != 'Resolved'
            WHERE a.status = 'Active'
            GROUP BY a.id, a.specialization, a.name, a.assigned_tickets
            ORDER BY a.specialization, a.assigned_tickets
        ''')
        
        workload_stats = cursor.fetchall()
        conn.close()
        
        # Organize by specialization
        stats_by_category = {}
        for row in workload_stats:
            specialization = row[0]
            if specialization not in stats_by_category:
                stats_by_category[specialization] = []
            
            stats_by_category[specialization].append({
                'name': row[1],
                'total_assigned': row[2],
                'active_tickets': row[3]
            })
        
        return stats_by_category
    
    def reassign_ticket(self, ticket_id, new_agent, admin_id, reason="Manual reassignment"):
        """Reassign ticket to different agent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get current assignment
        cursor.execute('SELECT assigned_to FROM complaints WHERE ticket_id = ?', (ticket_id,))
        current_agent = cursor.fetchone()
        
        if current_agent and current_agent[0]:
            # Decrease old agent's count
            cursor.execute('''
                UPDATE agents 
                SET assigned_tickets = assigned_tickets - 1
                WHERE name = ? AND assigned_tickets > 0
            ''', (current_agent[0],))
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update ticket assignment
        cursor.execute('''
            UPDATE complaints 
            SET assigned_to = ?, updated_at = ?
            WHERE ticket_id = ?
        ''', (new_agent, current_time, ticket_id))
        
        # Increase new agent's count
        cursor.execute('''
            UPDATE agents 
            SET assigned_tickets = assigned_tickets + 1
            WHERE name = ?
        ''', (new_agent,))
        
        # Log admin action
        cursor.execute('''
            INSERT INTO admin_actions (admin_id, action_type, target_id, description, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (admin_id, 'REASSIGN_TICKET', ticket_id, f"Reassigned to {new_agent}: {reason}", current_time))
        
        conn.commit()
        conn.close()
    
    def get_unassigned_tickets(self):
        """Get all unassigned tickets"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.username, u.email, u.full_name
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.assigned_to IS NULL OR c.assigned_to = ''
            ORDER BY 
                CASE c.priority 
                    WHEN 'Urgent' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                END,
                c.created_at ASC
        ''')
        
        tickets = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'ticket_id': row[1],
                'user_id': row[2],
                'title': row[3],
                'description': row[4],
                'category': row[5],
                'priority': row[6],
                'status': row[7],
                'assigned_to': row[8],
                'created_at': row[9],
                'updated_at': row[10],
                'resolved_at': row[11],
                'resolution_notes': row[12],
                'estimated_resolution_time': row[13],
                'username': row[14],
                'email': row[15],
                'full_name': row[16]
            }
            for row in tickets
        ]
    
    def hash_password(self, password):
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, email, password, full_name, phone=None):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, phone))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, username, email, full_name, is_admin 
            FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'is_admin': user[4]
            }
        return None
    
    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_hash, full_name, phone, created_at, is_admin 
            FROM users 
            WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    def generate_ticket_id(self):
        """Generate unique ticket ID"""
        return f"P004-{uuid.uuid4().hex[:8].upper()}"
    
    def create_complaint(self, user_id, title, description, category, priority, auto_assign=True):
        """Create a new complaint/ticket with optional auto-assignment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Safety check: Verify the table schema has user_id column
        try:
            cursor.execute("PRAGMA table_info(complaints)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'user_id' not in columns:
                raise Exception("Database schema error: user_id column missing from complaints table")
        except Exception as e:
            conn.close()
            raise Exception(f"Database schema validation failed: {e}")
        
        ticket_id = self.generate_ticket_id()
        
        # Estimate resolution time based on priority
        resolution_times = {
            'Urgent': '2-4 hours',
            'High': '1-2 days',
            'Medium': '3-5 days',
            'Low': '5-7 days'
        }
        
        # Auto-assign agent based on category if enabled
        assigned_to = None
        if auto_assign:
            assigned_to = self.get_best_agent_for_category(category, priority)
        
        # Use local time instead of CURRENT_TIMESTAMP
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO complaints 
            (ticket_id, user_id, title, description, category, priority, assigned_to, estimated_resolution_time, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ticket_id, user_id, title, description, category, priority, assigned_to, resolution_times.get(priority, '5-7 days'), current_time, current_time))
        
        complaint_id = cursor.lastrowid
        
        # Update agent assigned tickets count if auto-assigned
        if assigned_to:
            cursor.execute('''
                UPDATE agents 
                SET assigned_tickets = assigned_tickets + 1
                WHERE name = ?
            ''', (assigned_to,))
        
        conn.commit()
        conn.close()
        
        return ticket_id, complaint_id
    
    def get_user_complaints(self, user_id):
        """Get all complaints for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ticket_id, title, category, priority, status, created_at, estimated_resolution_time
            FROM complaints 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        complaints = cursor.fetchall()
        conn.close()
        
        return [
            {
                'ticket_id': row[0],
                'title': row[1],
                'category': row[2],
                'priority': row[3],
                'status': row[4],
                'created_at': row[5],
                'estimated_resolution_time': row[6]
            }
            for row in complaints
        ]
    
    def get_complaint_by_ticket_id(self, ticket_id):
        """Get complaint details by ticket ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.username, u.email, u.full_name
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.ticket_id = ?
        ''', (ticket_id,))
        
        complaint = cursor.fetchone()
        conn.close()
        
        if complaint:
            return {
                'id': complaint[0],
                'ticket_id': complaint[1],
                'user_id': complaint[2],
                'title': complaint[3],
                'description': complaint[4],
                'category': complaint[5],
                'priority': complaint[6],
                'status': complaint[7],
                'assigned_to': complaint[8],
                'created_at': complaint[9],
                'updated_at': complaint[10],
                'resolved_at': complaint[11],
                'resolution_notes': complaint[12],
                'estimated_resolution_time': complaint[13],
                'username': complaint[14],
                'email': complaint[15],
                'full_name': complaint[16]
            }
        return None
    
    def get_all_complaints_admin(self):
        """Get all complaints for admin dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.username, u.email, u.full_name
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            ORDER BY 
                CASE c.priority 
                    WHEN 'Urgent' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                END,
                c.created_at DESC
        ''')
        
        complaints = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'ticket_id': row[1],
                'user_id': row[2],
                'title': row[3],
                'description': row[4],
                'category': row[5],
                'priority': row[6],
                'status': row[7],
                'assigned_to': row[8],
                'created_at': row[9],
                'updated_at': row[10],
                'resolved_at': row[11],
                'resolution_notes': row[12],
                'estimated_resolution_time': row[13],
                'username': row[14],
                'email': row[15],
                'full_name': row[16]
            }
            for row in complaints
        ]
    
    def update_complaint_status(self, ticket_id, status, assigned_to=None, resolution_notes=None):
        """Update complaint status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if status == 'Resolved':
            cursor.execute('''
                UPDATE complaints 
                SET status = ?, assigned_to = ?, resolution_notes = ?, 
                    resolved_at = ?, updated_at = ?
                WHERE ticket_id = ?
            ''', (status, assigned_to, resolution_notes, current_time, current_time, ticket_id))
        else:
            cursor.execute('''
                UPDATE complaints 
                SET status = ?, assigned_to = ?, updated_at = ?
                WHERE ticket_id = ?
            ''', (status, assigned_to, current_time, ticket_id))
        
        conn.commit()
        conn.close()
    
    def save_chat_history(self, user_id, session_id, message, response):
        """Save chat interaction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Use local time instead of CURRENT_TIMESTAMP
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO chat_history (user_id, session_id, message, response, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, session_id, message, response, current_time))
        
        conn.commit()
        conn.close()
    
    def get_chat_history(self, user_id, session_id, limit=10):
        """Get recent chat history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, response, timestamp
            FROM chat_history
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, session_id, limit))
        
        history = cursor.fetchall()
        conn.close()
        
        return [
            {
                'message': row[0],
                'response': row[1],
                'timestamp': row[2]
            }
            for row in reversed(history)
        ]
    
    def get_dashboard_stats(self):
        """Get comprehensive statistics for admin dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get current date for local time comparisons
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Total complaints
        cursor.execute("SELECT COUNT(*) FROM complaints")
        total_complaints = cursor.fetchone()[0]
        
        # Open complaints
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status != 'Resolved'")
        open_complaints = cursor.fetchone()[0]
        
        # Resolved complaints
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'")
        resolved_complaints = cursor.fetchone()[0]
        
        # Today's complaints (using local time)
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE DATE(created_at) = DATE(?)", (today,))
        today_complaints = cursor.fetchone()[0]
        
        # This week's complaints (using local time)
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE created_at >= ?", (week_ago,))
        week_complaints = cursor.fetchone()[0]
        
        # Priority breakdown (open tickets only)
        cursor.execute('''
            SELECT priority, COUNT(*) 
            FROM complaints 
            WHERE status != 'Resolved'
            GROUP BY priority
        ''')
        priority_stats = dict(cursor.fetchall())
        
        # Category breakdown (all tickets)
        cursor.execute('''
            SELECT category, COUNT(*) 
            FROM complaints 
            GROUP BY category
        ''')
        category_stats = dict(cursor.fetchall())
        
        # Status breakdown
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM complaints 
            GROUP BY status
        ''')
        status_stats = dict(cursor.fetchall())
        
        # Recent activity (last 10 tickets)
        cursor.execute('''
            SELECT c.ticket_id, c.title, c.priority, c.status, c.created_at, u.full_name
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.created_at DESC
            LIMIT 10
        ''')
        recent_tickets = [
            {
                'ticket_id': row[0],
                'title': row[1],
                'priority': row[2],
                'status': row[3],
                'created_at': row[4],
                'user_name': row[5]
            }
            for row in cursor.fetchall()
        ]
        
        # Average resolution time
        cursor.execute('''
            SELECT AVG(julianday(resolved_at) - julianday(created_at)) as avg_days
            FROM complaints 
            WHERE resolved_at IS NOT NULL
        ''')
        avg_resolution_days = cursor.fetchone()[0] or 0
        
        # High priority urgent tickets
        cursor.execute('''
            SELECT COUNT(*) 
            FROM complaints 
            WHERE priority IN ('Urgent', 'High') AND status != 'Resolved'
        ''')
        urgent_tickets = cursor.fetchone()[0]
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = FALSE")
        total_users = cursor.fetchone()[0]
        
        # Active chat sessions today (using local time)
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM chat_history WHERE DATE(timestamp) = DATE(?)", (today,))
        active_chats_today = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_complaints': total_complaints,
            'open_complaints': open_complaints,
            'resolved_complaints': resolved_complaints,
            'today_complaints': today_complaints,
            'week_complaints': week_complaints,
            'urgent_tickets': urgent_tickets,
            'total_users': total_users,
            'active_chats_today': active_chats_today,
            'avg_resolution_days': round(avg_resolution_days, 1) if avg_resolution_days else 0,
            'priority_stats': priority_stats,
            'category_stats': category_stats,
            'status_stats': status_stats,
            'recent_tickets': recent_tickets
        }
    
    def get_all_agents(self):
        """Get all agents"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, phone, specialization, description, status, assigned_tickets
            FROM agents
            ORDER BY name
        ''')
        
        agents = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'specialization': row[4],
                'description': row[5],
                'status': row[6],
                'assigned_tickets': row[7]
            }
            for row in agents
        ]
    
    def get_agent_by_id(self, agent_id):
        """Get agent details by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, phone, specialization, description, status, assigned_tickets
            FROM agents
            WHERE id = ?
        ''', (agent_id,))
        
        agent = cursor.fetchone()
        conn.close()
        
        if agent:
            return {
                'id': agent[0],
                'name': agent[1],
                'email': agent[2],
                'phone': agent[3],
                'specialization': agent[4],
                'description': agent[5],
                'status': agent[6],
                'assigned_tickets': agent[7]
            }
        return None
    
    def get_agent_by_name(self, agent_name):
        """Get agent details by name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, phone, specialization, description, status, assigned_tickets
            FROM agents
            WHERE name = ?
        ''', (agent_name,))
        
        agent = cursor.fetchone()
        conn.close()
        
        if agent:
            return {
                'id': agent[0],
                'name': agent[1],
                'email': agent[2],
                'phone': agent[3],
                'specialization': agent[4],
                'description': agent[5],
                'status': agent[6],
                'assigned_tickets': agent[7]
            }
        return None
    
    def get_agent_tickets(self, agent_name):
        """Get tickets assigned to a specific agent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, u.username, u.email, u.full_name
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            WHERE c.assigned_to = ?
            ORDER BY 
                CASE c.priority 
                    WHEN 'Urgent' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                END,
                c.created_at DESC
        ''', (agent_name,))
        
        tickets = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'ticket_id': row[1],
                'user_id': row[2],
                'title': row[3],
                'description': row[4],
                'category': row[5],
                'priority': row[6],
                'status': row[7],
                'assigned_to': row[8],
                'created_at': row[9],
                'updated_at': row[10],
                'resolved_at': row[11],
                'resolution_notes': row[12],
                'estimated_resolution_time': row[13],
                'username': row[14],
                'email': row[15],
                'full_name': row[16]
            }
            for row in tickets
        ]
    
    def assign_ticket_to_agent(self, ticket_id, agent_name):
        """Assign ticket to agent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            UPDATE complaints 
            SET assigned_to = ?, status = 'In Progress', updated_at = ?
            WHERE ticket_id = ?
        ''', (agent_name, current_time, ticket_id))
        
        # Update agent's assigned ticket count
        cursor.execute('''
            UPDATE agents 
            SET assigned_tickets = assigned_tickets + 1
            WHERE name = ?
        ''', (agent_name,))
        
        conn.commit()
        conn.close()
    
    def add_agent_response(self, ticket_id, agent_id, response_text, response_type='Update'):
        """Add agent response to ticket"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO agent_responses (ticket_id, agent_id, response_text, response_type, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (ticket_id, agent_id, response_text, response_type, current_time))
        
        # Update ticket status
        cursor.execute('''
            UPDATE complaints 
            SET updated_at = ?
            WHERE ticket_id = ?
        ''', (current_time, ticket_id))
        
        conn.commit()
        conn.close()
    
    def get_ticket_responses(self, ticket_id):
        """Get all responses for a ticket"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ar.*, a.name, a.specialization
            FROM agent_responses ar
            JOIN agents a ON ar.agent_id = a.id
            WHERE ar.ticket_id = ?
            ORDER BY ar.created_at DESC
        ''', (ticket_id,))
        
        responses = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'ticket_id': row[1],
                'agent_id': row[2],
                'response_text': row[3],
                'response_type': row[4],
                'created_at': row[5],
                'agent_name': row[6],
                'agent_specialization': row[7]
            }
            for row in responses
        ]

# Initialize database
db = Database()

def reinitialize_global_db():
    """Reinitialize the global database instance"""
    global db
    db = Database()
    return db
