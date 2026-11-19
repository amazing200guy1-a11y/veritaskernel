"""
VeritasKernel — CLI Execution Runner
Autonomous Evidence Mining Engine for Delphi Prediction Markets (DoraHacks × Gensyn)
"""

import os
import sys
import argparse
import time

from src.veritas_agent import VeritasAgent
from src.delphi_client import DelphiClient

def banner():
    print("""
================================================================================
   _    __          _ _            __ __                     __
  | |  / /__  _____(_) /_____ _____/ //_/__  _________  ___  / /
  | | / / _ \\/ ___/ / __/ __ `/ ___/ ,< / _ \\/ ___/ __ \\/ _ \\/ / 
  | |/ /  __/ /  / / /_/ /_/ (__  ) /| /  __/ /  / / / /  __/ /  
  |___/\\___/_/  /_/\\__/\\__,_/____/_/ |_\\___/_/  /_/ /_/\\___/_/   
                                                                 
  Autonomous Evidence Mining & Forecasting Oracle Engine
  DoraHacks × Gensyn Delphi Agent Arena Competition 2026
  Author: Usman Bamidele · Pure Mathematics, FUNAAB
  Wallet: 0x8C64e8AB285F46cB22497f9B6Ce9DF42dDD19EcC
================================================================================
""")

def run_simulation():
    banner()
    print("[*] Initializing VeritasKernel in Autonomous Simulation Mode...")
    agent = VeritasAgent(mock_mode=True)
    markets = agent.client.get_markets()
    print(f"[*] Fetched {len(markets)} active Delphi Prediction Markets.\n")

    mock_leads = [
        {
            "market_id": "delphi-mkt-01",
            "text": "Washington D.C. — On November 18, 2026, the Securities and Exchange Commission (SEC) formally approved the amended S-1 registration statement for the Solana Spot ETF with a bipartisan vote tally of 4 to 1. The fund is expected to attract over $750 million in institutional seed liquidity during its first trading week.",
            "url": "https://sec.gov/news/press-release/2026-solana-etf-approved",
            "direction": "YES"
        },
        {
            "market_id": "delphi-mkt-02",
            "text": "Federal Reserve Chair Jerome Powell stated on November 17, 2026 that headline CPI inflation moderated to 2.1%, officially meeting the FOMC mandate and authorizing a 25bps interest rate reduction at the upcoming December monetary policy summit.",
            "url": "https://federalreserve.gov/newsevents/pressreleases/monetary20261117a.htm",
            "direction": "YES"
        },
        {
            "market_id": "delphi-mkt-03",
            "text": "Starbase, Texas — November 19, 2026: SpaceX successfully conducted a 33-engine static fire test of Super Heavy Booster 15. The FAA officially issued the commercial launch license approving mechanical tower catch operations.",
            "url": "https://spaceflightnow.com/2026/11/starship-flight-8-tower-catch-approved",
            "direction": "YES"
        }
    ]

    total_usdc_bounties = 0.0

    for idx, lead in enumerate(mock_leads, 1):
        target_mkt = next(m for m in markets if m["id"] == lead["market_id"])
        print(f"--------------------------------------------------------------------------------")
        print(f"[{idx}/{len(mock_leads)}] MINING MARKET: {target_mkt['question']}")
        print(f"    Category: {target_mkt['category']} | Reward Pot: ${target_mkt['reward_pot_usdc']:,.2f} USDC")
        print(f"    Source Lead: {lead['url']}")
        
        t0 = time.perf_counter()
        res = agent.process_and_submit_lead(
            market=target_mkt,
            raw_text=lead["text"],
            source_url=lead["url"],
            direction=lead["direction"]
        )
        t_elap = (time.perf_counter() - t0) * 1000

        if res["success"]:
            reward = res["receipt"]["judgment_reward_usdc"]
            total_usdc_bounties += reward
            print(f"    [+] STATUS: EVIDENCE ACCEPTED & JUDGED")
            print(f"    [+] Quality Score: {res['quality_score']}/100 | Sieve Latency: {res['total_latency_ms']} ms")
            print(f"    [+] Forensic Dossier: {res['pdf_dossier']}")
            print(f"    [+] Receipt ID: {res['receipt']['receipt_id']}")
            print(f"    [+] Forecaster Delta: {res['receipt']['forecaster_delta']}")
            print(f"    [+] Earned Judgment Reward: ${reward:.2f} USDC.e")
        else:
            print(f"    [-] STATUS: REJECTED: {res['reason']}")

    print("\n================================================================================")
    print(f"SIMULATION RUN COMPLETE")
    print(f"Total Evidentiary Dossiers Compiled: {len(mock_leads)}")
    print(f"Total Judgment Rewards Earned: ${total_usdc_bounties:.2f} USDC.e")
    print(f"Target Wallet: 0x8C64e8AB285F46cB22497f9B6Ce9DF42dDD19EcC")
    print("================================================================================")

def main():
    parser = argparse.ArgumentParser(description="VeritasKernel Delphi Evidence Mining Agent")
    parser.add_argument("--simulate", action="store_true", help="Run full evidence mining simulation across test markets")
    parser.add_argument("--markets", action="store_true", help="List active Delphi prediction markets")
    parser.add_argument("--live", action="store_true", help="Execute live evidence mining against production Delphi endpoints")
    args = parser.parse_args()

    if args.simulate or len(sys.argv) == 1:
        run_simulation()
    elif args.markets:
        agent = VeritasAgent(mock_mode=True)
        markets = agent.client.get_markets()
        print(f"Found {len(markets)} markets:")
        for m in markets:
            print(f" - [{m['id']}] {m['question']} (${m['reward_pot_usdc']} USDC)")

if __name__ == "__main__":
    main()
