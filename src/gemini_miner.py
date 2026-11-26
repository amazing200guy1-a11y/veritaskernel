"""
VeritasKernel: Gemini Reasoning + Mathematical Evidence Miner
Analyzes active Delphi prediction markets, extracts primary statistical series,
and submits objective mathematical derivations adhering strictly to Delphi's oracle rules.
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
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent",
        "https://generativelanguage.googleapis.com/v1/models/gemini-3.1-flash-lite:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    ]
    last_err = None
    for ep in endpoints:
        url = f"{ep}?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1}
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
    cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "markets.json")
    url = "https://competition.delphi.fyi/markets.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass
            return data
    except Exception as e:
        print(f"[-] Note: Delphi live markets query timed out ({e}), using local cache.")
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        raise e

def submit_delphi_evidence(market_address: str, note: str, links: list = None, file_path: str = None):
    if not DELPHI_KEY or not requests:
        print("[-] DELPHI_API_ACCESS_KEY or requests not set. Skipping live submission.")
        return None

    data_tuples = [("marketAddress", market_address), ("note", note)]
    if links:
        for link in links:
            if link:
                data_tuples.append(("links[]", link))

    files_payload = None
    if file_path and os.path.exists(file_path):
        try:
            files_payload = {
                "files": (os.path.basename(file_path), open(file_path, "rb"), "application/json")
            }
        except Exception as e:
            print(f"[-] Could not attach file: {e}")

    headers = {
        "Authorization": f"Bearer {DELPHI_KEY}",
        "Idempotency-Key": str(uuid.uuid4()),
        "X-Agent-Id": "veritaskernel-v1",
        "X-Agent-Harness": "veritaskernel-orchestrator",
        "X-Agent-Model": "gemini-flash-lite-latest"
    }

    try:
        resp = requests.post(
            "https://delphi.fyi/v1/submissions",
            data=data_tuples,
            files=files_payload,
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

def get_submitted_market_addresses():
    submitted = set()
    reg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "submitted_registry.json")
    if os.path.exists(reg_path):
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                for addr in json.load(f):
                    submitted.add(addr.lower())
        except Exception:
            pass

    if DELPHI_KEY and requests:
        headers = {"Authorization": f"Bearer {DELPHI_KEY}"}
        try:
            resp = requests.get("https://delphi.fyi/v1/submissions?limit=50", headers=headers, timeout=10)
            items = resp.json().get("items", [])
            for s in items:
                for m in s.get("markets", []):
                    addr = m.get("marketAddress")
                    if addr:
                        submitted.add(addr.lower())
        except Exception as e:
            print(f"[-] Note: Delphi remote query timed out ({e}), using local registry.")
    return submitted

def main():
    print("==================================================")
    print("  VERITASKERNEL — MATHEMATICAL EVIDENCE MINER")
    print("==================================================")
    markets = get_delphi_markets()
    print(f"[+] Loaded {len(markets)} competition prediction markets.")
    
    # Check which markets we have already submitted to
    submitted_addrs = get_submitted_market_addresses()
    print(f"[+] Found {len(submitted_addrs)} markets already submitted on this account.")
    
    # Automatically march down to unsubmitted markets!
    target_candidates = [
        m for m in markets 
        if m.get("address", "").lower() not in submitted_addrs
        and m.get("category") in ("official_statistics", "votes_government", "releases_standards")
    ][:5]
    
    if not target_candidates:
        target_candidates = [
            m for m in markets 
            if m.get("address", "").lower() not in submitted_addrs
        ][:5]
    
    print(f"[+] Automatically targeted {len(target_candidates)} fresh unsubmitted markets.")
    
    prompt = f"""You are the VeritasKernel Quantitative Forensic Analyst.
Below are active Delphi prediction markets on official statistics and events:
{json.dumps([{'address': m['address'], 'question': m['question'], 'category': m['category'], 'closesAt': m['closesAt'], 'odds': m['odds']} for m in target_candidates], indent=2)}

Task:
Select the top 2 markets and generate a mathematically rigorous evidence note for each, formatted strictly according to Delphi's earning criteria:
1. The fact: Latest published official baseline figure or state, with exact number and date.
2. The source: Official authority (e.g., Destatis, Swiss FSO, TurkStat, BLS, Federal Chancellery), publication date, and official portal URL.
3. Relevance: How this directly bears on the resolution threshold in the question.
4. Arithmetic & Working:
   - Delta required between latest baseline and resolution threshold.
   - Required rate of change (e.g., MoM change) needed to cross the threshold.
   - Historical context / empirical frequency of such rate over the past 10-15 years.

STRICT RULES:
- Do NOT steer the judge.
- Do NOT say 'Vote YES', 'Vote NO', or 'Probability adjustment'.
- Keep each note strictly factual, mathematical, and under 800 characters.

Return strictly valid JSON:
{{
  "submissions": [
    {{
      "market_address": "0x...",
      "question": "string",
      "note": "1. Fact: ... 2. Source: ... 3. Relevance: ... 4. Arithmetic: ...",
      "source_url": "https://..."
    }}
  ]
}}
"""
    print("[*] Running Quantitative Reasoning Engine...")
    t0 = time.time()
    try:
        plan_raw = call_gemini(prompt)
        print(f"[+] Quantitative Analysis Complete ({round(time.time() - t0, 2)}s):\n")
        
        clean = plan_raw.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        
        import re
        clean_sanitized = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', clean)
        try:
            data = json.loads(clean_sanitized, strict=False)
        except Exception:
            data = json.loads(clean, strict=False)
        
        submissions = data.get("submissions", [])
        print(f"[+] Prepared {len(submissions)} compliant mathematical submissions.")
        
        for idx, sub in enumerate(submissions, 1):
            addr = sub.get("market_address")
            q = sub.get("question")
            note = sub.get("note")
            url = sub.get("source_url")
            print(f"\n[{idx}] Market: {q} ({addr})")
            print(f"    Dispatching mathematical evidence note...")
            
            os.makedirs("data/snapshots", exist_ok=True)
            snap_path = f"data/snapshots/mkt_{addr[:10]}.json"
            snap_data = {
                "market_address": addr,
                "question": q,
                "source_url": url,
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "mathematical_note": note
            }
            with open(snap_path, "w", encoding="utf-8") as f:
                json.dump(snap_data, f, indent=2)

            res = submit_delphi_evidence(addr, note, [url] if url else None, file_path=snap_path)
            if res and "id" in res:
                sub_id = res["id"]
                print(f"    [+] Submitted! ID: {sub_id}")
                try:
                    reg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "submitted_registry.json")
                    with open(reg_path, "r", encoding="utf-8") as f:
                        reg = json.load(f)
                    if addr.lower() not in [x.lower() for x in reg]:
                        reg.append(addr.lower())
                        with open(reg_path, "w", encoding="utf-8") as f:
                            json.dump(reg, f, indent=2)
                except Exception:
                    pass
                time.sleep(5)
                status_res = check_submission_result(sub_id)
                if status_res:
                    m_list = status_res.get("markets", [])
                    status_text = status_res.get("status")
                    verdict = m_list[0].get("verdict") if m_list else "in_evaluation"
                    print(f"    [+] Current Oracle Status: {status_text} | Verdict: {verdict}")

    except Exception as e:
        print(f"[-] Execution notice: {e}")

if __name__ == "__main__":
    main()
