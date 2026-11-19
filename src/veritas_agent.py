"""
VeritasKernel — Autonomous Prediction Market Evidence Mining Orchestrator
Stitches Sieve Filtering, Cryptographic Fingerprinting, PDF Compilation, and Delphi Oracle Dispatch.
"""

import sys
import os
import time
from typing import Dict, List, Any, Optional

from src.sieve_engine import SieveEngine
from src.dedup_ledger import DedupLedger
from src.pdf_compiler import EvidencePDFCompiler
from src.delphi_client import DelphiClient

class VeritasAgent:
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        self.sieve = SieveEngine()
        self.ledger = DedupLedger()
        self.compiler = EvidencePDFCompiler()
        self.client = DelphiClient(api_key=api_key, mock_mode=mock_mode)

    def process_and_submit_lead(
        self,
        market: Dict[str, Any],
        raw_text: str,
        source_url: str,
        direction: str = "YES"
    ) -> Dict[str, Any]:
        """
        Executes the full end-to-end pipeline on an evidence lead:
        1. Sieve extracts facts and computes quality score
        2. Deduplication check prevents collisions and quota exhaustion
        3. ReportLab compiles 1-page Forensic PDF Dossier
        4. Delphi API client submits payload with Idempotency headers
        5. Receipt and reward logged
        """
        t0 = time.perf_counter_ns()
        market_id = market["id"]
        market_question = market["question"]
        keywords = market.get("keywords", [])

        # Stage 1: Sieve Information Filter
        signals = self.sieve.extract_evidence_signals(raw_text, keywords)
        if not signals["admissible"]:
            return {
                "success": False,
                "reason": f"SIEVE_REJECTED: {signals['rejection_reason']} (Score: {signals['quality_score']})",
                "signals": signals
            }

        primary_quote = signals["primary_quote"]
        date_anchor = signals["dates"][0] if signals["dates"] else ""

        # Stage 2: Deduplication & Quota Guard
        allowed, reason = self.ledger.can_submit(market_id, primary_quote, date_anchor)
        if not allowed:
            return {
                "success": False,
                "reason": f"LEDGER_REJECTED: {reason}",
                "signals": signals
            }

        # Stage 3: Fingerprint & Compile Cryptographic PDF Dossier
        fingerprint = self.ledger.compute_fingerprint(market_id, primary_quote, date_anchor)
        pdf_path = self.compiler.compile_dossier(
            market_id=market_id,
            market_question=market_question,
            direction=direction,
            source_url=source_url,
            primary_quote=primary_quote,
            dates=signals["dates"],
            metrics=signals["metrics"],
            quality_score=signals["quality_score"],
            fingerprint=fingerprint
        )

        # Stage 4: Record in Ledger (consumes slot)
        self.ledger.record_submission(
            market_id=market_id,
            primary_quote=primary_quote,
            date_anchor=date_anchor,
            metadata={"source_url": source_url, "pdf_path": pdf_path}
        )

        # Stage 5: Dispatch to Delphi Oracle
        submission_note = (
            f"[VERITASKERNEL AUDIT] Verified fact update for {market_question}: \"{primary_quote}\". "
            f"Sourced from {source_url} ({date_anchor}). Cryptographic dossier attached."
        )

        receipt = self.client.submit_evidence(
            market_id=market_id,
            note=submission_note,
            primary_link=source_url,
            direction=direction,
            file_paths=[pdf_path],
            idempotency_key=f"idem_{fingerprint[:16]}"
        )

        t1 = time.perf_counter_ns()
        total_latency_ms = (t1 - t0) / 1e6

        return {
            "success": True,
            "market_id": market_id,
            "quality_score": signals["quality_score"],
            "fingerprint": fingerprint,
            "pdf_dossier": pdf_path,
            "receipt": receipt,
            "total_latency_ms": round(total_latency_ms, 2)
        }
