# ui/streamlit_app.py
import streamlit as st
import asyncio
import sys
import os
from pathlib import Path
import nest_asyncio

# Fix for async event loop issues in Streamlit
nest_asyncio.apply()

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

# Now import the chatbot
try:
    from main import MultiAgentChatbot
    FULL_VERSION = True
except ImportError:
    FULL_VERSION = False
    
import base64
from io import BytesIO
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a singleton event loop for async operations
@st.cache_resource
def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

# Simple version for immediate testing
class SimpleStreamlitChatbot:
    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.vision_model = genai.GenerativeModel('gemini-2.5-flash')
        
    async def chat(self, message: str, context: dict = None) -> dict:
        """Process a chat message"""
        try:
            # Build prompt with context
            prompt = message
            if context and context.get("history"):
                history = "\n".join(context["history"][-10:])
                prompt = f"Previous conversation:\n{history}\n\nUser: {message}\nAssistant:"
            
            # Generate response
            response = await self.model.generate_content_async(prompt)
            
            # Check for image generation request
            images = []
            if any(keyword in message.lower() for keyword in ['generate image', 'create image', 'draw']):
                images = [{"info": "Image generation would happen here with Imagen API"}]
            
            return {
                "text": response.text,
                "images": images,
                "metadata": {"model": "gemini-2.5-flash"}
            }
            
        except Exception as e:
            return {"text": f"Error: {str(e)}", "images": [], "metadata": {}}
    
    def analyze_image(self, image_bytes: bytes, prompt: str = "What's in this image?") -> str:
        """Analyze an uploaded image"""
        try:
            img = Image.open(BytesIO(image_bytes))
            response = self.vision_model.generate_content([prompt, img])
            return response.text
        except Exception as e:
            return f"Image analysis error: {str(e)}"

# Async helper function
async def run_chat_async(chatbot, prompt, context):
    """Helper function to run chat asynchronously"""
    return await chatbot.chat(prompt, context)

# Page config
st.set_page_config(
    page_title="Multi-Agent Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Initialize chatbot
@st.cache_resource
def get_chatbot():
    if FULL_VERSION:
        return MultiAgentChatbot()
    else:
        return SimpleStreamlitChatbot()

try:
    chatbot = get_chatbot()
    initialization_success = True
    initialization_error = None
except Exception as e:
    initialization_success = False
    initialization_error = str(e)
    chatbot = None

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = {"history": []}

# UI Layout
st.title("🤖 Multi-Agent AI Assistant")
st.markdown(f"Powered by Google Gemini {'(Full Version)' if FULL_VERSION else '(Simplified Version)'}")

# Check initialization
if not initialization_success:
    st.error(f"Failed to initialize chatbot: {initialization_error}")
    st.info("Please ensure your .env file contains a valid GOOGLE_API_KEY")
    st.code("""
    # Create a .env file with:
    GOOGLE_API_KEY=your_google_api_key_here
    TAVILY_API_KEY=your_tavily_api_key_here  # Optional
    """)
    st.stop()

# Sidebar
with st.sidebar:
    st.header("📁 Upload Files")
    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt', 'csv', 'xlsx', 'json', 'png', 'jpg', 'jpeg']
    )
    
    uploaded_images = []
    uploaded_docs = []
    
    if uploaded_files:
        for file in uploaded_files:
            file_ext = Path(file.name).suffix.lower()
            
            # Handle images
            if file_ext in ['.png', '.jpg', '.jpeg']:
                uploaded_images.append({
                    "name": file.name,
                    "bytes": file.getvalue()
                })
                
            # Handle documents
            else:
                # Save temporarily
                temp_dir = "/tmp" if os.name != 'nt' else os.environ.get('TEMP', 'C:/temp')
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, file.name)
                
                with open(temp_path, "wb") as f:
                    f.write(file.getvalue())
                uploaded_docs.append({
                    "path": temp_path,
                    "name": file.name
                })
        
        if uploaded_images:
            st.success(f"✓ {len(uploaded_images)} image(s) uploaded")
            st.session_state.context["images"] = uploaded_images
            
        if uploaded_docs:
            st.success(f"✓ {len(uploaded_docs)} document(s) uploaded")
            st.session_state.context["files"] = uploaded_docs
    
    st.header("⚙️ Settings")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
    max_tokens = st.slider("Max Tokens", 100, 8192, 2048)
    
    # Model selection
    model_options = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]
    selected_model = st.selectbox("Model", model_options)
    
    # Feature toggles
    st.header("🎯 Features")
    enable_web_search = st.checkbox("Enable Web Search", value=True)
    enable_image_gen = st.checkbox("Enable Image Generation", value=True)
    
    # Info section
    st.header("ℹ️ Information")
    st.info(f"""
    **Status:** {'✓ Full Version' if FULL_VERSION else '⚠️ Simplified Version'}
    
    **Available Features:**
    - Chat with Gemini
    - Image Analysis
    {'- Web Search (if Tavily key set)' if enable_web_search else ''}
    {'- Image Generation (Imagen API)' if enable_image_gen else ''}
    """)

