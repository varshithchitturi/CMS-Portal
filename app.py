from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from gemini_chat import chatbot
from database import db
from agent_manager import agent_manager
from notifications import NotificationSystem
import uuid
from datetime import datetime
import markdown

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "P-004-complaint-management-secret-key")

# Initialize the notification system
notification_system = NotificationSystem()

# Routes
@app.route("/")
def index():
    """Main landing page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration"""
    if request.method == "POST":
        data = request.get_json()
        
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        full_name = data.get("full_name")
        phone = data.get("phone")
        
        if not all([username, email, password, full_name]):
            return jsonify({"success": False, "message": "All fields are required"})
        
        user_id = db.create_user(username, email, password, full_name, phone)
        
        if user_id:
            return jsonify({"success": True, "message": "Registration successful! Please login."})
        else:
            return jsonify({"success": False, "message": "Username or email already exists"})
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """User login"""
    if request.method == "POST":
        data = request.get_json()
        
        username = data.get("username")
        password = data.get("password")
        
        user = db.authenticate_user(username, password)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            session['full_name'] = user['full_name']
            
            if user['is_admin']:
                return jsonify({"success": True, "redirect": "/admin"})
            else:
                return jsonify({"success": True, "redirect": "/dashboard"})
        else:
            return jsonify({"success": False, "message": "Invalid username or password"})
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route("/profile")
def profile():
    """User profile view"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_details = db.get_user_by_id(session['user_id'])
    if user_details:
        return jsonify({
            "success": True,
            "username": user_details[1],
            "email": user_details[2], 
            "full_name": user_details[4],
            "phone": user_details[5] if user_details[5] else "Not provided",
            "created_at": user_details[6],
            "is_admin": bool(user_details[7])
        })
    return jsonify({"success": False, "message": "User not found"})

@app.route("/dashboard")
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_complaints = db.get_user_complaints(session['user_id'])
    return render_template("dashboard.html", complaints=user_complaints)

@app.route("/chat")
def chat():
    """Chatbot interface"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Generate new session ID for chat
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())
    
    return render_template("chat.html")

