import os
from dotenv import load_dotenv
from pathlib import Path
from app.utils.config import BASE_DIR, DATA_DIR, EMBEDDING_MODEL, VECTOR_DB_DIR
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()


def resolve_rag_context_dir() -> Path:
    """Resolve the directory containing RAG source files.
    """
    env_value = os.getenv("WORKSPACE_FOLDER_PATH")

    if env_value:
        env_path = Path(os.getenv("WORKSPACE_FOLDER_PATH") + "/rag_context_data").expanduser().resolve()
        if env_path.exists() and env_path.is_dir():
            return env_path
    
    fallback = (Path(BASE_DIR) / "llm" / "workspace" / "rag_context_data").resolve()
    return fallback


def build_or_load_vectorstore(force_rebuild: bool = False) -> Chroma:
    """
    Loads the service knowledge docs, splits them, embeds them, and stores them
    in a local Chroma DB. Reuses the existing DB on disk unless force_rebuild=True
    or the DB doesn't exist yet.
    """
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    if os.path.isdir(VECTOR_DB_DIR) and not force_rebuild:
        return Chroma(persist_directory=str(VECTOR_DB_DIR), embedding_function=embeddings)

    rag_context_data_path = resolve_rag_context_dir()
    docs = []
    for fname in os.listdir(rag_context_data_path):
        if fname.endswith(".md"):
            loader = TextLoader(os.path.join(rag_context_data_path, fname), encoding="utf-8")
            docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(docs)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTOR_DB_DIR),
    )
    return vectorstore


def get_retriever(k: int = 4):
    vectorstore = build_or_load_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": k})


def get_vectorstore_summary() -> dict:
    """Return lightweight summary information about the current Chroma vector DB."""
    vectorstore = build_or_load_vectorstore()
    collection = getattr(vectorstore, "_collection", None)

    if collection is None:
        return {
            "vector_db_dir": str(VECTOR_DB_DIR),
            "document_count": 0,
            "total_characters": 0,
            "source_files": [],
            "sample_documents": [],
        }

    result = collection.get(include=["documents", "metadatas"])
    documents = result.get("documents", []) or []
    metadatas = result.get("metadatas", []) or []

    source_files = []
    for metadata in metadatas:
        if not isinstance(metadata, dict):
            continue
        source = metadata.get("source") or metadata.get("filename") or metadata.get("file")
        if source:
            source_files.append(os.path.basename(str(source)))

    sample_documents = []
    for index, document in enumerate(documents[:3]):
        cleaned = (document or "").replace("\n", " ").strip()
        sample_documents.append(
            {
                "index": index,
                "preview": cleaned[:200],
                "length": len(cleaned),
            }
        )

    return {
        "vector_db_dir": str(VECTOR_DB_DIR),
        "document_count": len(documents),
        "total_characters": sum(len(document or "") for document in documents),
        "source_files": sorted(set(source_files)),
        "sample_documents": sample_documents,
    }
