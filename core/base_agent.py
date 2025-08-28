from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from config.settings import config

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str, model: str = None, temperature: float = 0.7):
        self.name = name
        self.model = model or config.DEFAULT_MODEL
        self.temperature = temperature
        self.conversation_history = []
        self.tools = []
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the Gemini model"""
        self.llm = genai.GenerativeModel(
            model_name=self.model,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": config.MAX_TOKENS,
            }
        )
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return response"""
        pass
    
    def add_tool(self, tool):
        """Add a tool to the agent"""
        self.tools.append(tool)
        
    async def think(self, prompt: str) -> str:
        """Generate response using LLM"""
        response = await self.llm.generate_content_async(prompt)
        return response.text