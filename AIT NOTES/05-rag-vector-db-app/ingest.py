"""Read the company document, embed its chunks, and store them in ChromaDB."""

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_DIR = Path(__file__).parent
DOCUMENT_PATH = PROJECT_DIR / "documents" / "company.txt"
CHROMA_PATH = PROJECT_DIR / "chroma_db"
COLLECTION_NAME = "company_documents"

load_dotenv(PROJECT_DIR / ".env")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")


def ingest() -> int:
    """Replace the collection contents with embeddings from company.txt."""
    document = DOCUMENT_PATH.read_text(encoding="utf-8")
    chunks = [chunk.strip() for chunk in document.split("\n\n") if chunk.strip()]
    if not chunks:
        raise ValueError("The document has no non-empty chunks.")

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass  # The collection does not exist yet.
    collection = chroma_client.create_collection(COLLECTION_NAME)

    response = client.embeddings.create(model=embedding_model, input=chunks)
    embeddings = [item.embedding for item in response.data]
    collection.add(
        ids=[f"chunk-{index}" for index in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
    )
    return len(chunks)


if __name__ == "__main__":
    count = ingest()
    print(f"Stored {count} document chunks in ChromaDB.")
