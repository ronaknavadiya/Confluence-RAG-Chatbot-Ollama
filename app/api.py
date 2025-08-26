from fastapi import FastAPI
from pydantic import BaseModel
from .chat import answer_question
from .indexer import build_index

# Init App
app = FastAPI(title="Confluence RAG Chatbot")

class ChatInput(BaseModel):
    question: str
    top_k:int | None = None

class ChatOutput(BaseModel):
    answer: str
    citations : list


@app.post("/chat", response_model=ChatOutput)
def chat_endpoint(payload: ChatInput):
    return answer_question(payload.question , payload.top_k)


@app.post("/rebuild-index")
def rebuild_index_endpoint():
    build_index(rebuild=True)
    return {"status": "ok"}
