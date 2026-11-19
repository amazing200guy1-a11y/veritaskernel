"""
VeritasKernel — High-Throughput Information Sieve Engine
Optimized for Delphi Prediction Market Evidence Mining.

Extracts dated, sourced, and quantitative facts from unstructured text
at sub-millisecond speeds, filtering noise before dispatching to oracle judges.
"""

import re
import math
import time
from typing import Dict, List, Any, Optional

class SieveEngine:
    def __init__(self):
        # Precompiled regex patterns for high-throughput microsecond matching
        self.date_patterns = [
            re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b', re.IGNORECASE),
            re.compile(r'\b\d{4}-\d{2}-\d{2}\b'), # ISO 8601
            re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b'),
            re.compile(r'\b(?:yesterday|today|earlier today|this morning|overnight)\b', re.IGNORECASE),
            re.compile(r'\b(?:Q[1-4]|H[1-2])\s+\d{4}\b', re.IGNORECASE),
        ]
        
        self.metric_patterns = [
            re.compile(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|trillion|M|B|T))?\b', re.IGNORECASE),
            re.compile(r'\b\d+(?:\.\d+)?%\b'), # Percentages
            re.compile(r'\b(?:approved|rejected|dismissed|settled|enacted|signed|passed|vetoed|issued|granted|authorized|conducted|completed|launched)\b', re.IGNORECASE),
            re.compile(r'\b(?:license|permit|order|filing|statement|ruling|indictment|consensus|quorum|injunction|verdict)\b', re.IGNORECASE),
            re.compile(r'\b(?:vote|votes|tally|poll)\s+(?:of\s+)?\d+[\s\-\–to]+\d+\b', re.IGNORECASE),
        ]
        
        # Stop-words and boilerplate to penalize
        self.noise_pattern = re.compile(
            r'(?:cookie\s+policy|terms\s+of\s+service|subscribe\s+to\s+read|all\s+rights\s+reserved|sign\s+up\s+for\s+free)',
            re.IGNORECASE
        )

    def extract_evidence_signals(self, raw_text: str, market_keywords: List[str]) -> Dict[str, Any]:
        """
        Parses text and extracts factual evidence signals matching the target market.
        Returns extracted dates, metrics, relevant sentences, and an Evidence Quality Score.
        """
        t0 = time.perf_counter_ns()
        
        if not raw_text or len(raw_text.strip()) == 0:
            return {
                "quality_score": 0.0,
                "dates": [],
                "metrics": [],
                "primary_quote": "",
                "latency_us": 0.0,
                "admissible": False,
                "rejection_reason": "EMPTY_PAYLOAD"
            }

        # Clean noise
        cleaned_text = self.noise_pattern.sub('', raw_text)
        sentences = [s.strip() for s in re.split(r'[.\n!?;]+', cleaned_text) if len(s.strip()) > 20]

        extracted_dates = []
        extracted_metrics = []
        candidate_sentences = []

        # Find all temporal and quantitative tokens
        for pat in self.date_patterns:
            matches = pat.findall(cleaned_text)
            extracted_dates.extend(matches)

        for pat in self.metric_patterns:
            matches = pat.findall(cleaned_text)
            extracted_metrics.extend(matches)

        # De-duplicate while preserving order
        extracted_dates = list(dict.fromkeys(extracted_dates))
        extracted_metrics = list(dict.fromkeys(extracted_metrics))

        # Sentence relevance scoring
        keyword_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in market_keywords if len(kw) > 2]
        
        for sent in sentences:
            kw_hits = sum(1 for kp in keyword_patterns if kp.search(sent))
            has_date = any(dp.search(sent) for dp in self.date_patterns)
            has_metric = any(mp.search(sent) for mp in self.metric_patterns)

            score = (kw_hits * 3.0) + (4.0 if has_date else 0.0) + (3.0 if has_metric else 0.0)
            if score >= 4.0:
                candidate_sentences.append((score, sent))

        # Sort candidate sentences by information density
        candidate_sentences.sort(key=lambda x: x[0], reverse=True)
        primary_quote = candidate_sentences[0][1] if candidate_sentences else (sentences[0] if sentences else "")

        # Compute Evidence Quality Score (0 to 100)
        # Factors: Date presence (25%), Metric/Decision presence (35%), Keyword relevance (40%)
        date_score = min(25.0, len(extracted_dates) * 20.0)
        metric_score = min(35.0, len(extracted_metrics) * 12.0)
        relevance_score = min(40.0, len(candidate_sentences) * 15.0)
        quality_score = date_score + metric_score + relevance_score

        t1 = time.perf_counter_ns()
        latency_us = (t1 - t0) / 1000.0

        admissible = quality_score >= 40.0 and len(primary_quote) > 25

        return {
            "quality_score": round(quality_score, 2),
            "dates": extracted_dates[:5],
            "metrics": extracted_metrics[:8],
            "primary_quote": primary_quote,
            "latency_us": round(latency_us, 2),
            "admissible": admissible,
            "rejection_reason": None if admissible else "LOW_EVIDENCE_DENSITY"
        }
