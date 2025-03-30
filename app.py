import streamlit as st
import os
import datetime
import time
import uuid
from dotenv import load_dotenv
from pymongo import MongoClient
from company_knowledge import COMPANY_PROMPT

# Load environment variables
load_dotenv()

# Set page title and icon - must be the first Streamlit command
st.set_page_config(page_title="RalphBOT NY v1.0", page_icon=":robot_face:")

# Add this right after loading environment variables
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

# Try both new and old OpenAI API styles
try:
    # Try new style
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    use_new_style = True
    st.success("Using new OpenAI API style")
except Exception as e:
    # Fall back to old style
    import openai
    openai.api_key = api_key
    use_new_style = False
    st.success("Using legacy OpenAI API style")

# MongoDB connection handling
mongo_uri = os.getenv("MONGO_URI", "mongodb://placeholder")
mongodb_available = False
db = None

# Only attempt connection if we have a real-looking MongoDB URI
if mongo_uri != "mongodb://placeholder" and not mongo_uri.startswith("mongodb://placeholder"):
    try:
        db_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Test the connection
        db_client.admin.command('ping')
        db = db_client.ralphbot_analytics
        mongodb_available = True
        print("MongoDB connection successful")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        mongodb_available = False
else:
    print("MongoDB URI not provided, analytics features disabled")

# Logging function with MongoDB availability check
def log_interaction(user_id, query, response, bot_type, metadata=None):
    """Log bot interaction to MongoDB if available"""
    if not mongodb_available:
        return
        
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
        print(f"Error logging interaction: {e}")

# Heartbeat function with availability check
def update_heartbeat(bot_type):
    """Update bot heartbeat status in MongoDB if available"""
    if not mongodb_available:
        return
        
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

# Call heartbeat only if MongoDB is available
if mongodb_available:
    update_heartbeat("streamlit")

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

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Add suggestion buttons if no conversation has started yet
if len(st.session_state.messages) == 0:
    st.markdown("##### Try asking about:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Services"):
            st.session_state.messages.append({"role": "user", "content": "What services does Ralph offer?"})
            st.rerun()
    
    with col2:
        if st.button("Company History"):
            st.session_state.messages.append({"role": "user", "content": "Tell me about Ralph's history"})
            st.rerun()
    
    with col3:
        if st.button("Offices"):
            st.session_state.messages.append({"role": "user", "content": "Where are Ralph's offices located?"})
            st.rerun()

# User input
user_query = st.chat_input("Ask RalphBOT something...")

# User input
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
            # Measure response time
            start_time = time.time()
            
            if use_new_style:
                # New style API call
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=api_messages,
                    stream=True
                )
                
                # Stream the response
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
            else:
                # Old style API call
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=api_messages,
                    stream=True
                )
                
                # Stream the response (old style)
                for chunk in response:
                    if 'content' in chunk.choices[0].delta and chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)
            
            # Calculate response time
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            # Final response without cursor
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            
            # Log the interaction if MongoDB is available
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

# Add a sidebar with additional information
with st.sidebar:
    st.title("About RalphBOT")
    st.write("RalphBOT is an AI assistant for Ralph agency.")
    st.write("Ask questions about Ralph's services, history, and expertise.")
    
    # Add a reset button
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()