# Main chat interface
chat_container = st.container()

with chat_container:
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display images if any
            if message.get("images"):
                for img_data in message["images"]:
                    if isinstance(img_data, dict) and img_data.get("info"):
                        st.info(img_data["info"])
                    elif isinstance(img_data, dict) and img_data.get("data"):
                        img = Image.open(BytesIO(base64.b64decode(img_data["data"])))
                        st.image(img, caption="Generated Image")
                    
            # Display audio if any
            if message.get("audio"):
                for audio_data in message["audio"]:
                    audio_bytes = base64.b64decode(audio_data["data"])
                    st.audio(audio_bytes, format="audio/mp3")

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Check for image analysis request
    if uploaded_images and any(word in prompt.lower() for word in ['analyze', 'what', 'describe', 'tell', 'show']):
        # Analyze uploaded images
        with st.chat_message("user"):
            st.markdown(prompt)
            
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing images..."):
                if FULL_VERSION:
                    # Use full version with proper async handling
                    loop = get_event_loop()
                    context_with_images = st.session_state.context.copy()
                    context_with_images["images"] = uploaded_images
                    
                    try:
                        response = loop.run_until_complete(
                            run_chat_async(chatbot, prompt, context_with_images)
                        )
                        response_text = response.get("text", "Image analysis complete.")
                    except Exception as e:
                        response_text = f"Error: {str(e)}"
                else:
                    # Use simple version
                    results = []
                    for img_info in uploaded_images:
                        result = chatbot.analyze_image(img_info["bytes"], prompt)
                        results.append(f"**{img_info['name']}:** {result}")
                    response_text = "\n\n".join(results)
                
                st.markdown(response_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text
                })
    else:
        # Regular chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Use proper async handling
                    loop = get_event_loop()
                    response = loop.run_until_complete(
                        run_chat_async(chatbot, prompt, st.session_state.context)
                    )
                    
                    # Display response
                    if response.get("text"):
                        st.markdown(response["text"])
                        
                    # Display images
                    if response.get("images"):
                        for img_data in response["images"]:
                            if isinstance(img_data, dict) and img_data.get("info"):
                                st.info(img_data["info"])
                            elif isinstance(img_data, dict) and img_data.get("data"):
                                img = Image.open(BytesIO(base64.b64decode(img_data["data"])))
                                st.image(img, caption="Generated Image")
                            
                    # Display audio
                    if response.get("audio"):
                        for audio_data in response["audio"]:
                            audio_bytes = base64.b64decode(audio_data["data"])
                            st.audio(audio_bytes, format="audio/mp3")
                            
                    # Display sources
                    if response.get("metadata", {}).get("sources"):
                        with st.expander("📚 Sources"):
                            for source in response["metadata"]["sources"]:
                                st.write(f"- {source}")
                    
                    # Save assistant message
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.get("text", ""),
                        "images": response.get("images"),
                        "audio": response.get("audio")
                    })
                    
                    # Update context
                    st.session_state.context["history"].append(f"User: {prompt}")
                    st.session_state.context["history"].append(f"Assistant: {response.get('text', '')}")
                    
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

# Footer with instructions
with st.expander("📖 How to Use"):
    st.markdown("""
    ### Features:
    1. **Chat**: Ask questions and get responses from Gemini
    2. **Image Analysis**: Upload images and ask questions about them
    3. **File Upload**: Upload documents for analysis
    4. **Web Search**: Search the web for current information (requires Tavily API)
    5. **Image Generation**: Ask to generate images
    
    ### Examples:
    - "What's in this image?" (after uploading an image)
    - "Generate an image of a sunset over mountains"
    - "Search for the latest news about AI"
    - "Analyze this document" (after uploading a file)
    """)

# Clear chat button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.context = {"history": []}
        st.rerun()