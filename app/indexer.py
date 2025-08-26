from langchain_community.document_loaders import ConfluenceLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from .config import ensure_dir, env
import os


#  Load confluence document
def load_confluence_documents():
    loader = ConfluenceLoader(
        url=env("CONFLUENCE_URL"),
        username=env("CONFLUENCE_EMAIL"),
        api_key=env("CONFLUENCE_API_TOKEN"),
        cloud=True,
        space_key=env("CONFLUENCE_SPACE_KEY"),
        cql=env("CONFLUENCE_CQL"),
        limit=2000,
        include_attachments=False,
    )

    return loader.load()


#  indexing 

def build_index(rebuild: bool = False):

    index_dir = ensure_dir(env("INDEX_DIR", "./data/index"))
    index_path = index_dir / "faiss_index"

    # embeddings 

    embeddings = HuggingFaceEmbeddings(model_name = env("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))

    # if rebuild is not required and index exists load it for faster similarity search
    if not rebuild and index_path.exists():
        return FAISS.load_local(str(index_path), embeddings, allow_dangerous_deserialization=True)
    
    docs = load_confluence_documents()

    # print("docs--------------------->" )
    # for doc in docs:
    #     print(doc)

    # splitting of docs 
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(env("CHUNK_SIZE", 1200)),
        chunk_overlap=int(env("CHUNK_OVERLAP", 200)),
        separators=["\n\n", "\n", ". ", ".", " "]
    )

    chunks = splitter.split_documents(docs)

    # create vector store
    vector_store = FAISS.from_documents(chunks, embeddings)

    vector_store.save_local(str(index_path))

    return vector_store


def get_vectorStore():
    return build_index(rebuild=False)

# build_index()

