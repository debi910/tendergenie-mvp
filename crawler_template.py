import requests
from bs4 import BeautifulSoup
import hashlib
import uuid
from dateutil import parser

def normalize_text(t):
    return ''.join(ch.lower() for ch in t if ch.isalnum() or ch.isspace()).strip()

def make_hash(text):
    return hashlib.md5(normalize_text(text).encode()).hexdigest()

def crawl_example_simple_site():
    url = "https://example.com/tenders"  # Replace with real site later
    r = requests.get(url, timeout=20)
    soup = BeautifulSoup(r.text, "lxml")
    items = []
    for node in soup.select(".tender-item"):  # Update CSS selector per site
        title = node.select_one(".title").get_text(strip=True)
        org = node.select_one(".org").get_text(strip=True) if node.select_one(".org") else ""
        closing = node.select_one(".closing").get_text(strip=True) if node.select_one(".closing") else ""
        link = node.select_one("a")["href"]
        try:
            closing_date = parser.parse(closing).strftime("%Y-%m-%d")
        except:
            closing_date = ""
        tid = str(uuid.uuid4())
        items.append({
            "id": tid,
            "title": title,
            "organization": org,
            "location": "",
            "closing_date": closing_date,
            "budget": "",
            "url": link,
            "hash": make_hash(title)
        })
    return items

if __name__ == "__main__":
    results = crawl_example_simple_site()
    for r in results:
        print(r)
