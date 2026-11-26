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

def fetch_live_market_telemetry(market: dict) -> dict:
    """Fetch real-time primary-source telemetry for a market (e.g., GitHub releases) so derivations are 100% verifiable."""
    telemetry = {}
    sources = market.get("dataSources", [])
    for src in sources:
        if "api.github.com/repos/" in src and "/releases" in src:
            try:
                api_url = src.split("?")[0] + "?per_page=15"
                headers = {"User-Agent": "VeritasKernel-Miner/1.0", "Accept": "application/vnd.github+json"}
                req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    releases = json.loads(resp.read().decode("utf-8"))
                from datetime import datetime
                stable = []
                for r in releases:
                    if not r.get("prerelease") and r.get("published_at"):
                        stable.append({
                            "tag": r.get("tag_name"),
                            "published_at": r.get("published_at")
                        })
                if len(stable) >= 2:
                    t0 = datetime.fromisoformat(stable[0]["published_at"].replace("Z", "+00:00"))
                    t_last = datetime.fromisoformat(stable[-1]["published_at"].replace("Z", "+00:00"))
                    span_days = max((t0 - t_last).total_seconds() / 86400.0, 0.01)
                    lam = (len(stable) - 1) / span_days
                    telemetry["github_releases"] = {
                        "source": api_url,
                        "latest_tag": stable[0]["tag"],
                        "latest_published_at": stable[0]["published_at"],
                        "oldest_sampled_tag": stable[-1]["tag"],
                        "oldest_sampled_at": stable[-1]["published_at"],
                        "sample_count": len(stable),
                        "span_days": round(span_days, 2),
                        "empirical_lambda_per_day": round(lam, 4),
                        "recent_5_tags": stable[:5]
                    }
                break
            except Exception as e:
                telemetry["github_fetch_error"] = str(e)
    return telemetry

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
    
    # Automatically prioritize high-alpha unsubmitted markets!
    priority_addrs = [
        "0x921e39354e4bfc18251ad1b1c80eec1a3940ab82",  # Bun GitHub release
        "0xf640443d15af94932e1a7294c15312f0ad9e1136",  # Go release
        "0x6d14f2291c886a3469e988a7f80d307802a40c0a",  # BLS NFP
        "0xb50e81264ad92791f9849f7f83e0dbad03a39861",  # Mexico CPI
        "0x94dbba7c9b44b788a701602ab6d919ff7b7fc38a"   # Swiss Turnout
    ]
    
    unsubmitted = [m for m in markets if m.get("address", "").lower() not in submitted_addrs]
    
    # Sort with priority addresses first
    def get_priority(m):
        addr = m.get("address", "").lower()
        for idx, p in enumerate(priority_addrs):
            if addr == p.lower():
                return idx
        return 999
        
    unsubmitted.sort(key=get_priority)
    target_candidates = unsubmitted[:4]
    
    print(f"[+] Automatically targeted {len(target_candidates)} fresh unsubmitted markets:")
    enriched_candidates = []
    for tc in target_candidates:
        print(f"    - {tc.get('address')[:10]}...: {tc.get('question')[:60]}")
        live_tel = fetch_live_market_telemetry(tc)
        if live_tel:
            print(f"      [+] Live telemetry fetched: {list(live_tel.keys())}")
        enriched_candidates.append({
            "address": tc["address"],
            "question": tc["question"],
            "category": tc["category"],
            "closesAt": tc["closesAt"],
            "odds": tc["odds"],
            "dataSources": tc.get("dataSources", []),
            "live_verified_telemetry": live_tel
        })
    
    prompt = f"""You are the VeritasKernel Quantitative Forensic Analyst.
Below are active Delphi prediction markets WITH LIVE VERIFIED PRIMARY-SOURCE TELEMETRY:
{json.dumps(enriched_candidates, indent=2)}

Task:
Generate a mathematically rigorous, novel leading-indicator evidence note for each candidate market that provides positive Information Gain (Delta I > 0) to Delphi's oracle forecaster.

DELPHI JUDGING CRITERIA (TO EARN ACCEPTED STATUS & USDC BOUNTY):
- To be ACCEPTED (not duplicate and not unverifiable), you MUST ground [Empirical Telemetry] in the exact numbers from `live_verified_telemetry` (when present) or verifiable `dataSources` — NEVER invent or guess dates, tags, or counts.
- Do NOT simply restate stale public baseline facts.
- Do NOT steer the oracle (NEVER say 'Vote YES', 'Vote NO', 'We predict', or 'Probability adjustment').
- Keep each note strictly under 800 characters and structured into exactly 4 parts:
  [Empirical Telemetry]: Specific measurable data (e.g. exact latest tag, release timestamps, sample count, span days, empirical lambda).
  [Primary Source]: Canonical official portal/endpoint URL from dataSources.
  [Stochastic Model]: The formal statistical/probability model used (e.g., Stationary Poisson Point Process P(K>=1)=1-exp(-lambda*t), OLS regression, or Bayes factor update).
  [Quantitative Derivation]: The exact numerical calculation, resulting in the model-implied probability vs current market odds.

Return strictly valid JSON:
{{
  "submissions": [
    {{
      "market_address": "0x...",
      "question": "string",
      "note": "[Empirical Telemetry] ... [Primary Source] ... [Stochastic Model] ... [Quantitative Derivation] ...",
      "source_url": "https://...",
      "snapshot_data": {{
        "metric": "...",
        "value": 0.0,
        "derivation": "..."
      }}
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
                "mathematical_note": note,
                "leading_telemetry": sub.get("snapshot_data", {})
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
