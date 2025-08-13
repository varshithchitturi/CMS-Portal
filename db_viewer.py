#!/usr/bin/env python3
"""
Database Viewer for IntelliSupport AI - Complaint Management System
This script allows you to view all data in your complaints.db SQLite database
"""

import sqlite3
import os
from datetime import datetime
from tabulate import tabulate

class DatabaseViewer:
    def __init__(self, db_path="complaints.db"):
        self.db_path = db_path
        
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_all_tables(self):
        """Get list of all tables in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return tables
    
    def get_table_schema(self, table_name):
        """Get schema information for a table"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name});")
        schema = cursor.fetchall()
        
        conn.close()
        return schema
    
    def get_table_data(self, table_name, limit=None):
        """Get all data from a table"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = f"SELECT * FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
            
        cursor.execute(query)
        data = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in cursor.fetchall()]
        
        conn.close()
        return columns, data
    
    def get_table_count(self, table_name):
        """Get row count for a table"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def display_table_summary(self):
        """Display summary of all tables"""
        print("=" * 80)
        print("📊 IntelliSupport AI - Database Summary")
        print("=" * 80)
        print(f"📁 Database File: {self.db_path}")
        print(f"📅 Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        tables = self.get_all_tables()
        
        if not tables:
            print("❌ No tables found in the database!")
            return
            
        summary_data = []
        for table in tables:
            count = self.get_table_count(table)
            summary_data.append([table, count])
        
        print("\n📋 Tables Overview:")
        print(tabulate(summary_data, headers=["Table Name", "Row Count"], tablefmt="grid"))
        
    def display_table_details(self, table_name):
        """Display detailed information about a specific table"""
        print(f"\n{'='*80}")
        print(f"🔍 Table: {table_name}")
        print(f"{'='*80}")
        
        # Show schema
        schema = self.get_table_schema(table_name)
        print("\n📋 Schema:")
        schema_data = []
        for col in schema:
            schema_data.append([col[1], col[2], "YES" if col[3] else "NO", col[4] if col[4] else ""])
        
        print(tabulate(schema_data, 
                      headers=["Column", "Type", "Not Null", "Default"], 
                      tablefmt="grid"))
        
        # Show data
        columns, data = self.get_table_data(table_name)
        row_count = len(data)
        
        print(f"\n📊 Data ({row_count} rows):")
        
        if row_count == 0:
            print("   No data found in this table.")
        else:
            # Truncate long text for better display
            display_data = []
            for row in data:
                display_row = []
                for cell in row:
                    if isinstance(cell, str) and len(cell) > 50:
                        display_row.append(cell[:47] + "...")
                    else:
                        display_row.append(cell)
                display_data.append(display_row)
            
            print(tabulate(display_data, headers=columns, tablefmt="grid"))
    
    def display_all_data(self):
        """Display all data from all tables"""
        self.display_table_summary()
        
        tables = self.get_all_tables()
        for table in tables:
            self.display_table_details(table)
    
    def interactive_menu(self):
        """Interactive menu for database viewing"""
        while True:
            print("\n" + "="*60)
            print("🔍 IntelliSupport AI - Database Viewer")
            print("="*60)
            print("1. Show database summary")
            print("2. View specific table")
            print("3. View all tables and data")
            print("4. Search users")
            print("5. Search tickets/complaints")
            print("6. View agents")
            print("7. Exit")
            print("="*60)
            
            choice = input("Enter your choice (1-7): ").strip()
            
            if choice == "1":
                self.display_table_summary()
            
            elif choice == "2":
                tables = self.get_all_tables()
                print("\nAvailable tables:")
                for i, table in enumerate(tables, 1):
                    print(f"  {i}. {table}")
                
                try:
                    table_choice = int(input(f"Enter table number (1-{len(tables)}): "))
                    if 1 <= table_choice <= len(tables):
                        self.display_table_details(tables[table_choice - 1])
                    else:
                        print("❌ Invalid table number!")
                except ValueError:
                    print("❌ Please enter a valid number!")
            
            elif choice == "3":
                self.display_all_data()
            
            elif choice == "4":
                self.search_users()
            
            elif choice == "5":
                self.search_tickets()
            
            elif choice == "6":
                self.view_agents()
            
            elif choice == "7":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice! Please try again.")
    
    def search_users(self):
        """Search and display users"""
        print("\n🔍 User Search")
        print("-" * 40)
        
        columns, data = self.get_table_data("users")
        
        if not data:
            print("No users found!")
            return
        
        print(f"Found {len(data)} users:")
        
        # Format user data for better display
        user_data = []
        for row in data:
            user_data.append([
                row[0],  # ID
                row[1],  # Username
                row[2],  # Email
                row[4],  # Full Name
                row[5] if row[5] else "N/A",  # Phone
                "Admin" if row[7] else "User",  # Role
                row[6]   # Created At
            ])
        
        print(tabulate(user_data, 
                      headers=["ID", "Username", "Email", "Full Name", "Phone", "Role", "Created"], 
                      tablefmt="grid"))
    
    def search_tickets(self):
        """Search and display tickets/complaints"""
        print("\n🎫 Tickets/Complaints Search")
        print("-" * 40)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get tickets with user information
        cursor.execute("""
            SELECT c.ticket_id, c.title, c.category, c.priority, c.status, 
                   c.assigned_to, c.created_at, u.full_name
            FROM complaints c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.created_at DESC
        """)
        
        tickets = cursor.fetchall()
        conn.close()
        
        if not tickets:
            print("No tickets found!")
            return
        
        print(f"Found {len(tickets)} tickets:")
        
        ticket_data = []
        for ticket in tickets:
            ticket_data.append([
                ticket[0],  # Ticket ID
                ticket[1][:30] + "..." if len(ticket[1]) > 30 else ticket[1],  # Title
                ticket[2],  # Category
                ticket[3],  # Priority
                ticket[4],  # Status
                ticket[5] if ticket[5] else "Unassigned",  # Assigned To
                ticket[7],  # User Name
                ticket[6]   # Created At
            ])
        
        print(tabulate(ticket_data, 
                      headers=["Ticket ID", "Title", "Category", "Priority", "Status", "Assigned To", "User", "Created"], 
                      tablefmt="grid"))
    
    def view_agents(self):
        """View all agents"""
        print("\n👥 Agents Overview")
        print("-" * 40)
        
        columns, data = self.get_table_data("agents")
        
        if not data:
            print("No agents found!")
            return
        
        print(f"Found {len(data)} agents:")
        
        agent_data = []
        for row in data:
            agent_data.append([
                row[0],  # ID
                row[1],  # Name
                row[2],  # Email
                row[4],  # Specialization
                row[6],  # Status
                row[7],  # Assigned Tickets
            ])
        
        print(tabulate(agent_data, 
                      headers=["ID", "Name", "Email", "Specialization", "Status", "Assigned Tickets"], 
                      tablefmt="grid"))

def main():
    # Check if database exists
    db_path = "complaints.db"
    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found!")
        print("Make sure you're running this script from the same directory as your database.")
        return
    
    try:
        viewer = DatabaseViewer(db_path)
        viewer.interactive_menu()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
