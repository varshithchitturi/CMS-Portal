import os
import re
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle
import uuid

load_dotenv()

class GeminiChatbot:
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Configure generation settings for better responses
        self.generation_config = genai.types.GenerationConfig(
            max_output_tokens=8192,
            temperature=0.7,
            top_p=0.8,
            top_k=40
        )
        
        self.model = genai.GenerativeModel(
            "gemini-2.0-flash-exp",
            generation_config=self.generation_config
        )
        
        # Initialize advanced features
        self.init_ml_classifier()
        self.init_sentiment_analyzer()
        self.init_knowledge_base()
        self.conversation_memory = {}
        
        # Enhanced resolution database with follow-up questions
        self.common_resolutions = {
            "password reset": {
                "solution": "To reset your password, go to the login page and click 'Forgot Password'. You'll receive an email with reset instructions.",
                "follow_up": "Have you checked your spam folder for the reset email?",
                "escalation_time": 300  # 5 minutes
            },
            "account locked": {
                "solution": "Your account appears to be locked. This usually happens after multiple failed login attempts. Please wait 30 minutes or contact support.",
                "follow_up": "How long ago did you last try to log in?",
                "escalation_time": 600  # 10 minutes
            },
            "billing question": {
                "solution": "For billing inquiries, please check your account dashboard or contact our billing department at billing@support.com",
                "follow_up": "Are you looking for a specific transaction or general billing information?",
                "escalation_time": 480  # 8 minutes
            },
            "service outage": {
                "solution": "We're aware of the service outage and our technical team is working to resolve it. Expected resolution time is 2-4 hours.",
                "follow_up": "Which specific service are you unable to access?",
                "escalation_time": 120  # 2 minutes - high priority
            },
            "technical issue": {
                "solution": "For technical issues, please try clearing your browser cache and cookies. If the problem persists, please provide more details.",
                "follow_up": "What browser are you using and when did this issue start?",
                "escalation_time": 600  # 10 minutes
            },
            "refund request": {
                "solution": "Refund requests are processed within 5-7 business days. Please provide your order number for faster processing.",
                "follow_up": "Do you have your order number available?",
                "escalation_time": 720  # 12 minutes
            }
        }
    
    def init_ml_classifier(self):
        """Initialize enhanced ML classifier for complaint categorization"""
        # Expanded training data with more examples
        training_data = [
            # Technical Issues
            ("My internet is not working", "Technical"),
            ("I can't log into my account", "Technical"),
            ("Website keeps crashing", "Technical"),
            ("App won't load", "Technical"),
            ("Getting error messages", "Technical"),
            ("Connection timeout", "Technical"),
            ("Can't access my dashboard", "Technical"),
            ("System is down", "Technical"),
            ("Login page not responding", "Technical"),
            ("Two-factor authentication not working", "Technical"),
            
            # Billing Issues
            ("Wrong amount charged on my bill", "Billing"),
            ("Need refund for cancelled service", "Billing"),
            ("Double charged for same service", "Billing"),
            ("Payment not processed", "Billing"),
            ("Invoice is incorrect", "Billing"),
            ("Subscription renewal issue", "Billing"),
            ("Credit card declined", "Billing"),
            ("Billing cycle questions", "Billing"),
            ("Want to update payment method", "Billing"),
            ("Unauthorized charges", "Billing"),
            
            # Service Issues
            ("Poor customer service experience", "Service"),
            ("Rude staff behavior", "Service"),
            ("Long wait times", "Service"),
            ("Representative was unhelpful", "Service"),
            ("Not satisfied with service quality", "Service"),
            ("Response time too slow", "Service"),
            ("Lack of communication", "Service"),
            ("Unprofessional behavior", "Service"),
            
            # Product Issues
            ("Product defect or damage", "Product"),
            ("Missing features in product", "Product"),
            ("Product doesn't work as advertised", "Product"),
            ("Quality issues with product", "Product"),
            ("Product arrived damaged", "Product"),
            ("Wrong product delivered", "Product"),
            ("Product stopped working", "Product"),
            ("Missing parts", "Product"),
            
            # General Inquiries
            ("General inquiry about services", "General"),
            ("How to use this feature", "General"),
            ("Need information about pricing", "General"),
            ("Want to know about new features", "General"),
            ("Question about account settings", "General"),
            ("How to contact support", "General"),
            ("General feedback", "General")
        ]
        
        # Prepare training data
        texts = [item[0] for item in training_data]
        categories = [item[1] for item in training_data]
        
        # Train the classifier with improved parameters
        self.vectorizer = TfidfVectorizer(
            stop_words='english', 
            lowercase=True, 
            ngram_range=(1, 2),  # Include bigrams
            max_features=1000
        )
        X = self.vectorizer.fit_transform(texts)
        
        self.classifier = MultinomialNB(alpha=0.1)
        self.classifier.fit(X, categories)
    
    def init_sentiment_analyzer(self):
        """Initialize sentiment analysis capabilities"""
        self.sentiment_keywords = {
            "positive": ["happy", "satisfied", "great", "excellent", "good", "pleased", "thank"],
            "negative": ["angry", "frustrated", "disappointed", "terrible", "awful", "hate", "worst"],
            "urgent": ["urgent", "emergency", "asap", "immediately", "critical", "severe", "urgent"],
            "neutral": ["question", "inquiry", "information", "help", "assistance"]
        }
    
    def init_knowledge_base(self):
        """Initialize comprehensive knowledge base"""
        self.knowledge_base = {
            "account_management": {
                "password_reset": "Visit login page → Click 'Forgot Password' → Check email for reset link",
                "account_locked": "Wait 30 minutes for auto-unlock or contact support",
                "profile_update": "Go to Settings → Profile → Edit information → Save changes",
                "two_factor_auth": "Settings → Security → Enable 2FA → Follow setup instructions"
            },
            "billing_help": {
                "payment_methods": "Accepted: Credit/Debit cards, PayPal, Bank transfer",
                "billing_cycle": "Monthly billing on signup date, annual discounts available",
                "refund_policy": "Full refund within 30 days, prorated refunds after",
                "invoice_download": "Account → Billing → Download Invoice"
            },
            "technical_support": {
                "browser_issues": "Clear cache, disable extensions, try incognito mode",
                "mobile_app": "Update app, restart device, reinstall if needed",
                "connectivity": "Check internet connection, try different network",
                "performance": "Close other apps, restart browser, check system resources"
            },
            "service_info": {
                "support_hours": "24/7 chat support, phone support 9 AM - 6 PM",
                "response_times": "Chat: immediate, Email: 24 hours, Phone: 2 minutes",
                "escalation": "Supervisor available for complex issues",
                "feedback": "feedback@intellisupport.ai for suggestions"
            }
        }
    
    def analyze_sentiment(self, text):
        """Advanced sentiment analysis"""
        text_lower = text.lower()
        scores = {"positive": 0, "negative": 0, "urgent": 0, "neutral": 0}
        
        for sentiment, keywords in self.sentiment_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[sentiment] += 1
        
        # Determine dominant sentiment
        dominant_sentiment = max(scores.items(), key=lambda x: x[1])
        
        # Calculate intensity
        total_keywords = sum(scores.values())
        intensity = "high" if total_keywords >= 3 else "medium" if total_keywords >= 1 else "low"
        
        return {
            "sentiment": dominant_sentiment[0],
            "intensity": intensity,
            "scores": scores
        }
    
    def get_conversation_context(self, session_id):
        """Retrieve conversation context for better responses"""
        if session_id not in self.conversation_memory:
            self.conversation_memory[session_id] = {
                "messages": [],
                "start_time": datetime.now(),
                "user_sentiment": "neutral",
                "issue_category": None,
                "resolution_attempts": 0,
                "escalation_level": 0
            }
        return self.conversation_memory[session_id]
    
    def update_conversation_context(self, session_id, user_message, bot_response, sentiment_analysis):
        """Update conversation context with new interaction"""
        context = self.get_conversation_context(session_id)
        
        context["messages"].append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": datetime.now(),
            "sentiment": sentiment_analysis
        })
        
        # Update user sentiment trend
        context["user_sentiment"] = sentiment_analysis["sentiment"]
        
        # Increment resolution attempts if bot provided a solution
        if any(keyword in bot_response.lower() for keyword in ["try", "solution", "resolve", "fix"]):
            context["resolution_attempts"] += 1
        
        # Keep only last 10 messages for performance
        context["messages"] = context["messages"][-10:]
        
        return context
    
    def categorize_complaint(self, complaint_text):
        """Enhanced complaint categorization using ML with confidence scoring"""
        try:
            X = self.vectorizer.transform([complaint_text])
            category = self.classifier.predict(X)[0]
            probabilities = self.classifier.predict_proba(X)[0]
            confidence = max(probabilities)
            
            return {
                "category": category,
                "confidence": confidence,
                "all_probabilities": dict(zip(self.classifier.classes_, probabilities))
            }
        except:
            return {
                "category": "General",
                "confidence": 0.5,
                "all_probabilities": {}
            }
    
    def search_knowledge_base(self, query):
        """Search knowledge base for relevant solutions"""
        query_lower = query.lower()
        relevant_solutions = []
        
        for category, solutions in self.knowledge_base.items():
            for issue, solution in solutions.items():
                if any(word in query_lower for word in issue.split('_')):
                    relevant_solutions.append({
                        "category": category,
                        "issue": issue,
                        "solution": solution,
                        "relevance": len([word for word in issue.split('_') if word in query_lower])
                    })
        
        # Sort by relevance
        return sorted(relevant_solutions, key=lambda x: x["relevance"], reverse=True)[:3]
    
    def extract_priority(self, text):
        """Extract priority from complaint text using keywords"""
        text_lower = text.lower()
        
        urgent_keywords = ["urgent", "emergency", "critical", "asap", "immediately", "outage", "down", "not working"]
        high_keywords = ["important", "serious", "major", "significant", "problem", "issue"]
        medium_keywords = ["concern", "question", "help", "assistance", "support"]
        
        if any(keyword in text_lower for keyword in urgent_keywords):
            return "Urgent"
        elif any(keyword in text_lower for keyword in high_keywords):
            return "High"
        elif any(keyword in text_lower for keyword in medium_keywords):
            return "Medium"
        else:
            return "Low"
    
    def check_common_resolution(self, user_message):
        """Check if the complaint can be resolved with common solutions"""
        message_lower = user_message.lower()
        
        for issue, resolution in self.common_resolutions.items():
            if issue in message_lower:
                return resolution
        return None
    
    def extract_complaint_details(self, user_message):
        """Extract complaint details from user message"""
        # Use Gemini to extract structured information
        prompt = f"""
        Analyze this user message and extract complaint details in this exact JSON format:
        {{
            "title": "Brief title of the complaint",
            "description": "Detailed description",
            "has_resolution": true/false,
            "resolution": "If has_resolution is true, provide resolution, otherwise empty string"
        }}
        
        User message: {user_message}
        
        Return only the JSON, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            import json
            json_start = response.text.find('{')
            json_end = response.text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response.text[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback extraction
        return {
            "title": user_message[:50] + "..." if len(user_message) > 50 else user_message,
            "description": user_message,
            "has_resolution": False,
            "resolution": ""
        }
    
    def chat_with_bot(self, user_message, user_id=None, session_id=None):
        """Enhanced main chatbot function with advanced AI capabilities"""
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get conversation context
        context = self.get_conversation_context(session_id)
        
        # Analyze sentiment
        sentiment_analysis = self.analyze_sentiment(user_message)
        
        # Categorize the complaint
        categorization = self.categorize_complaint(user_message)
        
        # Search knowledge base for relevant solutions
        knowledge_solutions = self.search_knowledge_base(user_message)
        
        # Check for escalation conditions
        should_escalate = self.should_escalate(context, sentiment_analysis, user_message)
        
        # Build context for AI response
        conversation_history = ""
        if context["messages"]:
            recent_messages = context["messages"][-3:]  # Last 3 exchanges
            conversation_history = "\n".join([
                f"User: {msg['user']}\nBot: {msg['bot']}" 
                for msg in recent_messages
            ])
        
        # Check for common resolutions first
        common_resolution = self.check_common_resolution(user_message)
        
        if common_resolution and context["resolution_attempts"] == 0:
            resolution_data = self.common_resolutions[self.find_matching_issue(user_message)]
            
            response = f"""
            🤖 **IntelliSupport AI**: I understand your concern and I'm here to help!
            
            **💡 Quick Solution**: {resolution_data['solution']}
            
            **🔍 Follow-up**: {resolution_data['follow_up']}
            
            Did this help resolve your issue? If you're still experiencing problems, I'll escalate this to our specialist team.
            """
            
            bot_response = response
            requires_ticket = False
            
        elif should_escalate:
            bot_response = self.generate_escalation_response(context, sentiment_analysis)
            requires_ticket = True
            
        else:
            # Use advanced Gemini processing
            bot_response = self.generate_advanced_response(
                user_message, 
                context, 
                sentiment_analysis, 
                categorization, 
                knowledge_solutions,
                conversation_history
            )
            
            # Determine if ticket is required
            requires_ticket = self.determine_ticket_requirement(
                user_message, 
                bot_response, 
                context, 
                sentiment_analysis
            )
        
        # Update conversation context
        updated_context = self.update_conversation_context(
            session_id, user_message, bot_response, sentiment_analysis
        )
        
        return {
            "response": bot_response,
            "session_id": session_id,
            "requires_ticket": requires_ticket,
            "resolution_provided": not requires_ticket,
            "sentiment": sentiment_analysis["sentiment"],
            "category": categorization["category"],
            "confidence": categorization["confidence"],
            "escalation_level": updated_context["escalation_level"]
        }
    
    def find_matching_issue(self, user_message):
        """Find the matching issue key for common resolutions"""
        message_lower = user_message.lower()
        for issue in self.common_resolutions.keys():
            if issue in message_lower:
                return issue
        return "technical issue"  # Default fallback
    
    def should_escalate(self, context, sentiment_analysis, user_message):
        """Determine if conversation should be escalated"""
        # Escalate if negative sentiment with high intensity
        if sentiment_analysis["sentiment"] == "negative" and sentiment_analysis["intensity"] == "high":
            return True
        
        # Escalate if multiple resolution attempts failed
        if context["resolution_attempts"] >= 3:
            return True
        
        # Escalate if conversation is going on too long
        if len(context["messages"]) >= 8:
            return True
        
        # Escalate for urgent keywords
        if sentiment_analysis["sentiment"] == "urgent":
            return True
        
        return False
    
    def generate_escalation_response(self, context, sentiment_analysis):
        """Generate appropriate escalation response"""
        if sentiment_analysis["sentiment"] == "negative":
            return """
            🤖 **IntelliSupport AI**: I understand your frustration, and I sincerely apologize for the inconvenience you've experienced.
            
            Given the complexity of your issue, I'm escalating this to our specialist support team who can provide more detailed assistance.
            
            **⚡ Next Steps:**
            - A support ticket will be created immediately
            - You'll receive a ticket number for tracking
            - Our specialist will contact you within 2 hours
            - Priority support will be provided
            
            Thank you for your patience as we work to resolve this matter quickly.
            """
        else:
            return """
            🤖 **IntelliSupport AI**: I want to make sure you get the best possible help for your issue.
            
            I'm connecting you with our specialist support team who have advanced tools and expertise to assist you.
            
            **📋 What happens next:**
            - A detailed support ticket will be created
            - Our specialist will review your case
            - You'll receive personalized assistance
            - Resolution timeline will be provided
            """
    
    def generate_advanced_response(self, user_message, context, sentiment_analysis, categorization, knowledge_solutions, conversation_history):
        """Generate advanced AI response using Gemini with rich context"""
        
        # Build context-aware prompt
        sentiment_context = f"User sentiment: {sentiment_analysis['sentiment']} (intensity: {sentiment_analysis['intensity']})"
        category_context = f"Issue category: {categorization['category']} (confidence: {categorization['confidence']:.2f})"
        
        knowledge_context = ""
        if knowledge_solutions:
            knowledge_context = "Relevant solutions from knowledge base:\n"
            for sol in knowledge_solutions[:2]:
                knowledge_context += f"- {sol['issue']}: {sol['solution']}\n"
        
        conversation_context = ""
        if conversation_history:
            conversation_context = f"Previous conversation:\n{conversation_history}\n"
        
        prompt = f"""
        You are IntelliSupport AI, an advanced customer service chatbot for a complaint management system.
        
        **Context Information:**
        {sentiment_context}
        {category_context}
        
        **Knowledge Base Solutions:**
        {knowledge_context}
        
        **Conversation History:**
        {conversation_context}
        
        **Current User Message:** {user_message}
        
        **Instructions:**
        1. Be empathetic and professional, especially if user seems frustrated
        2. Reference previous conversation if relevant
        3. Provide specific, actionable solutions
        4. Use knowledge base information when applicable
        5. If you cannot fully resolve the issue, indicate ticket creation is needed with "TICKET_REQUIRED"
        6. Ask follow-up questions to better understand complex issues
        7. Be concise but thorough
        
        **Response Style:**
        - Use professional but friendly tone
        - Include relevant emojis for better engagement
        - Structure response with clear sections if providing multiple solutions
        - Show empathy for user's situation
        
        Respond now:
        """
        
        try:
            response = self.model.generate_content(prompt)
            bot_response = response.text.strip()
            
            # Clean up the response
            bot_response = bot_response.replace("TICKET_REQUIRED", "").strip()
            
            return bot_response
            
        except Exception as e:
            return f"""
            🤖 **IntelliSupport AI**: I apologize, but I'm experiencing a temporary technical issue while processing your request.
            
            To ensure you receive the help you need, I'll create a support ticket for you right away. Our technical team will review your case and provide a solution.
            
            **Error Reference:** {str(e)[:50]}...
            """
    
    def determine_ticket_requirement(self, user_message, bot_response, context, sentiment_analysis):
        """Intelligent determination of ticket requirement"""
        
        # Always require ticket for high-priority or urgent issues
        if sentiment_analysis["sentiment"] == "urgent":
            return True
        
        # Require ticket if bot couldn't provide specific solution
        solution_indicators = ["try", "solution", "steps", "fix", "resolve", "here's how"]
        if not any(indicator in bot_response.lower() for indicator in solution_indicators):
            return True
        
        # Require ticket if user has been trying to resolve for a while
        if context["resolution_attempts"] >= 2:
            return True
        
        # Require ticket for complex technical issues
        if "technical" in self.categorize_complaint(user_message)["category"].lower():
            complexity_keywords = ["error code", "crashed", "corrupted", "malfunction", "bug"]
            if any(keyword in user_message.lower() for keyword in complexity_keywords):
                return True
        
        # Check if bot response mentions ticket creation
        if "TICKET_REQUIRED" in bot_response or "create a ticket" in bot_response.lower():
            return True
        
        return False
    
    def generate_ticket_summary(self, user_message, chat_history=None, sentiment_analysis=None, categorization=None):
        """Generate a comprehensive and intelligent ticket summary"""
        context = ""
        if chat_history:
            context = "\n".join([f"User: {h['message']}\nBot: {h['response']}" for h in chat_history[-3:]])
        
        # Add sentiment and categorization context if available
        additional_context = ""
        if sentiment_analysis:
            additional_context += f"User Sentiment: {sentiment_analysis['sentiment']} (intensity: {sentiment_analysis['intensity']})\n"
        
        if categorization:
            additional_context += f"AI Classification: {categorization['category']} (confidence: {categorization['confidence']:.2f})\n"
        
        prompt = f"""
        You are creating a detailed support ticket based on customer interaction. Be thorough and professional.
        
        **Conversation Context:** 
        {context}
        
        **Current Issue:** {user_message}
        
        **AI Analysis:**
        {additional_context}
        
        **Task:** Create a comprehensive support ticket with the following:
        
        1. **Title**: Clear, concise summary (max 60 characters)
        2. **Description**: Detailed explanation including:
           - What the customer is experiencing
           - Any steps they may have already tried
           - Impact on their work/experience
           - Any error messages or specific details
        3. **Category**: Choose from Technical, Billing, Service, Product, or General
        4. **Priority**: Determine based on:
           - Urgency of the issue
           - Impact on customer
           - Business criticality
           - Customer sentiment
           Choose from: Critical, High, Medium, Low
        5. **Suggested Resolution Time**: Estimate based on complexity
        6. **Required Expertise**: What type of specialist should handle this
        
        **Format your response exactly as:**
        TITLE: [title]
        DESCRIPTION: [description]
        CATEGORY: [category]  
        PRIORITY: [priority]
        RESOLUTION_TIME: [time estimate]
        EXPERTISE: [required specialist type]
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self.parse_enhanced_ticket_summary(response.text, user_message, categorization)
        except Exception as e:
            # Enhanced fallback processing
            fallback_category = categorization["category"] if categorization else self.categorize_complaint(user_message)["category"]
            fallback_priority = self.extract_priority(user_message)
            
            return {
                "title": user_message[:50] + "..." if len(user_message) > 50 else user_message,
                "description": f"Customer Issue: {user_message}\n\nAdditional Context: Generated automatically due to AI processing error.",
                "category": fallback_category,
                "priority": fallback_priority,
                "resolution_time": "24 hours",
                "expertise": "General Support",
                "ai_confidence": categorization["confidence"] if categorization else 0.5
            }
    
    def parse_enhanced_ticket_summary(self, response_text, user_message, categorization):
        """Parse the enhanced ticket summary from Gemini response"""
        lines = response_text.split('\n')
        result = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('TITLE:'):
                result['title'] = line.replace('TITLE:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                result['description'] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('CATEGORY:'):
                result['category'] = line.replace('CATEGORY:', '').strip()
            elif line.startswith('PRIORITY:'):
                result['priority'] = line.replace('PRIORITY:', '').strip()
            elif line.startswith('RESOLUTION_TIME:'):
                result['resolution_time'] = line.replace('RESOLUTION_TIME:', '').strip()
            elif line.startswith('EXPERTISE:'):
                result['expertise'] = line.replace('EXPERTISE:', '').strip()
        
        # Validate and set defaults
        valid_categories = ["Technical", "Billing", "Service", "Product", "General"]
        valid_priorities = ["Critical", "High", "Medium", "Low"]
        
        if result.get('category') not in valid_categories:
            result['category'] = categorization["category"] if categorization else "General"
        
        if result.get('priority') not in valid_priorities:
            result['priority'] = self.extract_priority(user_message)
        
        # Set defaults for new fields
        if not result.get('resolution_time'):
            result['resolution_time'] = self.estimate_resolution_time(result.get('priority', 'Medium'))
        
        if not result.get('expertise'):
            result['expertise'] = self.determine_required_expertise(result.get('category', 'General'))
        
        # Add confidence score
        result['ai_confidence'] = categorization["confidence"] if categorization else 0.7
        
        return result
    
    def estimate_resolution_time(self, priority):
        """Estimate resolution time based on priority"""
        time_estimates = {
            "Critical": "2-4 hours",
            "High": "4-8 hours", 
            "Medium": "1-2 business days",
            "Low": "3-5 business days"
        }
        return time_estimates.get(priority, "1-2 business days")
    
    def determine_required_expertise(self, category):
        """Determine required expertise based on category"""
        expertise_mapping = {
            "Technical": "Technical Support Specialist",
            "Billing": "Billing Department Specialist", 
            "Service": "Customer Success Manager",
            "Product": "Product Support Expert",
            "General": "General Support Agent"
        }
        return expertise_mapping.get(category, "General Support Agent")

    def parse_ticket_summary(self, response_text):
        """Legacy parsing method for backward compatibility"""
        lines = response_text.split('\n')
        result = {}
        
        for line in lines:
            if line.startswith('TITLE:'):
                result['title'] = line.replace('TITLE:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                result['description'] = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('CATEGORY:'):
                result['category'] = line.replace('CATEGORY:', '').strip()
            elif line.startswith('PRIORITY:'):
                result['priority'] = line.replace('PRIORITY:', '').strip()
        
        # Validate categories and priorities
        valid_categories = ["Technical", "Billing", "Service", "Product", "General"]
        valid_priorities = ["Urgent", "High", "Medium", "Low"]
        
        if result.get('category') not in valid_categories:
            result['category'] = "General"
        
        if result.get('priority') not in valid_priorities:
            result['priority'] = "Medium"
        
        return result

# Initialize the enhanced chatbot
chatbot = GeminiChatbot()
