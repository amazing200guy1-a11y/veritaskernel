"""
VeritasKernel — Comprehensive Automated Test Suite
Verifies Sieve Information Density, Deduplication Collision Guards,
Cryptographic PDF Dossier Compilation, and Delphi API Protocol Handshakes.
"""

import os
import sys
import unittest
import shutil

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sieve_engine import SieveEngine
from src.dedup_ledger import DedupLedger
from src.pdf_compiler import EvidencePDFCompiler
from src.delphi_client import DelphiClient
from src.veritas_agent import VeritasAgent

class TestVeritasKernel(unittest.TestCase):
    def setUp(self):
        self.test_data_dir = "test_data"
        os.makedirs(self.test_data_dir, exist_ok=True)
        self.test_ledger_path = os.path.join(self.test_data_dir, "test_ledger.json")
        self.test_dossier_dir = os.path.join(self.test_data_dir, "dossiers")
        if os.path.exists(self.test_ledger_path):
            os.remove(self.test_ledger_path)

    def tearDown(self):
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir, ignore_errors=True)

    def test_01_sieve_high_density_extraction(self):
        """Test sieve correctly extracts dates, metrics, and achieves admissible quality score."""
        sieve = SieveEngine()
        sample_news = (
            "Washington D.C. — On November 18, 2026, the Securities and Exchange Commission (SEC) "
            "formally approved the amended S-1 registration statement for the Solana Spot ETF with a "
            "bipartisan vote tally of 4 to 1. The fund is expected to attract over $750 million in "
            "institutional seed liquidity during its first trading week."
        )
        keywords = ["SEC", "Solana", "ETF", "approval", "S-1"]
        res = sieve.extract_evidence_signals(sample_news, keywords)

        self.assertTrue(res["admissible"], "High-density news must be deemed admissible")
        self.assertGreaterEqual(res["quality_score"], 60.0)
        self.assertIn("November 18, 2026", res["dates"])
        self.assertTrue(any("$750 million" in m or "4 to 1" in m for m in res["metrics"]))
        self.assertLess(res["latency_us"], 5000.0, "Sieve extraction must complete under 5ms")

    def test_02_sieve_rejects_empty_and_noise(self):
        """Test sieve rejects boilerplate cookie policies and empty payloads."""
        sieve = SieveEngine()
        noise = "All rights reserved. Accept our cookie policy and terms of service. Subscribe to read more."
        res = sieve.extract_evidence_signals(noise, ["Solana", "ETF"])
        self.assertFalse(res["admissible"])
        self.assertEqual(res["rejection_reason"], "LOW_EVIDENCE_DENSITY")

    def test_03_dedup_collision_prevention(self):
        """Test that submitting identical facts causes a duplicate collision block."""
        ledger = DedupLedger(storage_path=self.test_ledger_path)
        market_id = "delphi-mkt-01"
        quote = "SEC approved the amended S-1 registration statement for the Solana Spot ETF."
        date = "November 18, 2026"

        # First check: must be allowed
        allowed, reason = ledger.can_submit(market_id, quote, date)
        self.assertTrue(allowed)
        self.assertIsNone(reason)

        # Record submission
        fp = ledger.record_submission(market_id, quote, date)
        self.assertTrue(isinstance(fp, str) and len(fp) == 64)

        # Second check with same fact: MUST be rejected
        allowed2, reason2 = ledger.can_submit(market_id, quote, date)
        self.assertFalse(allowed2)
        self.assertIn("DUPLICATE_FACT_COLLISION", reason2)

    def test_04_per_market_quota_limit(self):
        """Test strict enforcement of Delphi's max 3 submissions per market rule."""
        ledger = DedupLedger(storage_path=self.test_ledger_path)
        market_id = "delphi-mkt-02"

        # Submit 3 distinct facts
        for i in range(3):
            quote = f"Unique economic indicator metric fact #{i} with CPI inflation data."
            allowed, _ = ledger.can_submit(market_id, quote, f"2026-11-0{i+1}")
            self.assertTrue(allowed, f"Submission {i+1} must be permitted")
            ledger.record_submission(market_id, quote, f"2026-11-0{i+1}")

        self.assertEqual(ledger.get_market_slot_count(market_id), 3)

        # 4th submission must be rejected
        allowed_4, reason_4 = ledger.can_submit(market_id, "4th fact beyond quota", "2026-11-04")
        self.assertFalse(allowed_4)
        self.assertIn("MARKET_QUOTA_REACHED", reason_4)

    def test_05_forensic_pdf_dossier_generation(self):
        """Test that EvidencePDFCompiler generates a valid PDF document with integrity seal."""
        compiler = EvidencePDFCompiler(output_dir=self.test_dossier_dir)
        pdf_path = compiler.compile_dossier(
            market_id="delphi-mkt-01",
            market_question="Will the SEC approve Solana Spot ETF before Dec 31, 2026?",
            direction="YES",
            source_url="https://sec.gov/news/press-release/2026-solana-etf",
            primary_quote="The Commission has formally granted approval under Rule 19b-4 for Solana ETF listing.",
            dates=["November 18, 2026"],
            metrics=["approved", "$750 million"],
            quality_score=85.0,
            fingerprint="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

        self.assertTrue(os.path.exists(pdf_path), "Generated PDF file must exist")
        file_size = os.path.getsize(pdf_path)
        self.assertGreater(file_size, 3000, "PDF file size must be substantial (>3KB)")

        with open(pdf_path, 'rb') as f:
            header = f.read(5)
            self.assertEqual(header, b'%PDF-', "File must have valid PDF magic bytes")

    def test_06_delphi_client_idempotency(self):
        """Test that Delphi client injects proper headers and generates reproducible idempotency keys."""
        client = DelphiClient(mock_mode=True)
        markets = client.get_markets()
        self.assertGreaterEqual(len(markets), 3)

        receipt = client.submit_evidence(
            market_id="delphi-mkt-01",
            note="Test evidence submission",
            primary_link="https://reuters.com/markets/crypto-update",
            direction="YES",
            file_paths=["dummy_dossier.pdf"]
        )

        self.assertEqual(receipt["status"], "JUDGED")
        self.assertGreater(receipt["judgment_reward_usdc"], 0)
        self.assertTrue(receipt["idempotency_key"].startswith("idem_"))

    def test_07_veritas_agent_end_to_end_pipeline(self):
        """Test full autonomous pipeline from raw lead to oracle receipt and dossier."""
        agent = VeritasAgent(mock_mode=True)
        market = {
            "id": "delphi-mkt-03",
            "question": "Will SpaceX successfully land Starship Flight 8 booster on the launch tower?",
            "keywords": ["SpaceX", "Starship", "booster", "catch", "Chopsticks"]
        }
        lead_text = (
            "Boca Chica, Texas — On November 19, 2026, SpaceX successfully conducted a full-duration static "
            "fire test of Super Heavy Booster 15. The FAA officially issued the modified commercial launch license "
            "approving tower catch operations with mechanical Chopsticks arms."
        )
        source_url = "https://spaceflightnow.com/2026/11/starship-flight-8-update"

        res = agent.process_and_submit_lead(
            market=market,
            raw_text=lead_text,
            source_url=source_url,
            direction="YES"
        )

        self.assertTrue(res["success"], f"End-to-end execution must succeed: {res}")
        self.assertGreaterEqual(res["quality_score"], 50.0)
        self.assertTrue(os.path.exists(res["pdf_dossier"]))
        self.assertEqual(res["receipt"]["status"], "JUDGED")
        self.assertLess(res["total_latency_ms"], 1000.0, "Total pipeline must execute in under 1 second")

if __name__ == "__main__":
    unittest.main()
