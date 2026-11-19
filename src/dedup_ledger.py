"""
VeritasKernel — Cryptographic Deduplication & Anti-Collision Ledger
Enforces Delphi prediction market submission limits and prevents duplicate penalties.
"""

import hashlib
import json
import os
import time
from typing import Dict, Any, Tuple, Optional

class DedupLedger:
    def __init__(self, storage_path: str = "data/dedup_ledger.json"):
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self.market_submissions: Dict[str, int] = {}
        self.fingerprint_registry: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _normalize_text(self, text: str) -> str:
        """Strips punctuation, lowercases, and removes extra spaces for collision analysis."""
        return " ".join("".join(c.lower() if c.isalnum() else " " for c in text).split())

    def compute_fingerprint(self, market_id: str, primary_quote: str, date_anchor: str = "") -> str:
        """Generates canonical SHA-256 fingerprint for a market fact."""
        norm_quote = self._normalize_text(primary_quote)
        norm_date = self._normalize_text(date_anchor)
        payload = f"{market_id.strip()}::{norm_quote}::{norm_date}".encode('utf-8')
        return hashlib.sha256(payload).hexdigest()

    def can_submit(self, market_id: str, primary_quote: str, date_anchor: str = "") -> Tuple[bool, Optional[str]]:
        """
        Validates if this evidence can be submitted to Delphi without violating:
        1. Delphi per-market quota (Max 3 submissions per agent per market)
        2. Duplicate evidence collision (Repeated facts earn $0 and waste slots)
        """
        # Rule 1: Per-market quota check (max 3)
        current_count = self.market_submissions.get(market_id, 0)
        if current_count >= 3:
            return False, f"MARKET_QUOTA_REACHED (Max 3 submissions for market {market_id})"

        # Rule 2: Duplicate fact fingerprint check
        fp = self.compute_fingerprint(market_id, primary_quote, date_anchor)
        if fp in self.fingerprint_registry:
            existing = self.fingerprint_registry[fp]
            return False, f"DUPLICATE_FACT_COLLISION (Already recorded at {existing.get('timestamp')})"

        return True, None

    def record_submission(self, market_id: str, primary_quote: str, date_anchor: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Registers submission into ledger, consumes a quota slot, and returns the unique fingerprint.
        """
        allowed, reason = self.can_submit(market_id, primary_quote, date_anchor)
        if not allowed:
            raise ValueError(f"Cannot record submission: {reason}")

        fp = self.compute_fingerprint(market_id, primary_quote, date_anchor)
        now_iso = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

        self.market_submissions[market_id] = self.market_submissions.get(market_id, 0) + 1
        self.fingerprint_registry[fp] = {
            "market_id": market_id,
            "timestamp": now_iso,
            "date_anchor": date_anchor,
            "quote_snippet": primary_quote[:120],
            "metadata": metadata or {}
        }
        self._save()
        return fp

    def get_market_slot_count(self, market_id: str) -> int:
        return self.market_submissions.get(market_id, 0)

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.market_submissions = data.get("market_submissions", {})
                    self.fingerprint_registry = data.get("fingerprint_registry", {})
            except Exception:
                self.market_submissions = {}
                self.fingerprint_registry = {}

    def _save(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({
                    "market_submissions": self.market_submissions,
                    "fingerprint_registry": self.fingerprint_registry
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save dedup ledger: {e}")
