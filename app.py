import streamlit as st
import os
import openai
from dotenv import load_dotenv
from company_knowledge import COMPANY_PROMPT

# This MUST be the first Streamlit command
st.set_page_config(page_title="v0.2", page_icon=":robot_face:")

import datetime
import time
import uuid
from pymongo import MongoClient

# Add MongoDB connection near your imports
mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://your-connection-string")
db_client = MongoClient(mongo_uri)
db = db_client.ralphbot_analytics

# Add logging function after initializing session state
def log_interaction(user_id, query, response, bot_type, metadata=None):
    """Log bot interaction to MongoDB"""
    try:
        interaction = {
            "timestamp": datetime.datetime.now(),
            "interaction_id": str(uuid.uuid4()),
            "user_id": user_id,
            "query": query,
            "response": response,
            "bot_type": bot_type,
            "response_time_ms": metadata.get("response_time_ms", 0),
            "token_usage": metadata.get("token_usage", 0),
            "metadata": metadata or {}
        }
        db.interactions.insert_one(interaction)
    except Exception as e:
        st.error(f"Error logging interaction: {e}")

# Add heartbeat function
def update_heartbeat(bot_type):
    """Update bot heartbeat status in MongoDB"""
    try:
        db.bot_status.update_one(
            {"bot_type": bot_type},
            {
                "$set": {
                    "last_heartbeat": datetime.datetime.now(),
                    "status": "online"
                }
            },
            upsert=True
        )
    except Exception as e:
        st.error(f"Error updating heartbeat: {e}")

# Call heartbeat on startup
update_heartbeat("streamlit")

# Initialize session state for chat history and welcome message
if "messages" not in st.session_state:
    st.session_state.messages = []

if "welcomed" not in st.session_state:
    st.session_state.welcomed = False

# Initialize button state variables
if "button_clicked" not in st.session_state:
    st.session_state.button_clicked = False
    
if "button_question" not in st.session_state:
    st.session_state.button_question = ""

if "used_suggestions" not in st.session_state:
    st.session_state.used_suggestions = set()

# After initializing session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add heartbeat function here
def update_heartbeat(bot_type):
    """Update bot heartbeat status in MongoDB"""
    try:
        db.bot_status.update_one(
            {"bot_type": bot_type},
            {
                "$set": {
                    "last_heartbeat": datetime.datetime.now(),
                    "status": "online"
                }
            },
            upsert=True
        )
    except Exception as e:
        print(f"Error updating heartbeat: {e}")

# Call on startup
update_heartbeat("streamlit")

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

# Inside your bot response code where you call OpenAI
start_time = time.time()

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=api_messages,
    stream=True
)

# After generating the full response:
end_time = time.time()
response_time_ms = int((end_time - start_time) * 1000)

# Log the interaction
session_id = st.session_state.get("session_id", str(uuid.uuid4()))
if "session_id" not in st.session_state:
    st.session_state.session_id = session_id
    
metadata = {
    "response_time_ms": response_time_ms,
    "session_length": len(st.session_state.messages),
    "platform": "web"
}

log_interaction(
    user_id=session_id, 
    query=user_query, 
    response=full_response, 
    bot_type="streamlit",
    metadata=metadata
)

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
        st.rerun()

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

# Initialize a flag for suggestion clicks
if "clicked_suggestion" not in st.session_state:
    st.session_state.clicked_suggestion = None

# Create dynamic suggestion system
if "used_suggestions" not in st.session_state:
    st.session_state.used_suggestions = set()

