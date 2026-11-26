"""
VeritasKernel: Gemini Reasoning + Finnhub Real-Time Evidence Miner
Analyzes active Delphi prediction markets, matches breaking facts from Finnhub & web,
and dispatches high-conviction non-duplicate evidence to Delphi's oracle.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

DELPHI_KEY = os.environ.get("DELPHI_API_ACCESS_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY", "")

def call_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["candidates"][0]["content"]["parts"][0]["text"]

def get_finnhub_news():
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_delphi_markets():
    url = "https://competition.delphi.fyi/markets.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("==================================================")
    print("  VERITASKERNEL — GEMINI REASONING + FINNHUB MINER")
    print("==================================================")
    markets = get_delphi_markets()
    print(f"[+] Loaded {len(markets)} competition prediction markets.")
    
    news = get_finnhub_news()
    print(f"[+] Loaded {len(news)} real-time breaking news items from Finnhub.")
    
    # Select the top 5 markets closing within 5 days
    prompt = f"""You are the VeritasKernel Chief Prediction Market Analyst.
Below are active Yes/No prediction markets on Delphi:
{json.dumps([{'address': m['address'], 'question': m['question'], 'category': m['category'], 'closesAt': m['closesAt'], 'odds': m['odds']} for m in markets[:10]], indent=2)}

And here are recent breaking financial news headlines from Finnhub:
{json.dumps([{'headline': n['headline'], 'summary': n['summary'][:150], 'url': n['url'], 'datetime': n['datetime']} for n in news[:15]], indent=2)}

Task:
Identify which 2 prediction markets have the highest probability of being impacted by immediate upcoming economic/policy data, and outline the exact verifiable fact and query needed to mine non-duplicate evidence for each.
Return your answer in strictly valid JSON:
{{
  "targets": [
    {{
      "market_address": "0x...",
      "question": "string",
      "direction": "YES or NO",
      "reasoning": "Why this market is actionable right now",
      "search_query": "Exact terms to find the latest dated primary source"
    }}
  ]
}}
"""
    print("[*] Running Gemini 2.5 Flash Reasoning Engine...")
    t0 = time.time()
    plan_raw = call_gemini(prompt)
    print(f"[+] Gemini Analysis Complete ({round(time.time() - t0, 2)}s):\n")
    print(plan_raw)

if __name__ == "__main__":
    main()
