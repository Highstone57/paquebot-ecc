#!/usr/bin/env python3
"""Moteur RAG local léger — embeddings + similarité vectorielle."""
import os, json, hashlib
from pathlib import Path
import numpy as np
import httpx

EMBEDDING_MODEL = "nomic-embed-text:latest"
OLLAMA_HOST = "http://localhost:11434"
DATA_FILE = os.path.expanduser("~/.hermes/rag_cache.json")

_cache = {"chunks": [], "vectors": None, "loaded": False}


def _embed(texts: list[str]) -> list[list[float]]:
    """Embedding via Ollama."""
    resp = httpx.post(f"{OLLAMA_HOST}/api/embed", json={
        "model": EMBEDDING_MODEL, "input": texts
    }, timeout=30)
    return resp.json().get("embeddings", [])


def index_dir(path: str):
    """Indexe tous les .md d'un dossier."""
    files = list(Path(path).rglob("*.md"))
    chunks = []
    for fp in files:
        try:
            text = fp.read_text("utf-8", errors="ignore").strip()
            if len(text) < 30: continue
            # Découpe en chunks de ~500 mots
            words = text.split()
            for i in range(0, len(words), 500):
                chunk = " ".join(words[i:i+500])
                chunks.append({"file": str(fp), "text": chunk,
                               "hash": hashlib.md5(chunk.encode()).hexdigest()})
        except: pass
    return chunks


def build_index(paths: list[str]):
    """Indexe plusieurs dossiers et sauvegarde."""
    all_chunks = []
    for p in paths:
        if os.path.isdir(p):
            c = index_dir(p)
            all_chunks.extend(c)
            print(f"[RAG] {os.path.basename(p)}: {len(c)} chunks")
    print(f"[RAG] Embedding {len(all_chunks)} chunks...")
    texts = [c["text"] for c in all_chunks]
    vecs = _embed(texts)
    data = {"chunks": all_chunks, "vectors": vecs}
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"[RAG] ✓ Sauvegardé: {len(all_chunks)} chunks dans {DATA_FILE}")
    return data


def load_index() -> dict:
    """Charge l'index."""
    global _cache
    if _cache["loaded"]:
        return _cache
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            data = json.load(f)
        _cache = data
        _cache["loaded"] = True
        print(f"[RAG] Index chargé: {len(data['chunks'])} chunks")
        return data
    return {"chunks": [], "vectors": []}


def search(query: str, top_k: int = 5) -> list[dict]:
    """Recherche les chunks les plus similaires."""
    data = load_index()
    if not data["vectors"]:
        return [{"text": "Aucun index. Lance index_all() d'abord.", "score": 0}]
    qvec = _embed([query])[0]
    scores = []
    for vec in data["vectors"]:
        sim = np.dot(qvec, vec) / (np.linalg.norm(qvec) * np.linalg.norm(vec))
        scores.append(sim)
    idx = np.argsort(scores)[-top_k:][::-1]
    results = []
    for i in idx:
        results.append({
            "text": data["chunks"][i]["text"][:200],
            "file": data["chunks"][i]["file"],
            "score": round(scores[i], 3),
        })
    return results


def index_all():
    """Indexe tous les dossiers utilisateur."""
    build_index([
        os.path.expanduser("~/IDO"),
        os.path.expanduser("~/CERVEAU"),
        os.path.expanduser("~/dev/Paquebot-OS"),
        os.path.expanduser("~/dev/personal-agent-os"),
    ])