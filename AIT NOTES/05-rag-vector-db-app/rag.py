"""Retrieve relevant company-document chunks and answer questions from them."""

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_DIR = Path(__file__).parent
CHROMA_PATH = PROJECT_DIR / "chroma_db"
COLLECTION_NAME = "company_documents"

load_dotenv(PROJECT_DIR / ".env")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
chat_model = os.environ.get("CHAT_MODEL", "gpt-4.1-mini")


def ask_question(question: str) -> str:
    """Answer *only* from the indexed company document."""
    question = question.strip()
    if not question:
        return "Please enter a question."

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        collection = chroma_client.get_collection(COLLECTION_NAME)
    except ValueError as error:
        raise RuntimeError("No data is indexed. Run `python ingest.py` first.") from error

    embedding_response = client.embeddings.create(
        model=embedding_model,
        input=question,
    )
    results = collection.query(
        query_embeddings=[embedding_response.data[0].embedding],
        n_results=3,
    )
    documents = results.get("documents", [[]])[0]
    if not documents:
        return "I could not find relevant information in the company documents."

    context = "\n\n".join(documents)
    instructions = (
        "Answer using only the supplied context. If the answer is not in the "
        "context, say: 'I don't know based on the company documents.'"
    )
    response = client.responses.create(
        model=chat_model,
        instructions=instructions,
        input=f"Context:\n{context}\n\nQuestion: {question}",
    )
    return response.output_text


if __name__ == "__main__":
    print(ask_question(input("Ask a question: ")))
