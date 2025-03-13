import streamlit as st
import os
from openai import OpenAI

# Try to get API key from environment variables or Streamlit secrets
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

# Initialize OpenAI client
client = OpenAI(api_key=api_key)
