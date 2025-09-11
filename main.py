import uvicorn
import argparse
from app.api import app
from app.chat import answer_question
from app.config import env
from app.indexer import build_index
import os


def serve():
    # Auto build Index if FAISS vector store doesn't exist
    if not os.path.exists(env("VECTOR_STORE_PATH", "./data/index/faiss_index")):
        print("No FAISS index found. Running ingestion first...")
        build_index(rebuild=True)
        print("Ingestion complete. Starting API server...")

    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)


def main():
    parser = argparse.ArgumentParser(description="Confluence RAG Chatbot")
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Ingest Confluence/Markdown data into FAISS",
    )
    parser.add_argument("--serve", action="store_true", help="Run API server")
    parser.add_argument("--chat", action="store_true")
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()

    if args.ingest:
        build_index(rebuild=True)
    elif args.serve:
        serve()

    elif args.rebuild_index:
        build_index(rebuild=True)

    elif args.chat:
        print("Type 'exit' to quit.")
        while True:
            question = input("You:").strip()

            if not question or question.lower() in {"exit", "quit"}:
                break
            output = answer_question(question)
            print("Assistant:", output["answer"])
            print("Sources:", output["citations"])

    else:
        print("Use either --rebuild-index or --serve")


if __name__ == "__main__":
    main()