@app.route("/ask", methods=["POST"])
def ask():
    """Handle chatbot conversations"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    user_message = data.get("message", "")
    
    if not user_message.strip():
        return jsonify({"reply": "Please enter a message."})
    
    # Get chat session ID
    chat_session_id = session.get('chat_session_id', str(uuid.uuid4()))
    session['chat_session_id'] = chat_session_id
    
    # Get chat history for context
    chat_history = db.get_chat_history(session['user_id'], chat_session_id)
    
    # Get bot response
    bot_result = chatbot.chat_with_bot(
        user_message, 
        user_id=session['user_id'], 
        session_id=chat_session_id
    )
    
    # Save chat history
    db.save_chat_history(
        session['user_id'], 
        chat_session_id, 
        user_message, 
        bot_result['response']
    )
    
    response_data = {
        "reply": bot_result['response'],
        "reply_html": markdown.markdown(bot_result['response']),
        "requires_ticket": bot_result.get('requires_ticket', False),
        "session_id": bot_result['session_id']
    }
    
    # If ticket is required, provide option to create ticket
    if bot_result.get('requires_ticket', False):
        response_data["show_ticket_button"] = True
        response_data["ticket_message"] = "Would you like me to create a support ticket for this issue?"
    
    return jsonify(response_data)

@app.route("/create_ticket", methods=["POST"])
def create_ticket():
    """Create support ticket from chat with auto-assignment"""
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"success": False, "error": "Invalid request data"}), 400
            
        user_message = data.get("message", "")
        chat_session_id = session.get('chat_session_id')
        
        # Get chat history for context
        chat_history = db.get_chat_history(session['user_id'], chat_session_id)
        
        # Generate ticket summary using AI
        ticket_info = chatbot.generate_ticket_summary(user_message, chat_history)
        if not all(key in ticket_info for key in ['title', 'description', 'category', 'priority']):
            raise ValueError("Failed to generate complete ticket summary from AI.")

        # Create the ticket with auto-assignment enabled
        ticket_id, complaint_id = db.create_complaint(
            session['user_id'],
            ticket_info['title'],
            ticket_info['description'],
            ticket_info['category'],
            ticket_info['priority'],
            auto_assign=True  # Enable auto-assignment
        )
        
        if not ticket_id:
            raise ConnectionError("Failed to create a complaint in the database.")

        # Get the assigned agent info
        complaint = db.get_complaint_by_ticket_id(ticket_id)
        assigned_agent = complaint['assigned_to'] if complaint else None
        
        # Create notifications
        notification_system.create_notification(
            session['user_id'],
            f"Ticket #{ticket_id} Created",
            f"Your {ticket_info['priority']} priority ticket has been created successfully.",
            "info"
        )
        notification_system.create_admin_notification(
            f"New Ticket Created",
            f"New {ticket_info['priority']} priority ticket #{ticket_id} created by {session['full_name']}.",
            "info"
        )
        if assigned_agent:
            agent = db.get_agent_by_name(assigned_agent)
            if agent:
                notification_system.create_agent_notification(
                    agent['id'],
                    f"New Ticket Assignment",
                    f"Ticket #{ticket_id} has been automatically assigned to you.",
                    "info"
                )
        
        assignment_message = f" Your ticket has been automatically assigned to {assigned_agent}." if assigned_agent else ""
        
        return jsonify({
            "success": True,
            "ticket_id": ticket_id,
            "category": ticket_info['category'],
            "priority": ticket_info['priority'],
            "assigned_agent": assigned_agent,
            "message": f"Support ticket {ticket_id} has been created successfully!{assignment_message} Our team will review your issue."
        })

    except Exception as e:
        # Log the full error for debugging
        print(f"Error in /create_ticket: {e}")
        # Return a JSON error to the frontend
        return jsonify({"success": False, "error": f"An internal server error occurred: {e}"}), 500

@app.route("/ticket/<ticket_id>")
def view_ticket(ticket_id):
    """View specific ticket details"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    complaint = db.get_complaint_by_ticket_id(ticket_id)
    
    if not complaint:
        flash("Ticket not found")
        return redirect(url_for('dashboard'))
    
    # Check if user owns this ticket (unless admin)
    if not session.get('is_admin') and complaint['user_id'] != session['user_id']:
        flash("Access denied")
        return redirect(url_for('dashboard'))
    
    # Get agent responses for this ticket
    agent_responses = db.get_ticket_responses(ticket_id)
    
    # Convert markdown to HTML for responses
    for response in agent_responses:
        response['response_html'] = markdown.markdown(response['response_text'])
    
    return render_template("ticket_details.html", complaint=complaint, agent_responses=agent_responses)

@app.route("/admin")
def admin_dashboard():
    """Admin dashboard"""
    if not session.get('is_admin'):
        flash("Access denied. Admin privileges required.")
        return redirect(url_for('login'))
    
    complaints = db.get_all_complaints_admin()
    stats = db.get_dashboard_stats()
    
    return render_template("admin_dashboard.html", complaints=complaints, stats=stats)

@app.route("/admin/update_ticket", methods=["POST"])
def admin_update_ticket():
    """Admin update ticket status"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    data = request.get_json()
    ticket_id = data.get("ticket_id")
    status = data.get("status")
    assigned_to = data.get("assigned_to")
    resolution_notes = data.get("resolution_notes")
    
    db.update_complaint_status(ticket_id, status, assigned_to, resolution_notes)
    
    return jsonify({"success": True, "message": "Ticket updated successfully"})

@app.route("/admin/agents")
def admin_agents():
    """Admin agents management page"""
    if not session.get('is_admin'):
        flash("Access denied. Admin privileges required.")
        return redirect(url_for('login'))
    
    agents = db.get_all_agents()
    unassigned_tickets = db.get_unassigned_tickets()
    return render_template("admin_agents.html", agents=agents, unassigned_tickets=unassigned_tickets)

@app.route("/admin/agent/<int:agent_id>")
def admin_agent_details(agent_id):
    """Admin view agent details and assigned tickets"""
    if not session.get('is_admin'):
        flash("Access denied. Admin privileges required.")
        return redirect(url_for('login'))
    
    agent = db.get_agent_by_id(agent_id)
    if not agent:
        flash("Agent not found")
        return redirect(url_for('admin_agents'))
    
    assigned_tickets = db.get_agent_tickets(agent['name'])
    return render_template("admin_agent_details.html", agent=agent, tickets=assigned_tickets)

@app.route("/admin/assign_ticket", methods=["POST"])
def assign_ticket():
    """Assign ticket to agent"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    data = request.get_json()
    ticket_id = data.get("ticket_id")
    agent_name = data.get("agent_name")
    
    db.assign_ticket_to_agent(ticket_id, agent_name)
    
    return jsonify({"success": True, "message": f"Ticket assigned to {agent_name} successfully"})

