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


# --------------------------x---------------------------------x--------------------------------------x------------------------------------#
# Initialize chat_history in session_state

if "messages" not in st.session_state:
    st.session_state["messages"] = []


#------------------------------- Render Chat History ----------------------------------#
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
        # citations
        if msg.get("citations"):
            with st.expander("Citations"):
                for i, citation in enumerate(msg["citations"],1):
                    st.markdown(f"**[{i}] {citation.get('title','Untitled')}** - {citation.get('source','')}")




#------------------------------- Chat Input Box ----------------------------------#

if user_input := st.chat_input("Ask a question about your Confluence docs..."):
    # save user msg in session state
    st.session_state["messages"].append({"role":"user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Call LLM using FastAPI

    try:
        response = requests.post(API_URL, json={"question": user_input, "top_k": top_k})
        if response.status_code == 200:
            data = response.json()
            answer = data["answer"]
            citations = data.get("citations",[])

            # save assistant response
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "citations": citations}
            )
        
            # Render assistant reply
            st.chat_message("assistant").write(answer)
            if citations:
                with st.expander("Citations"):
                    for i, citation in enumerate(data['citations'],1):
                        st.markdown(f"**[{i}] {citation.get('title','Untitled')}** - {citation.get('source','')}")
        
        else:
            st.error(f"API error {response.status_code}: {response.text}")

    except Exception as e:
        st.error(f"Request failed: {e}")