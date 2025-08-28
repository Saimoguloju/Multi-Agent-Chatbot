# agents/image_agent.py
from core.base_agent import BaseAgent
from typing import Dict, Any, List
from PIL import Image
import google.generativeai as genai
import base64
from io import BytesIO

class ImageAgent(BaseAgent):
    """Agent for image generation and processing"""
    
    def __init__(self):
        super().__init__(name="image_agent")
        self.vision_model = genai.GenerativeModel('gemini-2.5-flash')
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process image-related tasks"""
        message = input_data.get("message", "")
        context = input_data.get("context", {})
        
        response_data = {"metadata": {"agent": self.name}}
        
        # Check if there's an image to analyze
        if context.get("images"):
            analysis = await self.analyze_images(context["images"], message)
            response_data["text"] = analysis
            
        # Check if we need to generate an image
        if self._should_generate_image(message):
            # For now, just return a placeholder since Imagen requires additional setup
            response_data["text"] = "Image generation feature is being set up. This requires Imagen API configuration."
            response_data["images"] = []
            
        return response_data
    
    async def analyze_images(self, images: List, prompt: str) -> str:
        """Analyze uploaded images"""
        responses = []
        
        for image_data in images:
            try:
                # Handle different image formats
                if isinstance(image_data, dict):
                    if 'bytes' in image_data:
                        # Image from Streamlit upload
                        image = Image.open(BytesIO(image_data['bytes']))
                    elif 'data' in image_data:
                        # Base64 encoded image
                        image = Image.open(BytesIO(base64.b64decode(image_data['data'])))
                    else:
                        continue
                elif isinstance(image_data, str):
                    # Base64 string
                    image = Image.open(BytesIO(base64.b64decode(image_data)))
                elif isinstance(image_data, bytes):
                    # Raw bytes
                    image = Image.open(BytesIO(image_data))
                else:
                    # Assume it's already a PIL Image
                    image = image_data
                    
                # Analyze with vision model
                response = await self.vision_model.generate_content_async([prompt, image])
                responses.append(response.text)
                
            except Exception as e:
                responses.append(f"Error analyzing image: {str(e)}")
                
        return "\n".join(responses) if responses else "No images to analyze."
    
    async def generate_image(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate images using Imagen"""
        # Placeholder for now - actual Imagen implementation requires additional setup
        return []
    
    def _should_generate_image(self, message: str) -> bool:
        """Determine if image generation is needed"""
        keywords = ['generate', 'create', 'draw', 'make', 'design']
        image_keywords = ['image', 'picture', 'illustration', 'graphic']
        
        message_lower = message.lower()
        return any(k in message_lower for k in keywords) and any(k in message_lower for k in image_keywords)