@app.route("/admin/agent_response", methods=["POST"])
def add_agent_response():
    """Add agent response to ticket"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    data = request.get_json()
    ticket_id = data.get("ticket_id")
    agent_id = data.get("agent_id")
    response_text = data.get("response_text")
    response_type = data.get("response_type", "Update")
    
    db.add_agent_response(ticket_id, agent_id, response_text, response_type)
    
    # Get ticket details to send notification to user
    ticket = db.get_ticket_details(ticket_id)
    agent = db.get_agent_by_id(agent_id)
    
    if ticket and agent:
        # Send notification to the user who created the ticket
        notification_system.create_notification(
            ticket['user_id'],
            f"New Response on Ticket #{ticket_id}",
            f"Agent {agent['name']} has responded to your ticket.",
            "success"
        )
        
        # Notify admins as well
        notification_system.create_admin_notification(
            f"Agent Response",
            f"Agent {agent['name']} has responded to ticket #{ticket_id}.",
            "info"
        )
    
    return jsonify({"success": True, "message": "Response added successfully"})

@app.route("/api/stats")
def api_stats():
    """API endpoint for dashboard statistics"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    stats = db.get_dashboard_stats()
    return jsonify(stats)

@app.route("/api/unassigned_tickets")
def api_unassigned_tickets():
    """API endpoint for unassigned tickets"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    # Get tickets without assigned agents
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ticket_id, title, category, priority, status, created_at
        FROM complaints 
        WHERE assigned_to IS NULL OR assigned_to = ''
        ORDER BY 
            CASE priority 
                WHEN 'Urgent' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
            END,
            created_at DESC
    ''')
    
    tickets = cursor.fetchall()
    conn.close()
    
    unassigned_tickets = [
        {
            'ticket_id': row[0],
            'title': row[1],
            'category': row[2],
            'priority': row[3],
            'status': row[4],
            'created_at': row[5]
        }
        for row in tickets
    ]
    
    return jsonify(unassigned_tickets)

@app.route("/api/export")
def api_export():
    """API endpoint for exporting ticket data"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    export_type = request.args.get('type', 'all')
    format_type = request.args.get('format', 'json')
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Build query based on export type
    if export_type == 'active':
        query = '''
            SELECT ticket_id, title, description, category, priority, status, 
                   assigned_to, created_at, updated_at, resolution_notes
            FROM complaints 
            WHERE status != 'Resolved'
            ORDER BY created_at DESC
        '''
    elif export_type == 'resolved':
        query = '''
            SELECT ticket_id, title, description, category, priority, status, 
                   assigned_to, created_at, updated_at, resolution_notes
            FROM complaints 
            WHERE status = 'Resolved'
            ORDER BY updated_at DESC
        '''
    else:  # all
        query = '''
            SELECT ticket_id, title, description, category, priority, status, 
                   assigned_to, created_at, updated_at, resolution_notes
            FROM complaints 
            ORDER BY created_at DESC
        '''
    
    cursor.execute(query)
    tickets = cursor.fetchall()
    conn.close()
    
    # Format data
    ticket_data = []
    for row in tickets:
        ticket_data.append({
            'ticket_id': row[0],
            'title': row[1],
            'description': row[2],
            'category': row[3],
            'priority': row[4],
            'status': row[5],
            'assigned_to': row[6] or 'Unassigned',
            'created_at': row[7],
            'updated_at': row[8],
            'resolution_notes': row[9] or 'N/A'
        })
    
    if format_type == 'csv':
        # Generate CSV content
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=ticket_data[0].keys() if ticket_data else [])
        writer.writeheader()
        writer.writerows(ticket_data)
        
        return jsonify({
            'success': True,
            'data': output.getvalue(),
            'filename': f'tickets_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'count': len(ticket_data)
        })
    
    return jsonify({
        'success': True,
        'data': ticket_data,
        'count': len(ticket_data),
        'export_type': export_type
    })

