from core.base_agent import BaseAgent
from typing import Dict, Any

class ConversationalAgent(BaseAgent):
    """Main conversational agent"""
    
    def __init__(self):
        super().__init__(name="conversational_agent", model="gemini-2.5-flash")
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process conversation"""
        message = input_data.get("message", "")
        context = input_data.get("context", {})
        
        # Build prompt with context
        prompt = self._build_prompt(message, context)
        
        # Generate response
        response = await self.think(prompt)
        
        return {
            "text": response,
            "metadata": {"agent": self.name}
        }
    
    def _build_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """Build prompt with context"""
        prompt = f"User: {message}\n"
        
        if context.get("history"):
            prompt = "Previous conversation:\n"
            for entry in context["history"][-5:]:  # Last 5 messages
                prompt += f"{entry}\n"
            prompt += f"\nUser: {message}\n"
            
        return prompt