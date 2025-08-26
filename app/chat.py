from langchain.schema import HumanMessage, SystemMessage
from .indexer import get_vectorStore
from .llm import get_llm
from .config import env
from utills.rerank import re_rank

SYSTEM_PROMPT = """
        You are a helpful assistant that answers based on Confluence docs. 
        if confluence docs doesn't have context of asked query, say 'I don't know'
"""

def format_context(docs):
    output = []

    for i, doc in enumerate(docs, 1):
        title = doc.metadata.get("title", "Untitled")
        url = doc.metadata.get("source")
        header = f"[{i}] {title}"
        if url:
            header += f" - {url}"

        output.append(header + "\n" + doc.page_content.strip())
    return "\n\n".join(output)

def answer_question(question: str, k:int = None) -> dict:
    k = k or int(env("TOP_K", 3))

    vector_store = get_vectorStore()
    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": max(k*2, 8)})

    #  get relevant docs

    raw_docs = retriever.get_relevant_documents(question)
    
    # re rank docs
    top_docs = re_rank(question, raw_docs, top_k=k)

    # context
    context = format_context(top_docs)

    # llm
    llm = get_llm()

    msgs = [
        SystemMessage(content=SYSTEM_PROMPT + "\nContext:\n" + context),
        HumanMessage(content=question),
    ]

    # call method based on llm
    resp = llm.invoke(msgs) if hasattr(llm, "invoke") else llm(messages=msgs)
    text = resp.content if hasattr(resp, "content") else str(resp)

    return {"answer": text.strip(), "citations": [d.metadata for d in top_docs]}