import asyncio
from core.chat_manager import ChatManager
from agents.conversational_agent import ConversationalAgent
from agents.image_agent import ImageAgent
from agents.research_agent import ResearchAgent
from agents.file_agent import FileAgent
from agents.speech_agent import SpeechAgent
from config.settings import config
from typing import Dict, Any
class MultiAgentChatbot:
    """Main chatbot application"""
    
    def __init__(self):
        self.chat_manager = ChatManager()
        self._initialize_agents()
        
    def _initialize_agents(self):
        """Initialize and register all agents"""
        agents = [
            ConversationalAgent(),
            ImageAgent(),
            ResearchAgent(),
            FileAgent(),
            SpeechAgent()
        ]
        
        for agent in agents:
            self.chat_manager.register_agent(agent)
            print(f"Registered agent: {agent.name}")
            
    async def chat(self, message: str, context: Dict = None) -> Dict:
        """Process a chat message"""
        context = context or {}
        response = await self.chat_manager.process_message(message, context)
        return response
    
    async def run_cli(self):
        """Run command-line interface"""
        print("Multi-Agent Chatbot initialized. Type 'exit' to quit.")
        print("-" * 50)
        
        context = {"history": []}
        
        while True:
            try:
                user_input = input("\nYou: ")
                
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                    
                # Process message
                response = await self.chat(user_input, context)
                
                # Display response
                if response.get("text"):
                    print(f"\nAssistant: {response['text']}")
                    
                if response.get("images"):
                    print(f"\n[Generated {len(response['images'])} image(s)]")
                    
                if response.get("audio"):
                    print(f"\n[Generated audio file]")
                    
                if response.get("metadata", {}).get("sources"):
                    print("\nSources:")
                    for source in response["metadata"]["sources"]:
                        print(f"  - {source}")
                        
                # Update context
                context["history"].append(f"User: {user_input}")
                context["history"].append(f"Assistant: {response.get('text', '')}")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
                continue
            except Exception as e:
                print(f"Error: {e}")

async def main():
    """Main entry point"""
    chatbot = MultiAgentChatbot()
    await chatbot.run_cli()

if __name__ == "__main__":
    asyncio.run(main())