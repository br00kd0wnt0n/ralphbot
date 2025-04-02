import streamlit as st
import os
import datetime
import time
import uuid
from dotenv import load_dotenv
from openai import OpenAI

# This MUST be the first Streamlit command
st.set_page_config(page_title="RalphBOT NY v1.0", page_icon=":robot_face:")

# Import company prompt from external file
from company_knowledge import COMPANY_PROMPT

# Load environment variables
load_dotenv()

# Check for OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found in environment variables.")
    
    # Check if it's in Streamlit secrets
    if "openai" in st.secrets and "OPENAI_API_KEY" in st.secrets["openai"]:
        api_key = st.secrets["openai"]["OPENAI_API_KEY"]
        st.success("Found API key in st.secrets['openai']")
    elif "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("Found API key in st.secrets directly")
    else:
        st.error("API key not found in Streamlit secrets either")
        
if api_key:
    # Show the first 4 and last 4 characters only
    safe_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "Key too short"
    st.info(f"Using API key: {safe_key}")
else:
    st.error("No API key available. Bot functionality will be limited.")
    st.stop()

# Initialize OpenAI client with new API style
client = OpenAI(api_key=api_key)

# Simple logging function (no MongoDB)
def log_interaction(user_id, query, response, bot_type, metadata=None):
    """Log bot interaction to console only"""
    print(f"[LOG] User: {user_id} | Query: {query} | Bot: {bot_type} | Time: {metadata.get('response_time_ms', 0)}ms")

# Display logo and title
st.markdown("""
<div style='text-align: center; background-color: #E90080; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
    <h1 style='color: white; font-family: monospace;'>RALPH</h1>
</div>
""", unsafe_allow_html=True)

st.title("RalphBOT NY v1.0")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Generate a session ID if not already present
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Initialize state variables if they don't exist
if "clicked_question" not in st.session_state:
    st.session_state.clicked_question = None

# Function to set clicked question
def set_question(question):
    st.session_state.clicked_question = question

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Create suggestion buttons when no conversation yet
if len(st.session_state.messages) == 0:
    st.markdown("##### Try asking about:")
    
    # Custom CSS for equal width buttons
    st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        background-color: #E90080;
        color: white;
    }
    div.stButton > button:hover {
        background-color: #C50070;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create columns and buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("Services", key="btn_services", 
                 on_click=set_question, 
                 args=("What services does Ralph offer?",))
    with col2:
        st.button("Company History", key="btn_history", 
                 on_click=set_question, 
                 args=("Tell me about Ralph's history",))
    with col3:
        st.button("Offices", key="btn_offices", 
                 on_click=set_question, 
                 args=("Where are Ralph's offices located?",))

# Get user input
user_input = st.chat_input("Ask RalphBOT something...")

# Determine the actual query (from button or direct input)
user_query = None
if st.session_state.clicked_question:
    user_query = st.session_state.clicked_question
    st.session_state.clicked_question = None  # Clear for next time
elif user_input:
    user_query = user_input

# Process query if we have one
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
            # Measure response time
            start_time = time.time()
            
            # New style API call with streaming
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=api_messages,
                stream=True
            )
            
            # Stream the response (new style)
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
            
            # Calculate response time
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Final response without cursor
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            
            # Log the interaction to console
            metadata = {
                "response_time_ms": response_time_ms,
                "session_length": len(st.session_state.messages),
                "platform": "web"
            }
            
            log_interaction(
                user_id=st.session_state.session_id, 
                query=user_query, 
                response=full_response, 
                bot_type="streamlit",
                metadata=metadata
            )
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            full_response = "I'm sorry, I encountered an error. Please try again."
            message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Re-run the app to show the updated conversation and input field
    st.rerun()

# Add a sidebar with additional information
with st.sidebar:
    st.title("About RalphBOT")
    st.write("RalphBOT is an AI assistant for Ralph agency.")
    st.write("Ask questions about Ralph's services, history, and expertise.")
    
    # Add a reset button
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()
