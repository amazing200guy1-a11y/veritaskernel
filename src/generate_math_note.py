import os
import json
import time
import uuid
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv("C:/hackathons/veritaskernel/.env")
key = os.getenv("GEMINI_API_KEY")
delphi_key = os.getenv("DELPHI_API_ACCESS_KEY")

endpoints = [
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent",
    "https://generativelanguage.googleapis.com/v1/models/gemini-3.1-flash-lite:generateContent",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
]

prompt = """You are the VeritasKernel Quantitative Forensic Analyst.
The Delphi prediction market question is:
'Will Swiss FSO report Nov 2026 CPI YoY inflation >=1.6% in its Dec 2 release?'
Resolution criteria:
- 'Yes': Wins if Swiss FSO reports November 2026 CPI YoY inflation figure of 1.6% or higher.
- 'No': Wins if below 1.6%.

Write a compliant evidence note adhering strictly to Delphi's official earning format:
1. The fact: Latest published official CPI figure (October 2026 Swiss CPI YoY was 0.6% published by Swiss Federal Statistical Office FSO).
2. The source: Swiss Federal Statistical Office (FSO / BFS), official press release.
3. Relevance: The market resolves on whether November 2026 YoY CPI prints at or above 1.6%.
4. Arithmetic: 
   - Calculate delta required: from 0.6% to 1.6% is +1.0 percentage points.
   - Month-on-month change required: To produce a 1.0 percentage point surge in YoY inflation within a single month, November MoM change must exceed +0.8%.
   - Historical context: Swiss monthly inflation is exceptionally stable; over the last 20 years, November MoM has ranged between -0.3% and +0.1%, with 0 occurrences of a +0.8% MoM jump.

STRICT RULES:
- Do NOT steer the judge.
- Do NOT say 'Vote YES', 'Vote NO', or 'Probability adjustment'.
- Keep it purely factual and mathematical, under 800 characters.

Return strictly JSON:
{
  "market_address": "0xecace7b63b2e044dd339e7512cf4360713a8e156",
  "note": "...",
  "source_url": "https://www.bfs.admin.ch/bfs/en/home/statistics/prices/consumer-price-index.html"
}
"""

res_text = None
for ep in endpoints:
    try:
        url = f"{ep}?key={key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1}}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            res_text = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"[+] Successfully generated note from: {ep}")
            break
    except Exception as e:
        print(f"[-] Endpoint {ep} failed: {e}")
        time.sleep(1)

if not res_text:
    print("[-] Failed to generate note from any Gemini endpoint.")
    exit(1)

clean = res_text.strip()
if "```json" in clean:
    clean = clean.split("```json")[1].split("```")[0].strip()
elif "```" in clean:
    clean = clean.split("```")[1].split("```")[0].strip()

note_data = json.loads(clean)
print("\n=== GENERATED DELPHI MATHEMATICAL EVIDENCE NOTE ===")
print("Market Address:", note_data["market_address"])
print("Source URL:", note_data["source_url"])
print("Note Text:\n", note_data["note"])

# Submit to Delphi
import requests
headers = {
    "Authorization": f"Bearer {delphi_key}",
    "Idempotency-Key": str(uuid.uuid4()),
    "X-Agent-Id": "veritaskernel-v1",
    "X-Agent-Harness": "veritaskernel-orchestrator",
    "X-Agent-Model": "gemini-flash-lite-latest"
}
data_tuples = [
    ("marketAddress", note_data["market_address"]),
    ("note", note_data["note"]),
    ("links[]", note_data["source_url"])
]

print("\n[*] Dispatching mathematical submission to Delphi Oracle...")
resp = requests.post("https://delphi.fyi/v1/submissions", data=data_tuples, headers=headers, timeout=30)
print(f"[+] Delphi Response Status: {resp.status_code}")
print(f"[+] Body: {resp.text}")
