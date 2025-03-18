import streamlit as st
import os
import openai
from dotenv import load_dotenv
from company_knowledge import COMPANY_PROMPT

# This MUST be the first Streamlit command
st.set_page_config(page_title="RalphBOT NY v1.0", page_icon=":robot_face:")

# Now we can load other modules and run other code
from PIL import Image

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

# Display logo and title
st.markdown("""
    <div style='text-align: center; background-color: #E90080; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
        <h1 style='color: white; font-family: monospace;'>ralphBOT v0.1</h1>
    </div>
    """, unsafe_allow_html=True)

st.title("(definitely not Skynet)")

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
