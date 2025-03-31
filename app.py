import streamlit as st
import openai
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from company_knowledge import COMPANY_PROMPT
import uuid
import threading
import time

# Load API key from .env file
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# API Configuration
API_BASE_URL = "https://ralphbot-api-ef7a0f4b6655.herokuapp.com"

# Generate or retrieve unique session ID
def get_session_id():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

# Send heartbeat to API
def send_heartbeat():
    while True:
        try:
            response = requests.post(
                f"{API_BASE_URL}/heartbeat", 
                json={"bot_type": "streamlit"},
                timeout=10
            )
            if response.status_code != 200:
                st.warning("Failed to send heartbeat")
        except Exception as e:
            st.error(f"Heartbeat failed: {str(e)}")
        
        # Wait for 60 seconds before next heartbeat
        time.sleep(60)

# Log interaction to API
def log_interaction(interaction_data):
    try:
        response = requests.post(
            f"{API_BASE_URL}/log_interaction", 
            json=interaction_data,
            timeout=10
        )
        if response.status_code != 200:
            st.warning("Failed to log interaction")
    except Exception as e:
        st.error(f"Interaction logging failed: {str(e)}")

# Start heartbeat thread
heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
heartbeat_thread.start()

# App title and styling
st.set_page_config(page_title="RalphBOT NY", page_icon=":robot_face:")
st.title("RalphBOT NY v0.1")

# Add after the title
st.image("assets/logo.png", width=200)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
user_query = st.chat_input("Ask RalphBOT something...")

if user_query:
    # Record start time for response time tracking
    start_time = datetime.now()
    
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
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=api_messages,
                stream=True
            )
            
            # Stream the response
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log interaction
            interaction_data = {
                "timestamp": datetime.now().isoformat(),
                "user_id": get_session_id(),
                "bot_type": "streamlit",
                "query": user_query,
                "response": full_response,
                "response_time_ms": response_time
            }
            log_interaction(interaction_data)
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            full_response = "I'm sorry, I encountered an error. Please try again."
            message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
