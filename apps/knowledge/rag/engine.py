"""
Document parsing, chunking, embedding, vector storage.
Zero heavy dependencies: numpy + custom splitter + cosine similarity.
"""

import json, re, shutil
from pathlib import Path
import numpy as np
from django.conf import settings
from openai import OpenAI


def get_embedding_client() -> OpenAI:
    return OpenAI(
        api_key=settings.SILICONFLOW_API_KEY,
        base_url=settings.SILICONFLOW_BASE_URL,
    )


# ── Vector store ─────────────────────────────────────────────────

class VectorStore:
    def __init__(self, kb_id: str):
        self.store_dir = Path(settings.CHROMA_PERSIST_DIR) / f"kb_{kb_id}"
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _load(self):
        cf = self.store_dir / "chunks.json"
        ef = self.store_dir / "embeddings.npy"
        if not cf.exists() or not ef.exists():
            return [], None
        return json.loads(cf.read_text(encoding="utf-8")), np.load(ef)

    def _save(self, chunks, emb):
        (self.store_dir / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
        np.save(self.store_dir / "embeddings.npy", emb)

    def add(self, doc_id, filename, chunks, embeddings):
        all_c, all_e = self._load()
        for i, (c, e) in enumerate(zip(chunks, embeddings)):
            all_c.append({"doc_id": doc_id, "filename": filename, "chunk_index": i, "content": c})
        new_e = np.array(embeddings) if all_e is None else np.vstack([all_e, embeddings])
        self._save(all_c, new_e)

    def remove_doc(self, doc_id):
        all_c, all_e = self._load()
        keep = [i for i, c in enumerate(all_c) if c["doc_id"] != doc_id]
        if not keep:
            shutil.rmtree(self.store_dir, ignore_errors=True)
            return
        self._save([all_c[i] for i in keep], all_e[keep])

    def query(self, q_emb, top_k=5):
        all_c, all_e = self._load()
        if all_e is None or len(all_c) == 0:
            return []
        q = np.array(q_emb)
        # 手写余弦相似度（不需要 sklearn）
        sims = np.dot(all_e, q) / (np.linalg.norm(all_e, axis=1) * np.linalg.norm(q) + 1e-10)
        top = np.argsort(sims)[::-1][:top_k]
        return [
            {"content": all_c[i]["content"][:500], "filename": all_c[i]["filename"], "chunk_index": all_c[i]["chunk_index"]}
            for i in top if sims[i] > 0.1
        ]

    def count(self):
        c, _ = self._load()
        return len(c) if c else 0


def delete_collection(kb_id):
    shutil.rmtree(Path(settings.CHROMA_PERSIST_DIR) / f"kb_{kb_id}", ignore_errors=True)

def get_store(kb_id):
    return VectorStore(kb_id)


# ── Parsing ──────────────────────────────────────────────────────

def parse_pdf(fp):
    from PyPDF2 import PdfReader
    return "\n\n".join(p.extract_text() or "" for p in PdfReader(str(fp)).pages)

def parse_docx(fp):
    from docx import Document
    return "\n\n".join(p.text for p in Document(str(fp)).paragraphs if p.text.strip())

def parse_txt(fp):
    return fp.read_text(encoding="utf-8", errors="replace")

PARSERS = {"pdf": parse_pdf, "docx": parse_docx, "doc": parse_docx, "txt": parse_txt, "md": parse_txt}

def parse_document(fp, ft):
    return PARSERS.get(ft.lower(), parse_txt)(fp)


# ── Chunking (纯 Python，无 langchain 依赖) ───────────────────────

def chunk_text(text, chunk_size=500, overlap=50):
    """Simple recursive splitter: paragraphs → sentences → chars."""
    if not text.strip():
        return []
    # 先按段落分
    paras = re.split(r'\n\s*\n', text)
    chunks = []
    buf = ""
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if len(buf) + len(p) + 1 <= chunk_size:
            buf = (buf + "\n\n" + p).strip()
        else:
            if buf:
                chunks.append(buf)
            # 如果单段太长，按句子切
            if len(p) > chunk_size:
                sents = re.split(r'(?<=[。.！!？?])\s*', p)
                sbuf = ""
                for s in sents:
                    if len(sbuf) + len(s) <= chunk_size:
                        sbuf += s
                    else:
                        if sbuf:
                            chunks.append(sbuf)
                        # 按字符强制切
                        for i in range(0, len(s), chunk_size - overlap):
                            chunks.append(s[i:i+chunk_size])
                        sbuf = ""
                if sbuf:
                    buf = sbuf
                else:
                    buf = ""
            else:
                buf = p
    if buf:
        chunks.append(buf)
    return [c for c in chunks if len(c) >= 10]


# ── Embedding ────────────────────────────────────────────────────

def embed_chunks(chunks):
    client = get_embedding_client()
    resp = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=chunks)
    return [d.embedding for d in resp.data]


# ── Retrieve ─────────────────────────────────────────────────────

def retrieve(kb_id, query, top_k=5):
    store = get_store(kb_id)
    if store.count() == 0:
        return []
    resp = get_embedding_client().embeddings.create(model=settings.EMBEDDING_MODEL, input=[query])
    return store.query(resp.data[0].embedding, top_k)


# ── Async task ───────────────────────────────────────────────────

def process_document_task(doc_id):
    from apps.knowledge.models import Document
    try:
        doc = Document.objects.get(id=doc_id)
    except Document.DoesNotExist:
        return
    doc.status = Document.Status.PROCESSING
    doc.save(update_fields=["status"])
    try:
        fp = Path(doc.file.path)
        content = parse_document(fp, doc.file_type)
        doc.content_text = content
        doc.save(update_fields=["content_text"])
        chunks = chunk_text(content)
        if not chunks:
            chunks = [content[:500]]
        embs = embed_chunks(chunks)
        get_store(str(doc.kb_id)).add(str(doc.id), doc.filename, chunks, embs)
        doc.chunk_count = len(chunks)
        doc.status = Document.Status.READY
        doc.save(update_fields=["chunk_count", "status"])
    except Exception as e:
        doc.status = Document.Status.ERROR
        doc.error_message = str(e)
        doc.save(update_fields=["status", "error_message"])

def remove_document_chunks(kb_id, doc_id):
    get_store(kb_id).remove_doc(doc_id)