@app.route("/api/analytics/detailed")
def api_detailed_analytics():
    """API endpoint for detailed analytics"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get comprehensive analytics
    analytics = {}
    
    # Basic stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN status != 'Resolved' THEN 1 END) as active,
            COUNT(CASE WHEN status = 'Resolved' THEN 1 END) as resolved,
            COUNT(CASE WHEN assigned_to IS NULL OR assigned_to = '' THEN 1 END) as unassigned
        FROM complaints
    ''')
    basic_stats = cursor.fetchone()
    analytics['basic_stats'] = {
        'total_tickets': basic_stats[0],
        'active_tickets': basic_stats[1],
        'resolved_tickets': basic_stats[2],
        'unassigned_tickets': basic_stats[3]
    }
    
    # Priority distribution
    cursor.execute('''
        SELECT priority, COUNT(*) as count
        FROM complaints
        GROUP BY priority
        ORDER BY 
            CASE priority 
                WHEN 'Urgent' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
            END
    ''')
    priority_stats = dict(cursor.fetchall())
    analytics['priority_distribution'] = priority_stats
    
    # Category distribution
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM complaints
        GROUP BY category
        ORDER BY count DESC
    ''')
    category_stats = dict(cursor.fetchall())
    analytics['category_distribution'] = category_stats
    
    # Status distribution
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM complaints
        GROUP BY status
        ORDER BY count DESC
    ''')
    status_stats = dict(cursor.fetchall())
    analytics['status_distribution'] = status_stats
    
    # Agent workload
    cursor.execute('''
        SELECT 
            COALESCE(assigned_to, 'Unassigned') as agent,
            COUNT(*) as total_tickets,
            COUNT(CASE WHEN status != 'Resolved' THEN 1 END) as active_tickets,
            COUNT(CASE WHEN status = 'Resolved' THEN 1 END) as resolved_tickets
        FROM complaints
        GROUP BY assigned_to
        ORDER BY total_tickets DESC
    ''')
    agent_workload = []
    for row in cursor.fetchall():
        agent_workload.append({
            'agent': row[0],
            'total_tickets': row[1],
            'active_tickets': row[2],
            'resolved_tickets': row[3]
        })
    analytics['agent_workload'] = agent_workload
    
    # Recent activity (last 7 days)
    cursor.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM complaints
        WHERE created_at >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    ''')
    recent_activity = dict(cursor.fetchall())
    analytics['recent_activity'] = recent_activity
    
    # Average resolution time
    cursor.execute('''
        SELECT AVG(JULIANDAY(updated_at) - JULIANDAY(created_at)) as avg_resolution_days
        FROM complaints
        WHERE status = 'Resolved' AND updated_at IS NOT NULL
    ''')
    avg_resolution = cursor.fetchone()[0]
    analytics['avg_resolution_time'] = round(avg_resolution * 24, 2) if avg_resolution else 0  # Convert to hours
    
    conn.close()
    
    return jsonify({
        'success': True,
        'analytics': analytics,
        'generated_at': datetime.now().isoformat()
    })

@app.route("/api/agents/workload")
def api_agent_workload():
    """API endpoint for agent workload statistics"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    workload_stats = db.get_category_workload_stats()
    
    return jsonify({
        'success': True,
        'workload_stats': workload_stats
    })

@app.route("/api/tickets/reassign", methods=["POST"])
def api_reassign_ticket():
    """API endpoint for reassigning tickets"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    new_agent = data.get('new_agent')
    reason = data.get('reason', 'Manual reassignment by admin')
    
    if not ticket_id or not new_agent:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        db.reassign_ticket(ticket_id, new_agent, session['user_id'], reason)
        return jsonify({
            "success": True,
            "message": f"Ticket {ticket_id} reassigned to {new_agent}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tickets/auto-assign", methods=["POST"])
def api_auto_assign_tickets():
    """API endpoint for auto-assigning unassigned tickets"""
    if not session.get('is_admin'):
        return jsonify({"error": "Access denied"}), 403
    
    try:
        unassigned_tickets = db.get_unassigned_tickets()
        assigned_count = 0
        
        for ticket in unassigned_tickets:
            best_agent = db.get_best_agent_for_category(ticket['category'], ticket['priority'])
            if best_agent:
                db.reassign_ticket(ticket['ticket_id'], best_agent, session['user_id'], "Auto-assignment by system")
                assigned_count += 1
        
        return jsonify({
            "success": True,
            "message": f"Auto-assigned {assigned_count} tickets",
            "assigned_count": assigned_count,
            "total_unassigned": len(unassigned_tickets)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "system": "P-004 Complaint Management System",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

# Notification API endpoints
@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    """Get notifications for the current user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
        
    limit = request.args.get('limit', 20, type=int)
    only_unread = request.args.get('unread', False, type=bool)
    
    notifications = notification_system.get_notifications(
        session['user_id'], 
        limit=limit, 
        only_unread=only_unread
    )
    
    return jsonify({
        "notifications": notifications,
        "unread_count": notification_system.get_unread_count(session['user_id'])
    })

