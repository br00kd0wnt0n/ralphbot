import streamlit as st
import os
import openai
from dotenv import load_dotenv
from company_knowledge import COMPANY_PROMPT
from PIL import Image

# IMPORTANT: This must be the first Streamlit command
st.set_page_config(page_title="RalphBOT NY", page_icon=":robot_face:")

# Load API key from environment variables or Streamlit secrets
load_dotenv()  # This loads .env file if available (for local development)

# Try to get API key from various sources
api_key = os.getenv("OPENAI_API_KEY")

# If not found in environment, check Streamlit secrets
if not api_key:
    if "openai" in st.secrets and "api_key" in st.secrets["openai"]:
        api_key = st.secrets["openai"]["api_key"]
    elif "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]

if not api_key:
    st.error("OpenAI API key not found. Please add it to your environment variables or Streamlit secrets.")
    st.stop()

# Configure the OpenAI API key
openai.api_key = api_key

# Display the logo
try:
    logo = Image.open("logo.png")
    st.image(logo, width=200)
except Exception as e:
    # Alternative approach using HTML/CSS instead of an image file
    st.markdown("""
        <div style='text-align: center; background-color: #E90080; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
            <h1 style='color: white; font-family: monospace;'>RALPH</h1>
        </div>
        """, unsafe_allow_html=True)

# App title and styling
st.set_page_config(page_title="RalphBOT NY v1.0", page_icon=":robot_face:")

# Display logo
try:
    logo = Image.open("logo.png")  # Adjust the path if you put it in a different location
    st.image(logo, width=200)
except:
    # Fallback if image isn't found
    pass

# App title and styling
st.set_page_config(page_title="RalphBOT NY", page_icon=":robot_face:")
st.title("RalphBOT NY v0.1")

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
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            full_response = "I'm sorry, I encountered an error. Please try again."
            message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
