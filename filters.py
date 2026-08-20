"""
Row-level filters that decide whether to keep or delete a case.
"""

import re
from datetime import datetime
from typing import Optional

from config import PipelineConfig

_YEAR_RE = re.compile(r"(1[89]\d{2}|20\d{2})")


def _year_of(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y"):
        try:
            return datetime.strptime(date_str[: len(fmt) + 2], fmt).year
        except ValueError:
            continue
    m = _YEAR_RE.search(date_str)
    return int(m.group(1)) if m else None


def passes_filters(row: dict, cfg: PipelineConfig) -> bool:
    text = row.get("text") or ""

    if not (cfg.min_chars <= len(text) <= cfg.max_chars):
        return False

    if cfg.since_year is not None:
        year = _year_of(row.get("date"))
        if year is not None and year < cfg.since_year:
            return False

    if cfg.topic_keywords:
        haystack = f"{row.get('title', '')} {text[:3000]}".lower()
        if not any(k.lower() in haystack for k in cfg.topic_keywords):
            return False

    return True


def match_target_court(court_name: Optional[str], cfg: PipelineConfig) -> Optional[str]:
    """
    Returns the canonical key from cfg.court_quotas this row's court matches
    (e.g. "Supreme Court of India"), or None if it doesn't match any of your
    configured target courts.
    """
    if not court_name:
        return None
    haystack = court_name.lower()
    for canonical_name, spec in cfg.court_quotas.items():
        if any(keyword.lower() in haystack for keyword in spec["keywords"]):
            return canonical_name
    return None
