import os
from dotenv import load_dotenv
from typing import Dict, Any
import google.generativeai as genai

load_dotenv()

class Config:
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    
    # Model Settings
    DEFAULT_MODEL = 'gemini-2.5-flash'
    VISION_MODEL = 'gemini-2.5-flash'
    IMAGE_GEN_MODEL = 'imagen-4.0-generate-001'
    TTS_MODEL = 'gemini-2.5-flash-preview-tts'
    EMBEDDING_MODEL = 'text-embedding-004'
    
    # Agent Settings
    MAX_AGENTS = 5
    DEFAULT_TEMPERATURE = 0.7
    MAX_TOKENS = 8192
    
    # File Settings
    ALLOWED_FILE_TYPES = ['pdf', 'docx', 'txt', 'csv', 'xlsx', 'json', 'md']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # MCP Protocol Settings
    MCP_VERSION = "1.0"
    MCP_TIMEOUT = 30
    
    @classmethod
    def initialize(cls):
        """Initialize Google AI with API key"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        genai.configure(api_key=cls.GOOGLE_API_KEY)
        return cls

# Initialize configuration
config = Config.initialize()