import streamlit as st
import requests
import os
import json
import traceback

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

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = None


# Sidebar for thread selection
try:
    thread_response = requests.get(os.getenv("CHAT_API_URL_THREADS","http://localhost:8000/threads"))
    threads = thread_response.json() if thread_response.status_code == 200 else []
except:
    threads = []

st.sidebar.subheader("Threads")

for thread in threads:
    col1,col2 = st.sidebar.columns([4,1])
    with col1:
        if col1.button(thread["name"], type="secondary"):
            # if name != "New Thread":
                st.session_state["thread_id"] = thread["id"]
                # call db and set messages
                response = requests.get(f"http://localhost:8000/messages/{st.session_state['thread_id']}")
                if response.status_code == 200:
                    messages = response.json()
                    st.session_state["messages"] = messages
                    # print(messages)
            # else:
            #     st.session_state["thread_id"] = None

    with col2:
        # if name != "New Thread":
            # st.write(f"Thread id------------------>{st.session_state['thread_id']}")
            if col2.button("🗑️", key=f"delete_{thread['id']}"):
                try:
                    response = requests.delete(f"http://localhost:8000/delete-thread/{thread['id']}")
                    if response.status_code == 200:
                        if st.session_state["thread_id"] == thread['id']:
                            st.session_state["thread_id"] = None
                            st.session_state["messages"] = []
                        # toast notification
                        st.toast(f"Deleted thread **{thread['name']}**", icon="🗑️")
                        # refresh UI
                        st.rerun()

                    else:
                        st.toast(f"❌ Error deleting {thread['name']}: {response.text}", icon="⚠️")
                    
                except Exception as e:
                    print("Failed to delete thread :-" , traceback.print_exc())

    # st.sidebar.button("Delete", type="secondary", key=f"Delete_{name}")

#  Add New Thread
if st.sidebar.button("➕ New Thread", type="primary", key="new_thread_btn"):
    st.session_state["thread_id"] = None
    st.session_state["messages"] = []
    st.rerun()


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
        payload = {"question": user_input, "top_k": top_k, "thread_id": st.session_state["thread_id"]}
        with requests.post(API_URL, json= payload, stream= True) as response:
            if response.status_code != 200:
                 st.error(f"API error {response.status_code}: {response.text}")
            else:
                # Create assistant chat bubble for streaming tokens
                full_answer , citations = "", []
                citations_rendered = False  # Flag to prevent duplicate rendering

                with st.chat_message("assistant"):
                    msg_placeholder = st.empty()
                    citations_placeholder = st.empty()

                    for line in response.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except:
                            continue
                        
                        # print("DEBUG data:", data)

                        if data["type"] == "token":
                            full_answer += data["content"]
                            msg_placeholder.markdown(full_answer + "▌")

                        elif data["type"] == "citations":
                            citations = data["citations"]
                            if citations and not citations_rendered:
                                with citations_placeholder.expander("Citations"):
                                    for i, citation in enumerate(citations, 1):
                                        st.markdown(f"**[{i}] {citation.get('title','Untitled')}** - {citation.get('source','')}")
                                citations_rendered = True

                        elif data["type"] == "thread_info":
                            st.session_state["thread_id"] = data["thread_id"]

                    msg_placeholder.markdown(full_answer)
        
                # Save assistant message into session state
                st.session_state["messages"].append(
                    {"role": "assistant", "content": full_answer, "citations": citations}
                )

    except Exception as e:
        st.error(f"Request failed: {traceback.format_exc()}")