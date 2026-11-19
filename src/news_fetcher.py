"""
VeritasKernel — Free Real-Time News & Primary Source Ingestion Engine
Fetches breaking headlines from free public RSS feeds (SEC, Reuters, Yahoo Finance, CoinDesk)
and Finnhub without requiring expensive paid subscriptions.
"""

import urllib.request
import xml.etree.ElementTree as ET
import time
import re
from typing import List, Dict, Any, Optional

class NewsFetcher:
    def __init__(self, finnhub_api_key: Optional[str] = None):
        self.finnhub_api_key = finnhub_api_key
        # Free, verified high-speed RSS endpoints
        self.rss_feeds = {
            "sec_gov": "https://www.sec.gov/news/pressreleases.rss",
            "yahoo_finance": "https://finance.yahoo.com/news/rssindex",
            "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "reuters_business": "https://feeds.feedburner.com/reuters/businessNews"
        }

    def fetch_rss_feed(self, url: str, timeout: int = 8) -> List[Dict[str, Any]]:
        """
        Fetches and parses an RSS feed using Python standard library xml.etree.
        Returns a list of standardized items: title, description, link, pub_date.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VeritasKernel/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml"
        }
        items = []
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                
                # Standard RSS <channel><item>
                for item in root.findall('.//item'):
                    title = item.findtext('title', default='').strip()
                    desc = item.findtext('description', default='').strip()
                    link = item.findtext('link', default='').strip()
                    pub_date = item.findtext('pubDate', default='').strip()
                    
                    # Clean HTML tags from description if present
                    clean_desc = re.sub(r'<[^>]+>', ' ', desc)
                    clean_desc = ' '.join(clean_desc.split())

                    if title:
                        items.append({
                            "title": title,
                            "summary": clean_desc,
                            "link": link,
                            "pub_date": pub_date,
                            "full_text": f"{title}. {clean_desc}"
                        })
        except Exception as e:
            # Non-blocking catch to ensure pipeline resilience across network hiccups
            pass
        return items

    def parse_rss_string(self, xml_string: str) -> List[Dict[str, Any]]:
        """Utility method to parse raw RSS XML string (used for tests and offline mocks)."""
        items = []
        try:
            root = ET.fromstring(xml_string)
            for item in root.findall('.//item'):
                title = item.findtext('title', default='').strip()
                desc = item.findtext('description', default='').strip()
                link = item.findtext('link', default='').strip()
                pub_date = item.findtext('pubDate', default='').strip()
                clean_desc = re.sub(r'<[^>]+>', ' ', desc)
                items.append({
                    "title": title,
                    "summary": clean_desc,
                    "link": link,
                    "pub_date": pub_date,
                    "full_text": f"{title}. {clean_desc}"
                })
        except Exception:
            pass
        return items

    def search_news_for_market(self, market_keywords: List[str], max_items: int = 5) -> List[Dict[str, Any]]:
        """
        Polls configured free feeds and filters items matching market keywords.
        """
        all_candidates = []
        # Precompile keyword patterns
        kw_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) for kw in market_keywords if len(kw) > 2]

        for feed_name, feed_url in self.rss_feeds.items():
            feed_items = self.fetch_rss_feed(feed_url)
            for item in feed_items:
                text = item["full_text"]
                hits = sum(1 for p in kw_patterns if p.search(text))
                if hits >= 1:
                    item["keyword_hits"] = hits
                    item["source_feed"] = feed_name
                    all_candidates.append(item)

        # Sort by keyword match density
        all_candidates.sort(key=lambda x: x.get("keyword_hits", 0), reverse=True)
        return all_candidates[:max_items]
