"""
RAG: ChromaDB vector storage. Before answering, the agent checks the local vector DB
for previous projects or 'Help Me Pro' context stored on GitHub.
"""
import os
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(ROOT / "data" / "chroma"))
COLLECTION_NAME = "core_ai_knowledge"

_vectordb = None


def _get_embeddings():
    """Local embeddings (sentence-transformers) to avoid API calls."""
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
    except Exception:
        return None


def get_or_create_vector_store(force_new: bool = False):
    """Get or create Chroma vector store with persistent storage."""
    global _vectordb
    if _vectordb is not None and not force_new:
        return _vectordb
    try:
        from langchain_community.vectorstores import Chroma
        embeddings = _get_embeddings()
        if embeddings is None:
            return None
        Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        _vectordb = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
        )
        return _vectordb
    except Exception:
        return None


def add_documents(texts: List[str], metadatas: Optional[List[dict]] = None) -> bool:
    """Add text chunks to the vector store."""
    if not texts:
        return False
    store = get_or_create_vector_store()
    if store is None:
        return False
    try:
        try:
            from langchain_core.documents import Document
        except ImportError:
            from langchain.schema import Document
        docs = [
            Document(page_content=t.strip(), metadata=metadatas[i] if metadatas and i < len(metadatas) else {"source": "user"})
            for i, t in enumerate(texts) if t and t.strip()
        ]
        if not docs:
            return False
        store.add_documents(docs)
        return True
    except Exception:
        return False


def query_vector_db(question: str, k: int = 5) -> str:
    """
    RAG: Query the local vector DB for relevant previous projects / Help Me Pro context.
    Returns concatenated context string to inject into the prompt.
    """
    if not question or not question.strip():
        return ""
    store = get_or_create_vector_store()
    if store is None:
        return ""
    try:
        docs = store.similarity_search(question.strip(), k=k)
        if not docs:
            return ""
        return "\n\n---\n\n".join(d.page_content for d in docs)
    except Exception:
        return ""


def load_github_context_into_store() -> bool:
    """
    Pull project / 'Help Me Pro' context from GitHub and add to the local vector DB.
    Uses knowledge_base.md, memory/tasks, and any 'Help Me Pro' or project-related paths.
    """
    try:
        from memory.github_rag import read_from_github, pull_github_memory
    except ImportError:
        return False
    store = get_or_create_vector_store()
    if store is None:
        return False
    chunks = []
    # Knowledge base
    kb = read_from_github("knowledge_base.md")
    if kb:
        for part in kb.split("\n\n---\n\n"):
            if part.strip():
                chunks.append((part.strip()[:2000], {"source": "knowledge_base.md"}))
    # Recent experience / tasks (last 10 files)
    raw = pull_github_memory(max_files=10)
    if raw:
        for part in raw.split("\n\n---\n\n"):
            if part.strip():
                chunks.append((part.strip()[:2000], {"source": "github_memory"}))
    if not chunks:
        return False
    texts = [c[0] for c in chunks]
    metadatas = [c[1] for c in chunks]
    return add_documents(texts, metadatas)


def ensure_rag_context_loaded():
    """Call at startup or before first RAG query: load GitHub context into vector DB if empty."""
    store = get_or_create_vector_store()
    if store is None:
        return
    try:
        # If collection is empty or small, load from GitHub
        n = store._collection.count() if hasattr(store, "_collection") and hasattr(store._collection, "count") else 0
        if n < 3:
            load_github_context_into_store()
    except Exception:
        load_github_context_into_store()
