import requests
import os
import json
from sentence_transformers import SentenceTransformer, util
import time

SHEET_ENDPOINT = os.environ.get("SHEET_ENDPOINT")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

BUSINESS_KEYWORDS = os.environ.get("BUSINESS_KEYWORDS", "civil construction,road work").split(",")

model = SentenceTransformer('all-MiniLM-L6-v2')

from crawler_template import crawl_example_simple_site

def post_to_sheet(tenders):
    if not SHEET_ENDPOINT:
        print("No sheet endpoint configured. Skipping posting.")
        return
    resp = requests.post(SHEET_ENDPOINT, json=tenders, timeout=30)
    print("Posted to sheet:", resp.text)

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("No telegram creds. Skipping send.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    r = requests.post(url, data=data, timeout=20)
    print("Telegram send:", r.status_code, r.text)

def is_similar(a, b):
    a_emb = model.encode(a, convert_to_tensor=True)
    b_emb = model.encode(b, convert_to_tensor=True)
    score = util.cos_sim(a_emb, b_emb).item()
    return score

def run_pipeline():
    crawled = []
    crawled.extend(crawl_example_simple_site())

    unique = {}
    for t in crawled:
        if t['hash'] not in unique:
            unique[t['hash']] = t

    items = list(unique.values())

    final = []
    for t in items:
        is_dup = False
        for f in final:
            sim = is_similar(t['title'], f['title'])
            if sim > 0.90:
                is_dup = True
                break
        if not is_dup:
            final.append(t)

    results_to_post = []
    for t in final:
        max_score = 0.0
        for k in BUSINESS_KEYWORDS:
            sc = is_similar(t['title'], k.strip())
            if sc > max_score:
                max_score = sc
        match_pct = round(max_score * 100, 2)
        t['match_score'] = match_pct
        if match_pct >= 60:
            results_to_post.append(t)

    if results_to_post:
        post_to_sheet(results_to_post)

    if results_to_post:
        msg = "<b>TenderGenie — Top Matches</b>\n\n"
        for r in results_to_post[:10]:
            msg += f"{r['title']} (Score: {r['match_score']}%)\n{r['url']}\n\n"
        send_telegram(msg)
    else:
        send_telegram("TenderGenie: No good matches found today.")

if __name__ == "__main__":
    run_pipeline()
