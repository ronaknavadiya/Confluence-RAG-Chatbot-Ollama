from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .chat import answer_question
from .indexer import build_index
from .database import SessionLocal, Thread, Message, init_db
from datetime import datetime
import json

# Init App
app = FastAPI(title="Confluence RAG Chatbot")

# Init DB
init_db()

class ChatInput(BaseModel):
    question: str
    top_k:int | None = None
    thread_id: int | None = None

class ChatOutput(BaseModel):
    answer: str
    citations : list
    thread_id: int


@app.post("/chat", response_model=ChatOutput)
def chat_endpoint(payload: ChatInput):
    db = SessionLocal()

    try:
        if payload.thread_id == None:
            thread = Thread(name="Thread_" + datetime.utcnow().isoformat())
            db.add(thread)
            db.commit()
            db.refresh(thread)
            payload.thread_id = thread.id
        else:
            thread = db.query(Thread).filter(Thread.id == payload.thread_id).first()
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            
        user_msg = Message(thread_id = thread.id, role="user", content=payload.question)
        db.add(user_msg)
        db.commit()

        def generate():
            full_answer = ""
            citations = []
            for chunk in answer_question(payload.question, payload.top_k):
                
                if chunk["type"] == "token":
                    full_answer += chunk["content"]
                    # "\n" Separates each JSON message in the stream.
                    # "\n" Ensures the client (iter_lines()) receives complete JSON objects.
                    yield json.dumps(chunk) + "\n"

                elif chunk["type"] == "citations":
                    citations = chunk["citations"]
                    yield json.dumps(chunk) + "\n"


            # save assistant msg after streaming finishes
            assistant_msg = Message(thread_id=payload.thread_id, role="assistant", content=full_answer, citations=citations)
            db.add(assistant_msg)
            db.commit()

            # yield final message with thread_id so frontend can capture it
            final_info = {
                "type": "thread_info",
                "thread_id": payload.thread_id
            }
            yield json.dumps(final_info) + "\n"

        return StreamingResponse(generate(), media_type="application/x-ndjson")

    finally:
        db.close()



@app.get("/threads")
def list_threads():
    db = SessionLocal()
    try:
        threads = db.query(Thread).order_by(Thread.created_at.desc()).all()
        return [{"id":t.id, "name":t.name, "created_at": t.created_at.isoformat()}  for t in threads]

    finally:
        db.close()

@app.get("/messages/{thread_id}")
def extract_messages_from_thread_id(thread_id: int):
    db = SessionLocal()
    try:
        messages = db.query(Message).filter(Message.thread_id == thread_id).all()
        return messages
    except Exception as e:
        return e.with_traceback()
    finally:
        db.close()

@app.delete("/delete-thread/{thread_id}")
def delete_thread_based_on_thread_id(thread_id:int):
    db = SessionLocal()
    try:
        thread = db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            raise HTTPException(status_code=404, detail= "Thread not found")
        
        # delete all msg first 
        db.query(Message).filter(Message.thread_id == thread_id).delete()
        # delete thread form Thread table
        db.delete(thread)
        db.commit()
    finally:
        db.close()


@app.post("/rebuild-index")
def rebuild_index_endpoint():
    build_index(rebuild=True)
    return {"status": "ok"}



