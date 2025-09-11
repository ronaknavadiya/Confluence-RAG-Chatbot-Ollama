import streamlit as st
import requests
import os
import json
import traceback

# --------------------  Global variables ---------------------------- #
API_URL_CHAT = os.getenv("CHAT_API_URL", "http://localhost:8000/chat")
API_URL_THREADS = os.getenv("CHAT_API_URL_THREADS", "http://localhost:8000/threads")
API_URL_MESSAGES = os.getenv("CHAT_API_URL_MESSAGES", "http://localhost:8000/messages")
API_URL_DELETE_THREAD = os.getenv(
    "CHAT_API_URL_DELETE_THREAD", "http://localhost:8000/delete-thread"
)

# ------------------------  Streamlit UI ------------------------------ #
st.set_page_config(page_title="Confluence RAG Chatbot", layout="wide")
st.title("Confluence RAG Chatbot")
st.markdown("Ask questions and get answers from your Confluence documentation.")

# --------------------- Sidebar: Threads ---------------------------- #
top_k = st.sidebar.slider("Search from Top-K Documents", 1, 10, 3)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = None


def fetch_threads():
    try:
        response = requests.get(API_URL_THREADS)
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        print(e)
        return []


def fetch_thread_messages(thread_id):
    try:
        response = requests.get(f"{API_URL_MESSAGES}/{thread_id}")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(e)
        return []


threads = fetch_threads()
st.sidebar.subheader("Threads")

for thread in threads:
    col1, col2 = st.sidebar.columns([4, 1])

    with col1:
        if col1.button(thread["name"], key=f"select_{thread['id']}"):
            st.session_state["thread_id"] = thread["id"]
            st.session_state["messages"] = fetch_thread_messages(thread["id"])

    with col2:
        if col2.button("🗑️", key=f"delete_{thread['id']}"):
            try:
                response = requests.delete(f"{API_URL_DELETE_THREAD}/{thread['id']}")
                if response.status_code == 200:
                    # clear session if deleted thread was selected
                    if st.session_state["thread_id"] == thread["id"]:
                        st.session_state["thread_id"] = None
                        st.session_state["messages"] = []
                    st.toast(f"Deleted thread **{thread['name']}**", icon="🗑️")
                    st.rerun()
                else:
                    st.toast(
                        f"❌ Error deleting {thread['name']}: {response.text}", icon="⚠️"
                    )
            except Exception:
                st.error("Failed to delete thread:\n" + traceback.format_exc())

# Add New Thread
if st.sidebar.button("➕ New Thread", key="new_thread_btn"):
    st.session_state["thread_id"] = None
    st.session_state["messages"] = []
    st.rerun()

# --------------------- Chat Area: History --------------------------- #
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
        if msg.get("citations"):
            with st.expander("Citations"):
                for i, citation in enumerate(msg["citations"], 1):
                    st.markdown(
                        f"**[{i}] {citation.get('title','Untitled')}** - {citation.get('source','')}"
                    )

# --------------------- Chat Input & Streaming ----------------------- #
if user_input := st.chat_input("Ask a question about your Confluence docs..."):
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    payload = {
        "question": user_input,
        "top_k": top_k,
        "thread_id": st.session_state["thread_id"],
    }

    try:
        with requests.post(API_URL_CHAT, json=payload, stream=True) as response:
            if response.status_code != 200:
                st.error(f"API error {response.status_code}: {response.text}")
            else:
                full_answer, citations = "", []
                citations_rendered = False

                with st.chat_message("assistant"):
                    msg_placeholder = st.empty()
                    citations_placeholder = st.empty()

                    for line in response.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except Exception:
                            continue

                        if data["type"] == "token":
                            full_answer += data["content"]
                            msg_placeholder.markdown(full_answer + "▌")
                        elif data["type"] == "citations" and not citations_rendered:
                            citations = data["citations"]
                            if citations:
                                with citations_placeholder.expander("Citations"):
                                    for i, citation in enumerate(citations, 1):
                                        st.markdown(
                                            f"**[{i}] {citation.get('title','Untitled')}** - {citation.get('source','')}"
                                        )
                                citations_rendered = True
                        elif data["type"] == "thread_info":
                            st.session_state["thread_id"] = data["thread_id"]

                    msg_placeholder.markdown(full_answer)

                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": full_answer,
                        "citations": citations,
                    }
                )
    except Exception:
        st.error("Request failed:\n" + traceback.format_exc())
