from core.base_agent import BaseAgent
from typing import Dict, Any
import google.generativeai as genai
from gtts import gTTS
import io
import base64

class SpeechAgent(BaseAgent):
    """Agent for speech synthesis and audio processing"""
    
    def __init__(self):
        super().__init__(name="speech_agent")
        # Note: Google's TTS model integration would need proper API setup
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process speech-related tasks"""
        message = input_data.get("message", "")
        context = input_data.get("context", {})
        
        # Check if we need to generate speech
        if self._should_generate_speech(message):
            text_to_speak = self._extract_text_to_speak(message, context)
            audio_data = await self.generate_speech(text_to_speak)
            
            return {
                "text": f"Generated audio for: '{text_to_speak[:50]}...'",
                "audio": [audio_data],
                "metadata": {"agent": self.name}
            }
            
        return {"text": "", "metadata": {"agent": self.name}}
    
    async def generate_speech(self, text: str) -> Dict[str, Any]:
        """Generate speech from text"""
        try:
            # Using gTTS as fallback (Google's TTS model would be better)
            tts = gTTS(text=text, lang='en')
            
            # Save to buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            # Convert to base64
            audio_base64 = base64.b64encode(audio_buffer.read()).decode()
            
            return {
                "data": audio_base64,
                "format": "mp3",
                "text": text
            }
            
        except Exception as e:
            print(f"Speech generation error: {e}")
            return {}
    
    def _should_generate_speech(self, message: str) -> bool:
        """Determine if speech generation is needed"""
        keywords = ['say', 'speak', 'pronounce', 'read', 'voice', 'audio', 'sound']
        return any(k in message.lower() for k in keywords)
    
    def _extract_text_to_speak(self, message: str, context: Dict) -> str:
        """Extract text that should be converted to speech"""
        # Simple extraction - could be enhanced with NLP
        if '"' in message:
            # Extract text between quotes
            import re
            quotes = re.findall(r'"([^"]*)"', message)
            if quotes:
                return quotes[0]
                
        # Use last response if available
        if context.get("last_response"):
            return context["last_response"]
            
        return message