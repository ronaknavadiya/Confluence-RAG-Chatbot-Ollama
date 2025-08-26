import uvicorn
import argparse
from app.api import app
from app.chat import answer_question
from app.config import env
from app.indexer import build_index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--chat", action="store_true")
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()

    if args.rebuild_index:
        build_index(rebuild=True)

    if args.serve:
        uvicorn.run(app, host="0.0.0.0", port=int(env("PORT",8000)))

    if args.chat:
        print("Type 'exit' to quit.")
        while True:
            question = input("You:").strip()
            
            if not question or question.lower() in {"exit", "quit"}:
                break
            output = answer_question(question)
            print("Assistant:", output["answer"])
            print("Sources:", output["citations"])


if __name__ == "__main__":
    main()