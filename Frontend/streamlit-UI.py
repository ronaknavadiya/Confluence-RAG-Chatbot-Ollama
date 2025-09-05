import streamlit as st
import requests
import os

# --------------------  Global variables ---------------------------- #

API_URL = os.getenv("CHAT_API_URL", "http://localhost:8000/chat")


#------------------------  Streamlit UI ------------------------------#

st.set_page_config(page_title="Confluence RAG Chatbot", layout="wide")

st.title("Confluence RAG Chatbot")
st.markdown("Ask questions and get answers from your Confluence documentation.")

# Sidebar for settings 
top_k = st.sidebar.slider("Search from Top-K Documents", 1, 10, 3)

question = st.text_input("Ask a question: ")

if st.button("Get Answer") and question.strip():
    with st.spinner("Querying the knowledge base..."):
        try:
            response = requests.post(API_URL, json={"question": question, "top_k": top_k})
            if response.status_code == 200:
                data = response.json()
                st.subheader("Answer:")
                st.write(data["answer"])

                st.subheader("Citations")
                for i, citation in enumerate(data['citations'],1):
                    st.markdown(f"**[{i}] {citation.get('title','Untitled')}** - {citation.get('source','')}")

            else:
                st.error(f"Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"Request failed: {e}")