# Define suggestion pools by category
SUGGESTION_POOLS = {
    "services": [
        "What services does Ralph offer?",
        "Tell me about your Strategy services",
        "How does your Social service work?",
        "What does your Studio team do?",
        "Can you explain your Live services?"
    ],
    "company": [
        "When was Ralph founded?",
        "How many offices does Ralph have?",
        "What's Ralph's mission?",
        "Who is the Managing Director of Ralph NY?",
        "What's your famous brand color?"
    ],
    "cases": [
        "Tell me about your work on Stranger Things",
        "What did you do for Squid Game?",
        "Show me your best case study",
        "What entertainment brands have you worked with?",
        "What's your approach to fan engagement?"
    ],
    "fun": [
        "How's the temperature in the office?",
        "Tell me a joke about the founders",
        "What's your favorite 90s TV show?",
        "Share a random internet meme",
        "What do you think about Bridgerton?"
    ]
}

# Function to get fresh suggestions
def get_fresh_suggestions():
    suggestions = []
    
    # Try to infer what categories might interest the user based on conversation
    interested_categories = ["services", "company", "cases", "fun"]  # Default starting categories
    
    if len(st.session_state.messages) > 0:
        # Analyze conversation to determine interests
        conversation_text = " ".join([m["content"] for m in st.session_state.messages])
        if "service" in conversation_text.lower() or "strategy" in conversation_text.lower():
            interested_categories = ["services"] + [c for c in interested_categories if c != "services"]
        if "case" in conversation_text.lower() or "stranger" in conversation_text.lower():
            interested_categories = ["cases"] + [c for c in interested_categories if c != "cases"]
        if "found" in conversation_text.lower() or "company" in conversation_text.lower():
            interested_categories = ["company"] + [c for c in interested_categories if c != "company"]
    
    # Get one suggestion from each interested category
    for category in interested_categories[:3]:  # Limit to 3 categories
        available = [s for s in SUGGESTION_POOLS[category] if s not in st.session_state.used_suggestions]
        if not available:  # If all used, reset for this category
            available = SUGGESTION_POOLS[category]
            
        if available:
            suggestion = available[0]  # Choose first available
            suggestions.append(suggestion)
            
    # If we don't have 3 suggestions yet, fill in from any category
    all_suggestions = [item for sublist in SUGGESTION_POOLS.values() for item in sublist]
    while len(suggestions) < 3:
        available = [s for s in all_suggestions if s not in suggestions and s not in st.session_state.used_suggestions]
        if not available:
            available = [s for s in all_suggestions if s not in suggestions]
        
        if available:
            suggestions.append(available[0])
        else:
            break  # Safety check
            
    return suggestions

# Get three dynamic suggestions
suggestions = get_fresh_suggestions()

# Define button click handlers
def click_button1():
    st.session_state.button_clicked = True
    st.session_state.button_question = suggestions[0]
    st.session_state.used_suggestions.add(suggestions[0])

def click_button2():
    st.session_state.button_clicked = True
    st.session_state.button_question = suggestions[1]
    st.session_state.used_suggestions.add(suggestions[1])

def click_button3():
    st.session_state.button_clicked = True
    st.session_state.button_question = suggestions[2]
    st.session_state.used_suggestions.add(suggestions[2])

# Display buttons with dynamic text
st.markdown("##### Try asking about:")  # Keep only this one
col1, col2, col3 = st.columns(3)

with col1:
    st.button(suggestions[0].split("?")[0].split(".")[0], on_click=click_button1)

with col2:
    st.button(suggestions[1].split("?")[0].split(".")[0], on_click=click_button2)

with col3:
    st.button(suggestions[2].split("?")[0].split(".")[0], on_click=click_button3)

# Process button clicks 
if st.session_state.button_clicked:
    # Only proceed if we don't already have an unprocessed question
    if not any(msg["role"] == "user" and msg == st.session_state.messages[-1] for msg in st.session_state.messages):
        question = st.session_state.button_question
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(question)
        
        # Add to message history
        st.session_state.messages.append({"role": "user", "content": question})
        
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
    
    # Reset the button click state
    st.session_state.button_clicked = False

# Process suggestion clicks BEFORE checking for direct user input
if st.session_state.clicked_suggestion:
    question = st.session_state.clicked_suggestion
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(question)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": question})
    
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
    
    # Reset the flag
    st.session_state.clicked_suggestion = None

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
