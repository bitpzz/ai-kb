"""
Document parsing, chunking, embedding, and ChromaDB storage.
"""

import os
import uuid
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from django.conf import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI

# ── ChromaDB client (lazy init) ──────────────────────────────────
_chroma_client = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        chroma_dir = str(settings.CHROMA_PERSIST_DIR)
        os.makedirs(chroma_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_collection_name(kb_id: str) -> str:
    """Each knowledge base gets its own Chroma collection."""
    return f"kb_{kb_id}"


def get_or_create_collection(kb_id: str):
    client = get_chroma_client()
    name = get_collection_name(kb_id)
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(name)


def delete_collection(kb_id: str):
    """Remove a collection from ChromaDB."""
    client = get_chroma_client()
    name = get_collection_name(kb_id)
    try:
        client.delete_collection(name)
    except Exception:
        pass


def get_embedding_client() -> OpenAI:
    return OpenAI(
        api_key=settings.SILICONFLOW_API_KEY,
        base_url=settings.SILICONFLOW_BASE_URL,
    )


# ── Parsing ──────────────────────────────────────────────────────

def parse_pdf(file_path: Path) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(str(file_path))
    text_parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t)
    return "\n\n".join(text_parts)


def parse_docx(file_path: Path) -> str:
    from docx import Document

    doc = Document(str(file_path))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="replace")


PARSERS = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "doc": parse_docx,
    "txt": parse_txt,
    "md": parse_txt,
}


def parse_document(file_path: Path, file_type: str) -> str:
    parser = PARSERS.get(file_type.lower(), parse_txt)
    return parser(file_path)


# ── Chunking ─────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    return splitter.split_text(text)


# ── Embedding ────────────────────────────────────────────────────

@dataclass
class ChunkWithMeta:
    chunk_index: int
    content: str
    filename: str


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Batch embed chunks using SiliconFlow embedding API."""
    client = get_embedding_client()
    resp = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=chunks,
    )
    return [d.embedding for d in resp.data]


# ── Store ────────────────────────────────────────────────────────

def store_document_chunks(
    kb_id: str,
    doc_id: str,
    filename: str,
    chunks: list[str],
    embeddings: list[list[float]],
):
    """Store chunks + embeddings into ChromaDB."""
    collection = get_or_create_collection(kb_id)
    n = len(chunks)
    collection.add(
        ids=[f"{doc_id}_{i}" for i in range(n)],
        embeddings=embeddings,
        documents=chunks,
        metadatas=[
            {"doc_id": doc_id, "filename": filename, "chunk_index": i}
            for i in range(n)
        ],
    )


def remove_document_chunks(kb_id: str, doc_id: str):
    """Remove all chunks for a document from ChromaDB."""
    collection = get_or_create_collection(kb_id)
    try:
        results = collection.get(
            where={"doc_id": doc_id},
        )
        ids = results.get("ids", [])
        if ids:
            collection.delete(ids=ids)
    except Exception:
        pass


# ── Retrieve ─────────────────────────────────────────────────────

def retrieve(kb_id: str, query: str, top_k: int = 5) -> list[dict]:
    """Retrieve top-K relevant chunks for a query.

    Returns list of {"content": ..., "filename": ..., "chunk_index": ...}
    """
    collection = get_or_create_collection(kb_id)
    if collection.count() == 0:
        return []

    client = get_embedding_client()
    resp = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=[query],
    )
    query_embedding = resp.data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    sources = []
    if results["documents"] and results["documents"][0]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            sources.append({
                "content": doc[:500],  # truncate for context
                "filename": meta.get("filename", ""),
                "chunk_index": meta.get("chunk_index", 0),
            })
    return sources


# ── Full pipeline (called by django-q async task) ─────────────────

def process_document_task(doc_id: str):
    """Async task: parse → chunk → embed → store → update status."""
    from apps.knowledge.models import Document

    try:
        doc = Document.objects.get(id=doc_id)
    except Document.DoesNotExist:
        return

    doc.status = Document.Status.PROCESSING
    doc.save(update_fields=["status"])

    try:
        file_path = Path(doc.file.path)
        content = parse_document(file_path, doc.file_type)
        doc.content_text = content
        doc.save(update_fields=["content_text"])

        chunks = chunk_text(content)
        if not chunks:
            chunks = [content[:500]]  # fallback

        embeddings = embed_chunks(chunks)

        store_document_chunks(
            kb_id=str(doc.kb_id),
            doc_id=str(doc.id),
            filename=doc.filename,
            chunks=chunks,
            embeddings=embeddings,
        )

        doc.chunk_count = len(chunks)
        doc.status = Document.Status.READY
        doc.save(update_fields=["chunk_count", "status"])

    except Exception as e:
        doc.status = Document.Status.ERROR
        doc.error_message = str(e)
        doc.save(update_fields=["status", "error_message"])
        raise
