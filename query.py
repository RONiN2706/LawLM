"""
Quick sanity check / demo of the retrieval half of the RAG pipeline.
Run this after build_index.py has populated the Chroma store, to confirm
retrieval works before wiring it into Gemini's  generation step.
"""
import sys
import chromadb
from sentence_transformers import SentenceTransformer

from config import PipelineConfig


def main():
    cfg = PipelineConfig()
    query = " ".join(sys.argv[1:]) or "breach of contract damages"

    model = SentenceTransformer(cfg.embedding_model)
    client = chromadb.PersistentClient(path=cfg.chroma_dir)
    collection = client.get_or_create_collection(cfg.chroma_collection)

    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=5)

    print(f"Query: {query}\n")
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    if not docs:
        print("No results -- did build_index.py finish and write to the same chroma_dir?")
        return

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
        print(f"--- Result {i + 1} (distance={dist:.3f}) ---")
        print(f"{meta['title']}  |  {meta['court']}  |  {meta['date']}")
        print(f"citation: {meta['citation']}")
        print(doc[:400].replace("\n", " ") + "...")
        print()


if __name__ == "__main__":
    main()
