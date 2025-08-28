from typing import Dict, Any, List, Optional
import asyncio
from core.base_agent import BaseAgent
from core.mcp_protocol import MCPProtocol

class ChatManager:
    """Manages multiple agents and orchestrates conversations"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.mcp_protocol = MCPProtocol()
        self.conversation_state = {}
        self.active_agents = []
        
    def register_agent(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.name] = agent
        
    async def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user message through appropriate agents"""
        # Determine which agents to activate
        activated_agents = await self._select_agents(message, context)
        
        # Process through agents
        responses = []
        for agent_name in activated_agents:
            agent = self.agents[agent_name]
            response = await agent.process({
                "message": message,
                "context": context,
                "state": self.conversation_state
            })
            responses.append(response)
            
        # Combine responses
        final_response = await self._combine_responses(responses)
        
        # Update conversation state
        self.conversation_state["last_message"] = message
        self.conversation_state["last_response"] = final_response
        
        return final_response
    
    async def _select_agents(self, message: str, context: Dict[str, Any]) -> List[str]:
        """Select appropriate agents based on message content"""
        agents_to_activate = []
        
        # Analyze message for agent activation
        if any(keyword in message.lower() for keyword in ['image', 'picture', 'generate', 'create']):
            agents_to_activate.append('image_agent')
            
        if any(keyword in message.lower() for keyword in ['search', 'find', 'research', 'web']):
            agents_to_activate.append('research_agent')
            
        if context.get('files'):
            agents_to_activate.append('file_agent')
            
        if any(keyword in message.lower() for keyword in ['speak', 'say', 'voice', 'audio']):
            agents_to_activate.append('speech_agent')
            
        # Always include conversational agent
        if 'conversational_agent' not in agents_to_activate:
            agents_to_activate.append('conversational_agent')
            
        return agents_to_activate
    
    async def _combine_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine multiple agent responses"""
        combined = {
            "text": "",
            "images": [],
            "audio": [],
            "files": [],
            "metadata": {}
        }
        
        for response in responses:
            if response.get("text"):
                combined["text"] += response["text"] + "\n"
            if response.get("images"):
                combined["images"].extend(response["images"])
            if response.get("audio"):
                combined["audio"].extend(response["audio"])
            if response.get("files"):
                combined["files"].extend(response["files"])
            if response.get("metadata"):
                combined["metadata"].update(response["metadata"])
                
        return combined