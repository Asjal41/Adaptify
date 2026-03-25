"""
Simple text-based vector store replacement.
Uses basic keyword matching instead of ChromaDB to avoid C++ build dependency.
"""

import json
import os
from pathlib import Path

STORE_DIR = os.path.join(os.path.dirname(__file__), "material_store")
Path(STORE_DIR).mkdir(exist_ok=True)


def add_material(material_id: int, text: str, chunk_size: int = 500):
    """Split text into chunks and save to a JSON file."""
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    if not chunks:
        return
    store_path = os.path.join(STORE_DIR, f"mat_{material_id}.json")
    with open(store_path, "w", encoding="utf-8") as f:
        json.dump({"material_id": material_id, "chunks": chunks}, f, ensure_ascii=False)


def query_material(query: str, material_id: int | None = None, n_results: int = 5) -> list[str]:
    """Simple keyword-based retrieval from stored material chunks."""
    try:
        results = []
        query_words = set(query.lower().split())

        if material_id:
            files = [os.path.join(STORE_DIR, f"mat_{material_id}.json")]
        else:
            files = [os.path.join(STORE_DIR, f) for f in os.listdir(STORE_DIR) if f.endswith(".json")]

        for filepath in files:
            if not os.path.exists(filepath):
                continue
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for chunk in data["chunks"]:
                chunk_lower = chunk.lower()
                score = sum(1 for w in query_words if w in chunk_lower)
                if score > 0:
                    results.append((score, chunk))

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in results[:n_results]]

    except Exception:
        return []


def delete_material(material_id: int):
    """Delete stored chunks for a given material_id."""
    try:
        store_path = os.path.join(STORE_DIR, f"mat_{material_id}.json")
        if os.path.exists(store_path):
            os.remove(store_path)
    except Exception:
        pass
