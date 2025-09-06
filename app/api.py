from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .chat import answer_question
from .indexer import build_index
from .database import SessionLocal, Thread, Message, init_db
from datetime import datetime

# Init App
app = FastAPI(title="Confluence RAG Chatbot")

# Init DB
init_db()

class ChatInput(BaseModel):
    question: str
    top_k:int | None = None
    thread_id: int | None = None
    stream: bool = False

class ChatOutput(BaseModel):
    answer: str
    citations : list
    thread_id: int


@app.post("/chat", response_model=ChatOutput)
def chat_endpoint(payload: ChatInput):
    db = SessionLocal()

    try:
        if not payload.thread_id:
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

        #  Streaming response        
        if payload.stream:

            def generate():
                full_answer = ""
                citations = []
                for chunk in answer_question(payload.question, payload.top_k, payload.stream):
                    
                    if chunk.startswith("\n[CITATIONS]"):
                        # print("citations in API --->"+ chunk)
                        citations = eval(chunk.replace("\n[CITATIONS]", ""))
                        continue
                    full_answer +=chunk
                    yield chunk

                # save assistant msg after streaming finishes
                assistant_msg = Message(thread_id=payload.thread_id, role="assistant", content=full_answer, citations=citations)
                db.add(assistant_msg)
                db.commit()
            
            return StreamingResponse(generate(), media_type="text/plain")

        else:
            # without streaming
            result = answer_question(payload.question, payload.top_k, payload.stream)

            assistant_msg = Message(thread_id = thread.id, role="assistant", content= result["answer"], citations=result.get("citations", []))
            db.add(assistant_msg)
            db.commit()

            return {"answer": result["answer"], "citations": result.get("citations", []), "thread_id": thread.id}

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


@app.post("/rebuild-index")
def rebuild_index_endpoint():
    build_index(rebuild=True)
    return {"status": "ok"}



