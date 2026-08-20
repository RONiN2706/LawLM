"""
Central configuration for the legal-case RAG ingestion pipeline.

Everything here is meant to be tweaked. This is set up for
KanoonGPT/indian-case-laws (~10.9GB streamed, 17.1M rows, single "train"
split -- no per-country splits). If you swap datasets, change dataset_name /
dataset_split and the values in field_map to match its actual column names;
nothing else in the pipeline needs to change.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CHROMA_DIR = (
    PROJECT_ROOT
    / "data"
    / "chroma_db-20260820T111802Z-1-001"
    / "chroma_db"
)


@dataclass
class PipelineConfig:
    # --- Source dataset (streamed, never downloaded in full) ---
    dataset_name: str = "KanoonGPT/indian-case-laws"
    dataset_split: str = "train"  # single split -- no per-country splits in this dataset

    # Maps the pipeline's internal field names -> actual column names in the
    # HF dataset. Change the values (right side) if you swap datasets.
    #
    # IMPORTANT: this dataset has NO full-judgment-text column. "indexable_text"
    # is a short auto-generated summary (148-975 chars: title/parties/court/
    # judge/date), not the opinion itself. The real text lives in the PDF/JSON
    # behind source_pdf_s3_url / source_json_s3_url. See the README note on
    # whether that's good enough for your demo or whether you need to fetch
    # and parse the PDFs too.
    field_map: dict = field(default_factory=lambda: {
        "id": "id",
        "title": "case_title",
        "text": "indexable_text",        # short summary -- see note above
        "citation": "neutral_citation",  # often null; law_report_citation is an alternative
        "docket_number": "docket_number",
        "court": "court_name",
        "date": "decision_date",
        "hash": "cnr_number",            # no hash column; CNR is India's unique case ID, works fine for dedupe
    })

    # --- Court targeting + per-court quotas ---
    # Only cases whose court_name matches one of these get kept -- this is
    # both your court filter AND your quota system in one place. `keywords`
    # is checked case-insensitively as a substring against court_name, so it
    # tolerates naming variants ("Bombay High Court" vs "High Court of
    # Bombay") since I couldn't confirm this dataset's exact court_name
    # strings ahead of time. Run a small smoke test (see README) and check
    # the end-of-run "kept by court" breakdown -- if a court you expected
    # shows 0, the dataset likely spells it differently; add that spelling
    # to its keyword list.
    court_quotas: Dict[str, dict] = field(default_factory=lambda: {
        "Supreme Court of India":  {"keywords": ["supreme court"], "max_kept": 5000},
        "Bombay High Court":       {"keywords": ["bombay high court", "high court of bombay"], "max_kept": 2000},
        "Calcutta High Court":     {"keywords": ["calcutta high court", "high court of calcutta"], "max_kept": 2000},
        "High Court of Delhi":     {"keywords": ["delhi high court", "high court of delhi"], "max_kept": 2000},
        "Madras High Court":       {"keywords": ["madras high court", "high court of madras"], "max_kept": 2000},
        "High Court of Karnataka": {"keywords": ["karnataka high court", "high court of karnataka"], "max_kept": 2000},
    })

    # --- Volume controls (this is what keeps you off the full 10.9GB download) ---
    max_scanned: int = 500_000  # hard stop: how many raw rows to stream before giving up.
    # Supreme Court cases are a sliver of 17.1M rows -- raise this if the
    # end-of-run summary shows you're short on Supreme Court cases.

    # --- Filtering (applies on top of the court quotas above) ---
    min_chars: int = 100               # indexable_text tops out around 975 chars -- don't set this too high
    max_chars: int = 2_000
    since_year: Optional[int] = 2000   # None disables the date filter
    topic_keywords: List[str] = field(default_factory=lambda: [])  # e.g. ["contract", "negligence"]; [] = no restriction

    # --- Chunking ---
    chunk_size: int = 1200  # characters
    chunk_overlap: int = 200

    # --- Embedding + storage ---
    embedding_model: str = "all-MiniLM-L6-v2"  # small, fast, runs fine on CPU
    embed_batch_size: int = 64
    chroma_dir: str = os.getenv("CHROMA_DIR", str(DEFAULT_CHROMA_DIR))
    chroma_collection: str = "legal_cases"
    filtered_jsonl_path: str = str(PROJECT_ROOT / "data" / "filtered_cases.jsonl")
