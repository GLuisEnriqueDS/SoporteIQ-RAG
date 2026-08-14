import hashlib
import json

import chromadb
from langchain_chroma import Chroma
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import config

_embeddings = None
_hybrid_retriever = None
_vectorstore = None
_chroma_client = None


def _load_entries() -> list[dict]:
    with open(config.KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _content_hash(entries: list[dict]) -> str:
    raw = json.dumps(entries, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _build_documents(entries: list[dict]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    documents = []
    for entry in entries:
        pregunta = entry["pregunta"]
        respuesta = entry["respuesta"]
        keywords = ", ".join(entry.get("palabras_clave", []))
        base_metadata = {
            "id": entry["id"],
            "categoria": entry["categoria"],
            "pregunta": pregunta,
        }

        if len(respuesta) <= config.CHUNK_SPLIT_THRESHOLD:
            content = f"Pregunta: {pregunta}\nPalabras clave: {keywords}\nRespuesta: {respuesta}"
            documents.append(
                Document(
                    page_content=content,
                    metadata={**base_metadata, "respuesta": respuesta, "chunk": 0},
                )
            )
            continue

        # Respuesta larga: se trocea, pero cada fragmento conserva la
        # pregunta como prefijo para no perder contexto al recuperarlo.
        partes = splitter.split_text(respuesta)
        for i, parte in enumerate(partes):
            content = f"Pregunta: {pregunta}\nPalabras clave: {keywords}\nRespuesta (parte {i + 1}/{len(partes)}): {parte}"
            documents.append(
                Document(
                    page_content=content,
                    metadata={**base_metadata, "respuesta": parte, "chunk": i},
                )
            )

    return documents


def _resolve_local_model_path(model_name: str) -> str:
    from huggingface_hub import snapshot_download
    from huggingface_hub.utils import LocalEntryNotFoundError

    try:
        return snapshot_download(model_name, local_files_only=True)
    except LocalEntryNotFoundError:
        return model_name


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        model_path = _resolve_local_model_path(config.EMBEDDINGS_MODEL)
        _embeddings = HuggingFaceEmbeddings(model_name=model_path)
    return _embeddings


def _get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        config.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(config.CHROMA_PERSIST_DIR))
    return _chroma_client


def _load_or_build_vectorstore(documents: list[Document], content_hash: str) -> Chroma:
    hash_marker = config.CHROMA_PERSIST_DIR / "content.hash"

    vectorstore = Chroma(
        client=_get_chroma_client(),
        collection_name=config.CHROMA_COLLECTION_NAME,
        embedding_function=_get_embeddings(),
        collection_metadata={"hnsw:space": "cosine"},
    )

    needs_rebuild = (
        not hash_marker.exists() or hash_marker.read_text(encoding="utf-8") != content_hash
    )

    if needs_rebuild:
        existing_ids = vectorstore.get()["ids"]
        if existing_ids:
            vectorstore.delete(ids=existing_ids)
        ids = [f"{doc.metadata['id']}::{doc.metadata['chunk']}" for doc in documents]
        vectorstore.add_documents(documents, ids=ids)
        hash_marker.write_text(content_hash, encoding="utf-8")

    return vectorstore


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        entries = _load_entries()
        documents = _build_documents(entries)
        _vectorstore = _load_or_build_vectorstore(documents, _content_hash(entries))
    return _vectorstore


def get_hybrid_retriever() -> EnsembleRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is not None:
        return _hybrid_retriever

    entries = _load_entries()
    documents = _build_documents(entries)

    vectorstore = get_vectorstore()
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": config.RETRIEVAL_K})

    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = config.RETRIEVAL_K

    _hybrid_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[config.VECTOR_WEIGHT, config.BM25_WEIGHT],
    )
    return _hybrid_retriever
