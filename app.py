import streamlit as st
import os
import openai
from dotenv import load_dotenv
from company_knowledge import COMPANY_PROMPT

# This MUST be the first Streamlit command
st.set_page_config(page_title="RalphBOT NY v1.0", page_icon=":robot_face:")

# Now we can load other modules and run other code
from PIL import Image

# Add styling for images and content
st.markdown("""
<style>
    .stMarkdown img {
        max-width: 100%;
        height: auto;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    /* Brand colors and styling */
    :root {
        --ralph-pink: #E1562;
    }
    
    /* Styling for suggestion buttons */
    div.stButton > button {
        background-color: #E1562;
        color: white;
        border: none;
        padding: 5px 10px;
        border-radius: 5px;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #c7135e;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables and configure OpenAI
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    if "openai" in st.secrets and "api_key" in st.secrets["openai"]:
        api_key = st.secrets["openai"]["api_key"]
    elif "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]

if not api_key:
    st.error("OpenAI API key not found. Please add it to your environment variables or Streamlit secrets.")
    st.stop()

openai.api_key = api_key

# Function to handle audio in responses
def handle_audio_in_response(response):
    """Check response for audio trigger tags and display audio if found"""
    import re
    
    # Pattern to look for audio triggers
    audio_pattern = r'\[PLAY_AUDIO:(.*?)\]'
    audio_matches = re.findall(audio_pattern, response)
    
    # If audio triggers are found
    for audio_file in audio_matches:
        try:
            audio_path = f"audio/{audio_file.strip()}"
            st.audio(audio_path)
        except Exception as e:
            st.error(f"Could not play audio: {e}")
    
    # Remove the triggers from the displayed response
    cleaned_response = re.sub(audio_pattern, '', response)
    return cleaned_response

# Display logo and title
st.markdown("""
<div style='text-align: center; background-color: #E90080; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
    <h1 style='color: white; font-family: monospace;'>RALPH</h1>
</div>
""", unsafe_allow_html=True)

st.title("RalphBOT NY v1.0")

# Add a reset button in the sidebar
with st.sidebar:
    st.title("RalphBOT Controls")
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.session_state.welcomed = False
        st.experimental_rerun()

# Initialize session state for chat history and welcome message
if "messages" not in st.session_state:
    st.session_state.messages = []

if "welcomed" not in st.session_state:
    st.session_state.welcomed = False

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Display welcome message if first visit
if not st.session_state.welcomed:
    with st.chat_message("assistant"):
        st.markdown("""
        # 👋 Hiya! I'm RalphBot! 
        
        Half Ralph Wiggum, half ad exec man-child, all about that sweet Ralph agency knowledge. 🧠✨
        
        You can ask me stuff like:
        - What services does Ralph offer? 🚀
        - Tell me about the company history 🕰️
        - Who's the Managing Director of Ralph NY? 👔
        - What's your famous brand color? 🎨
        - Got any case studies on Stranger Things? 🙃
        
        Or just chat about 90s TV shows, internet memes, or why the office temperature is ALWAYS wrong. 🥶🔥
        
        (Warning: I may randomly start talking about Stranger Things or make jokes about the founders. It's my thing.) 💁‍♂️
        """, unsafe_allow_html=True)
    
    # Mark as welcomed so this only shows once per session
    st.session_state.welcomed = True

# Add suggestion chips if no conversation has started yet
if len(st.session_state.messages) == 0:
    st.markdown("##### Try asking about:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Services"):
            # Simulate clicking this suggestion
            st.session_state.messages.append({"role": "user", "content": "What services does Ralph offer?"})
            st.experimental_rerun()
    
    with col2:
        if st.button("Case Studies"):
            st.session_state.messages.append({"role": "user", "content": "Tell me about your work on Stranger Things"})
            st.experimental_rerun()
    
    with col3:
        if st.button("Office Temperature"):
            st.session_state.messages.append({"role": "user", "content": "How's the temperature in the office?"})
            st.experimental_rerun()

# Get user input
user_query = st.chat_input("Ask RalphBOT something...")

if user_query:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Prepare messages for API call
    api_messages = [
        {"role": "system", "content": COMPANY_PROMPT},
    ]
    
    # Add conversation history
    for message in st.session_state.messages:
        api_messages.append({"role": message["role"], "content": message["content"]})
    
    # Call OpenAI API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Use the older API format which is more compatible
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=api_messages,
                stream=True
            )
            
            # Stream the response
            for chunk in response:
                if 'content' in chunk.choices[0].delta and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
            
            # Process any audio triggers in the response
            processed_response = handle_audio_in_response(full_response)
            message_placeholder.markdown(processed_response, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            full_response = "I'm sorry, I encountered an error. Please try again."
            message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
