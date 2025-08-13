"""
Agent Management System with Category Assignment
"""

class AgentManager:
    def __init__(self):
        # Define 5 agents with their specializations
        self.agents = {
            "john_doe": {
                "name": "John Doe",
                "email": "john.doe@intellisupport.ai",
                "specialization": "Technical",
                "categories": ["Technical"],
                "active": True,
                "current_workload": 0,
                "max_workload": 10
            },
            "jane_smith": {
                "name": "Jane Smith", 
                "email": "jane.smith@intellisupport.ai",
                "specialization": "Billing",
                "categories": ["Billing"],
                "active": True,
                "current_workload": 0,
                "max_workload": 10
            },
            "mike_johnson": {
                "name": "Mike Johnson",
                "email": "mike.johnson@intellisupport.ai", 
                "specialization": "Service",
                "categories": ["Service"],
                "active": True,
                "current_workload": 0,
                "max_workload": 10
            },
            "sarah_wilson": {
                "name": "Sarah Wilson",
                "email": "sarah.wilson@intellisupport.ai",
                "specialization": "Product",
                "categories": ["Product"],
                "active": True,
                "current_workload": 0,
                "max_workload": 10
            },
            "alex_brown": {
                "name": "Alex Brown",
                "email": "alex.brown@intellisupport.ai",
                "specialization": "General Support",
                "categories": ["General", "Pending"],
                "active": True,
                "current_workload": 0,
                "max_workload": 15  # Can handle more since general support
            }
        }
        
        # Category mapping
        self.category_agents = {
            "Technical": ["john_doe"],
            "Billing": ["jane_smith"],
            "Service": ["mike_johnson"],
            "Product": ["sarah_wilson"],
            "General": ["alex_brown"],
            "Pending": ["alex_brown"]  # Handles unassigned/pending issues
        }
    
    def auto_assign_agent(self, category, priority="Medium"):
        """
        Automatically assign the best available agent for a category
        """
        available_agents = self.category_agents.get(category, self.category_agents["General"])
        
        # Filter active agents and sort by workload
        best_agent = None
        min_workload = float('inf')
        
        for agent_id in available_agents:
            agent = self.agents[agent_id]
            if agent["active"] and agent["current_workload"] < agent["max_workload"]:
                if agent["current_workload"] < min_workload:
                    min_workload = agent["current_workload"]
                    best_agent = agent_id
        
        # If no specialized agent available, try general support
        if not best_agent and category != "General":
            general_agents = self.category_agents["General"]
            for agent_id in general_agents:
                agent = self.agents[agent_id]
                if agent["active"] and agent["current_workload"] < agent["max_workload"]:
                    best_agent = agent_id
                    break
        
        if best_agent:
            self.agents[best_agent]["current_workload"] += 1
            return {
                "agent_id": best_agent,
                "agent_name": self.agents[best_agent]["name"],
                "agent_email": self.agents[best_agent]["email"],
                "specialization": self.agents[best_agent]["specialization"]
            }
        
        # If all agents are busy, assign to the one with least workload
        fallback_agent = min(self.agents.items(), 
                           key=lambda x: x[1]["current_workload"] if x[1]["active"] else float('inf'))
        
        if fallback_agent:
            agent_id, agent_data = fallback_agent
            agent_data["current_workload"] += 1
            return {
                "agent_id": agent_id,
                "agent_name": agent_data["name"],
                "agent_email": agent_data["email"],
                "specialization": agent_data["specialization"]
            }
        
        return None
    
    def get_agent_workload(self):
        """Get current workload for all agents"""
        workload = {}
        for agent_id, agent_data in self.agents.items():
            workload[agent_id] = {
                "name": agent_data["name"],
                "specialization": agent_data["specialization"],
                "current_workload": agent_data["current_workload"],
                "max_workload": agent_data["max_workload"],
                "availability": agent_data["max_workload"] - agent_data["current_workload"],
                "active": agent_data["active"]
            }
        return workload
    
    def reassign_ticket(self, ticket_id, new_agent_id, old_agent_id=None):
        """Reassign a ticket to a different agent"""
        if old_agent_id and old_agent_id in self.agents:
            self.agents[old_agent_id]["current_workload"] = max(0, 
                self.agents[old_agent_id]["current_workload"] - 1)
        
        if new_agent_id in self.agents:
            self.agents[new_agent_id]["current_workload"] += 1
            return True
        return False
    
    def update_agent_status(self, agent_id, active_status):
        """Update agent active status"""
        if agent_id in self.agents:
            self.agents[agent_id]["active"] = active_status
            return True
        return False
    
    def get_agents_by_category(self, category):
        """Get all agents who can handle a specific category"""
        agent_ids = self.category_agents.get(category, [])
        return [
            {
                "agent_id": agent_id,
                "name": self.agents[agent_id]["name"],
                "specialization": self.agents[agent_id]["specialization"],
                "active": self.agents[agent_id]["active"],
                "workload": self.agents[agent_id]["current_workload"]
            }
            for agent_id in agent_ids
        ]

# Global agent manager instance
agent_manager = AgentManager()
