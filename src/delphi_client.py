"""
VeritasKernel — Delphi Prediction Market API Client
Implements Delphi Evidence Mining Protocol specs with strict idempotency and receipt tracking.
"""

import os
import time
import uuid
import json
import hashlib
from typing import Dict, List, Any, Optional

class DelphiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.delphi.fyi/v1",
        wallet_address: str = "0x8C64e8AB285F46cB22497f9B6Ce9DF42dDD19EcC",
        mock_mode: bool = False
    ):
        self.api_key = api_key or os.environ.get("DELPHI_API_KEY", "")
        self.base_url = base_url.rstrip('/')
        self.wallet_address = wallet_address
        # If no real API key is present yet (before Nov 23 release), run in simulated sandbox mode
        self.mock_mode = mock_mode or (not bool(self.api_key))

    def _get_headers(self, idempotency_key: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": "VeritasKernel/1.0",
            "X-Agent-ID": "VeritasKernel",
            "X-Harness": "Native-Autonomous-Sieve",
            "X-Model": "Hybrid-Mathematical-Entropy",
            "X-Wallet": self.wallet_address,
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def get_markets(self) -> List[Dict[str, Any]]:
        """
        Retrieves active Delphi prediction markets.
        In mock_mode, returns high-fidelity real-world test markets.
        """
        if self.mock_mode:
            return [
                {
                    "id": "delphi-mkt-01",
                    "question": "Will the SEC approve the first Solana Spot ETF before December 31, 2026?",
                    "category": "Crypto",
                    "odds_yes": 0.38,
                    "odds_no": 0.62,
                    "reward_pot_usdc": 1250.0,
                    "evidence_cutoff": "2026-12-10T17:00:00Z",
                    "status": "OPEN",
                    "keywords": ["SEC", "Solana", "ETF", "approval", "Gensler", "filing", "S-1"]
                },
                {
                    "id": "delphi-mkt-02",
                    "question": "Will the Federal Reserve cut the benchmark interest rate by 25bps at the next FOMC?",
                    "category": "Macro",
                    "odds_yes": 0.74,
                    "odds_no": 0.26,
                    "reward_pot_usdc": 2000.0,
                    "evidence_cutoff": "2026-12-08T17:00:00Z",
                    "status": "OPEN",
                    "keywords": ["Federal Reserve", "FOMC", "interest rate", "inflation", "Powell", "CPI"]
                },
                {
                    "id": "delphi-mkt-03",
                    "question": "Will SpaceX successfully land Starship Flight 8 booster on the launch tower?",
                    "category": "Technology",
                    "odds_yes": 0.61,
                    "odds_no": 0.39,
                    "reward_pot_usdc": 800.0,
                    "evidence_cutoff": "2026-12-05T17:00:00Z",
                    "status": "OPEN",
                    "keywords": ["SpaceX", "Starship", "booster", "catch", "Chopsticks", "FAA", "launch"]
                }
            ]

        import requests
        resp = requests.get(f"{self.base_url}/markets", headers=self._get_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json().get("markets", [])

    def submit_evidence(
        self,
        market_id: str,
        note: str,
        primary_link: str,
        direction: str,
        file_paths: Optional[List[str]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submits evidence to Delphi.
        Enforces idempotency headers and attaches up to 3 files.
        """
        if not idempotency_key:
            idempotency_key = f"idem_{market_id}_{hashlib.sha256(note.encode()).hexdigest()[:16]}"

        if self.mock_mode:
            # Simulate oracle verdict and instant reward receipt
            time.sleep(0.05) # simulate sub-100ms roundtrip
            has_pdf = any(f.endswith('.pdf') for f in (file_paths or []))
            base_reward = 35.0 if has_pdf else 15.0
            
            return {
                "status": "JUDGED",
                "receipt_id": f"rcpt_{uuid.uuid4().hex[:12]}",
                "market_id": market_id,
                "direction": direction,
                "judgment_reward_usdc": base_reward,
                "idempotency_key": idempotency_key,
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "forecaster_delta": "+0.082",
                "rationale": f"Verified primary evidence cited with {len(file_paths or [])} verified cryptographic attachment(s). Moved forecaster odds by +8.2% toward {direction.upper()}."
            }

        import requests
        headers = self._get_headers(idempotency_key=idempotency_key)
        payload = {
            "market_id": market_id,
            "direction": direction,
            "note": note,
            "links": [primary_link] if primary_link else []
        }

        # Multi-part file upload for dossiers
        files = []
        if file_paths:
            for p in file_paths[:3]: # Max 3 files per Delphi rules
                if os.path.exists(p):
                    files.append(("files", (os.path.basename(p), open(p, "rb"), "application/pdf")))

        resp = requests.post(f"{self.base_url}/submissions", headers=headers, data=payload, files=files if files else None, timeout=15)
        resp.raise_for_status()
        return resp.json()
