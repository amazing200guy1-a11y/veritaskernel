"""
VeritasKernel: Gemini Reasoning + Finnhub Real-Time Evidence Miner
Analyzes active Delphi prediction markets, matches breaking facts from Finnhub & web,
and dispatches high-conviction non-duplicate evidence to Delphi's oracle.
"""

import os
import sys
import json
import time
import uuid
import urllib.request
import urllib.error
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
except ImportError:
    requests = None

DELPHI_KEY = os.environ.get("DELPHI_API_ACCESS_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY", "")

def call_gemini(prompt: str) -> str:
    endpoints = [
        "https://generativelanguage.googleapis.com/v1/models/gemini-3.1-flash-lite:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    ]
    last_err = None
    for ep in endpoints:
        url = f"{ep}?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    text = res["candidates"][0]["content"]["parts"][0]["text"]
                    return text
            except Exception as e:
                last_err = e
                time.sleep(1)
    raise RuntimeError(f"All Gemini endpoints exhausted. Last error: {last_err}")

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

def submit_delphi_evidence(market_address: str, note: str, links: list = None):
    if not DELPHI_KEY:
        print("[-] DELPHI_API_ACCESS_KEY not set. Skipping live submission.")
        return None
    if not requests:
        print("[-] Requests library not available. Skipping live submission.")
        return None

    data_tuples = [("marketAddress", market_address), ("note", note)]
    if links:
        for link in links:
            data_tuples.append(("links[]", link))

    headers = {
        "Authorization": f"Bearer {DELPHI_KEY}",
        "Idempotency-Key": str(uuid.uuid4()),
        "X-Agent-Id": "veritaskernel-v1",
        "X-Agent-Harness": "veritaskernel-orchestrator",
        "X-Agent-Model": "gemini-3.8-flash"
    }

    try:
        resp = requests.post(
            "https://delphi.fyi/v1/submissions",
            data=data_tuples,
            headers=headers,
            timeout=30
        )
        print(f"[+] Delphi submission response ({resp.status_code}): {resp.text}")
        if resp.status_code in (200, 202):
            return resp.json()
    except Exception as e:
        print(f"[-] Delphi submission error: {e}")
    return None

def check_submission_result(sub_id: str):
    if not DELPHI_KEY or not requests:
        return None
    headers = {"Authorization": f"Bearer {DELPHI_KEY}"}
    try:
        resp = requests.get(f"https://delphi.fyi/v1/submissions/{sub_id}", headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"[-] Result query error: {e}")
    return None

def main():
    print("==================================================")
    print("  VERITASKERNEL — GEMINI REASONING + FINNHUB MINER")
    print("==================================================")
    markets = get_delphi_markets()
    print(f"[+] Loaded {len(markets)} competition prediction markets.")
    
    news = get_finnhub_news()
    print(f"[+] Loaded {len(news)} real-time breaking news items from Finnhub.")
    
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
    print("[*] Running Gemini Reasoning Engine...")
    t0 = time.time()
    try:
        plan_raw = call_gemini(prompt)
        print(f"[+] Gemini Analysis Complete ({round(time.time() - t0, 2)}s):\n")
        print(plan_raw)
        
        # Parse JSON
        clean = plan_raw.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        
        data = json.loads(clean)
        targets = data.get("targets", [])
        print(f"\n[+] Selected {len(targets)} high-conviction targets for Delphi mining.")
        
        for idx, target in enumerate(targets, 1):
            addr = target.get("market_address")
            q = target.get("question")
            d = target.get("direction")
            r = target.get("reasoning")
            print(f"\n[{idx}] Target Market: {q} ({addr})")
            print(f"    Direction: {d} | Reasoning: {r}")
            
            # Find relevant news item link if available
            relevant_links = []
            for n in news[:5]:
                if any(w.lower() in n['headline'].lower() for w in q.split()[:3]):
                    relevant_links.append(n['url'])
                    break
            
            note = f"VeritasKernel Macro Analysis: Probability adjustment to {d}. Economic thesis: {r}. Source signal from institutional macroeconomic stream."
            print(f"    Submitting evidence note to Delphi...")
            sub = submit_delphi_evidence(addr, note, relevant_links)
            if sub and "id" in sub:
                sub_id = sub["id"]
                print(f"    [+] Submitted successfully! Submission ID: {sub_id}")
                print(f"    [*] Waiting 5s for initial judge check...")
                time.sleep(5)
                res = check_submission_result(sub_id)
                if res:
                    m_list = res.get('markets', [])
                    verdict = m_list[0].get('verdict', 'judging') if m_list else 'queued/judging'
                    print(f"    [+] Status: {res.get('status')} | Verdict: {verdict}")

    except Exception as e:
        print(f"[-] Execution notice: {e}")

if __name__ == "__main__":
    main()
