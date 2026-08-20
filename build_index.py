"""
Streams the case-law dataset row by row, discards cases that aren't useful
for this project, chunks the ones that pass, embeds the chunks, and writes
them into a local persistent Chroma vector store.

Nothing is bulk-downloaded: `streaming=True` pulls one row at a time from
Hugging Face, and any row that fails dedupe, the filters, or doesn't belong
to one of your configured target courts is discarded immediately -- it's
never written to disk or embedded.

Court targeting + per-court quotas live in config.py's court_quotas dict,
since each court needs its own number, not one flag. Edit that dict to
change which courts you want or how many cases per court.

Usage:
    python build_index.py
    python build_index.py --max-scanned 1000000 --since-year 2010
    python build_index.py --topic-keywords contract negligence
"""

import argparse
import json
import os
import time
from collections import defaultdict

from datasets import load_dataset
from sentence_transformers import SentenceTransformer
import chromadb
from tqdm import tqdm

from config import PipelineConfig
from filters import passes_filters, match_target_court
from chunker import chunk_text


def normalize(raw_row: dict, cfg: PipelineConfig) -> dict:
    """Map a raw HF row onto the pipeline's internal field names."""
    return {k: raw_row.get(v) for k, v in cfg.field_map.items()}


def build_arg_parser(cfg: PipelineConfig) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Stream, filter, chunk, and embed a legal case dataset.")
    p.add_argument("--dataset", default=cfg.dataset_name)
    p.add_argument("--split", default=cfg.dataset_split)
    p.add_argument("--max-scanned", type=int, default=cfg.max_scanned)
    p.add_argument("--since-year", type=int, default=cfg.since_year)
    p.add_argument("--topic-keywords", nargs="*", default=cfg.topic_keywords)
    return p


def main():
    cfg = PipelineConfig()
    args = build_arg_parser(cfg).parse_args()
    cfg.dataset_name = args.dataset
    cfg.dataset_split = args.split
    cfg.max_scanned = args.max_scanned
    cfg.since_year = args.since_year
    cfg.topic_keywords = args.topic_keywords

    os.makedirs(os.path.dirname(cfg.filtered_jsonl_path) or ".", exist_ok=True)
    os.makedirs(cfg.chroma_dir, exist_ok=True)

    print(f"Loading '{cfg.dataset_name}' (split={cfg.dataset_split}) in streaming mode...")
    stream = load_dataset(cfg.dataset_name, split=cfg.dataset_split, streaming=True)

    print(f"Loading embedding model '{cfg.embedding_model}'...")
    model = SentenceTransformer(cfg.embedding_model)

    client = chromadb.PersistentClient(path=cfg.chroma_dir)
    collection = client.get_or_create_collection(cfg.chroma_collection)

    print("Target courts and quotas:")
    for court, spec in cfg.court_quotas.items():
        print(f"    {spec['max_kept']:>5}  {court}")
    total_target = sum(spec["max_kept"] for spec in cfg.court_quotas.values())

    seen_hashes = set()
    court_counts = defaultdict(int)
    scanned = 0
    kept = 0
    total_chunks = 0

    batch_ids, batch_docs, batch_metas = [], [], []

    def flush_batch():
        nonlocal batch_ids, batch_docs, batch_metas, total_chunks
        if not batch_docs:
            return
        embeddings = model.encode(
            batch_docs, batch_size=cfg.embed_batch_size, show_progress_bar=False
        ).tolist()
        collection.add(ids=batch_ids, documents=batch_docs, metadatas=batch_metas, embeddings=embeddings)
        total_chunks += len(batch_docs)
        batch_ids, batch_docs, batch_metas = [], [], []

    def all_quotas_full() -> bool:
        return all(
            court_counts[c] >= spec["max_kept"] for c, spec in cfg.court_quotas.items()
        )

    start = time.time()
    fout = open(cfg.filtered_jsonl_path, "w", encoding="utf-8")
    pbar = tqdm(desc="Scanning cases", unit="row")

    for raw_row in stream:
        if scanned >= cfg.max_scanned or kept >= total_target:
            break
        scanned += 1
        pbar.update(1)
        if scanned % 5000 == 0 and all_quotas_full():
            break  # every target court has hit its quota -- no need to keep streaming

        row = normalize(raw_row, cfg)

        row_hash = row.get("hash")
        if row_hash:
            if row_hash in seen_hashes:
                continue  # exact duplicate, discard
            seen_hashes.add(row_hash)

        target_court = match_target_court(row.get("court"), cfg)
        if target_court is None:
            continue  # not one of the courts we're targeting, discard

        quota = cfg.court_quotas[target_court]["max_kept"]
        if court_counts[target_court] >= quota:
            continue  # this court already has its full quota

        if not passes_filters(row, cfg):
            continue  # fails length/date/topic checks, discard

        chunks = chunk_text(row["text"], cfg.chunk_size, cfg.chunk_overlap)
        if not chunks:
            continue

        court_counts[target_court] += 1
        kept += 1
        fout.write(json.dumps({
            "id": row["id"], "title": row["title"], "citation": row["citation"],
            "court": row["court"], "target_court": target_court, "date": row["date"],
            "num_chunks": len(chunks),
        }) + "\n")

        for i, chunk in enumerate(chunks):
            batch_ids.append(f"{row['id']}_{i}")
            batch_docs.append(chunk)
            batch_metas.append({
                "case_id": row["id"] or "",
                "title": row["title"] or "",
                "citation": row["citation"] or "",
                "docket_number": row["docket_number"] or "",
                "court": row["court"] or "",
                "target_court": target_court,
                "date": row["date"] or "",
                "chunk_index": i,
                "num_chunks": len(chunks),
            })

        if len(batch_docs) >= cfg.embed_batch_size:
            flush_batch()

    flush_batch()
    fout.close()
    pbar.close()

    elapsed = time.time() - start
    print("\nDone.")
    print(f"  Rows scanned:     {scanned}")
    print(f"  Cases kept:       {kept} / {total_target} target")
    print(f"  Chunks embedded:  {total_chunks}")
    print(f"  Time:             {elapsed:.1f}s")
    print(f"  Vector store:     {cfg.chroma_dir}  (collection='{cfg.chroma_collection}')")
    print(f"  Audit log:        {cfg.filtered_jsonl_path}")
    print("\n  Cases kept by court (target / actual):")
    for court, spec in cfg.court_quotas.items():
        actual = court_counts[court]
        flag = "  <-- short, raise --max-scanned or check keyword spelling" if actual < spec["max_kept"] else ""
        print(f"    {actual:>5} / {spec['max_kept']:<5} {court}{flag}")


if __name__ == "__main__":
    main()