@app.route("/api/notifications/unread-count", methods=["GET"])
def get_unread_count():
    """Get the number of unread notifications for the current user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    count = notification_system.get_unread_count(session['user_id'])
    return jsonify({"count": count})

@app.route("/api/notifications/<notification_id>/read", methods=["PUT"])
def mark_as_read(notification_id):
    """Mark a notification as read"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    notification_system.mark_as_read(notification_id)
    return jsonify({"success": True})

@app.route("/api/notifications/mark-all-read", methods=["PUT"])
def mark_all_as_read():
    """Mark all notifications as read for the current user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    notification_system.mark_all_as_read(session['user_id'])
    return jsonify({"success": True})

@app.route("/api/notifications/<notification_id>", methods=["DELETE"])
def delete_notification(notification_id):
    """Delete a specific notification"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    notification_system.delete_notification(notification_id)
    return jsonify({"success": True})

# Update existing endpoints to create notifications
@app.route("/admin/update_ticket", methods=["POST"])
def update_ticket():
    """Update ticket status or assignment"""
    if 'user_id' not in session or not session.get('is_admin', False):
        return jsonify({"error": "Not authorized"}), 403
    
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    new_status = data.get('status')
    assigned_to = data.get('assigned_to')
    
    if not ticket_id:
        return jsonify({"error": "Ticket ID is required"}), 400
    
    try:
        # Get ticket info to send proper notifications
        ticket = db.get_ticket_details(ticket_id)
        if not ticket:
            return jsonify({"error": "Ticket not found"}), 404
        
        # Update the ticket
        if new_status:
            db.update_ticket_status(ticket_id, new_status)
            
            # Send notification to customer
            notification_system.create_notification(
                ticket['user_id'],
                f"Ticket Status Update",
                f"Your ticket #{ticket_id} has been updated to {new_status}.",
                "info"
            )
            
            # Send notification to all admins
            notification_system.create_admin_notification(
                f"Ticket Status Changed",
                f"Ticket #{ticket_id} status changed to {new_status} by {session['full_name']}",
                "info"
            )
            
            # If assigned to an agent, notify them too
            if ticket['assigned_to']:
                agent = db.get_agent_by_name(ticket['assigned_to'])
                if agent:
                    notification_system.create_agent_notification(
                        agent['id'],
                        f"Ticket Status Changed",
                        f"Ticket #{ticket_id} status changed to {new_status} by admin {session['full_name']}",
                        "info"
                    )
                    
        if assigned_to:
            previous_agent = ticket.get('assigned_to')
            db.assign_ticket(ticket_id, assigned_to)
            
            # Notify the newly assigned agent
            new_agent = db.get_agent_by_name(assigned_to)
            if new_agent:
                notification_system.create_agent_notification(
                    new_agent['id'],
                    "New Ticket Assignment",
                    f"Ticket #{ticket_id} has been assigned to you.",
                    "info"
                )
            
            # Notify admins
            notification_system.create_admin_notification(
                "Ticket Assignment",
                f"Ticket #{ticket_id} reassigned from {previous_agent or 'Unassigned'} to {assigned_to}",
                "info"
            )
            
            # Notify customer
            notification_system.create_notification(
                ticket['user_id'],
                f"Ticket Assigned",
                f"Your ticket #{ticket_id} has been assigned to agent {assigned_to}.",
                "info"
            )
            
        return jsonify({
            "success": True,
            "message": "Ticket updated successfully"
        })
    except Exception as e:
        print(f"Error updating ticket: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
