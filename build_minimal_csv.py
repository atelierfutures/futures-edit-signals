# builds docs/signals_simple.csv with 7 columns (no notebook needed)
import os, time, feedparser, pandas as pd
from urllib.parse import urlparse
from datetime import datetime, timezone
from dateutil import parser as dateparser

FEEDS = {
    "fashion": [
        "https://www.hypebeast.com/feed",
        "https://www.highsnobiety.com/feed",
        "https://theimpression.com/feed/",
        "https://news.google.com/rss/search?q=fashion%20innovation&hl=en&gl=US&ceid=US:en",
    ],
    "beauty": [
        "https://www.beautymatter.com/rss.xml",
        "https://www.allure.com/feed/all/rss",
        "https://www.glossy.co/feed/",
        "https://news.google.com/rss/search?q=beauty%20skincare%20trend&hl=en&gl=US&ceid=US:en",
    ],
    "wellness": [
        "https://www.wellandgood.com/feed/",
        "https://www.mindbodygreen.com/feeds/latest",
        "https://examine.com/feed/",
        "https://news.google.com/rss/search?q=wellness%20longevity%20trend&hl=en&gl=US&ceid=US:en",
    ],
}

SEEDS = {
    "fashion": ["quiet luxury","balletcore","coquette","techwear","gorpcore","upcycled","denim","crochet","rental","resale","kitten heels","ballet flats"],
    "beauty":  ["skin cycling","skin barrier","slugging","glass skin","lip oil","peptide","microbiome","mushroom","adaptogen","LED mask","SPF","mineral sunscreen"],
    "wellness":["longevity","GLP-1","red light","cold plunge","sauna","breathwork","magnesium","creatine","gut health","electrolytes","sleep","HRV","zone 2","pilates"],
}

def clean(txt): return (txt or "").replace("\n"," ").strip()

def recency_score(dt_iso):
    if not dt_iso: return 0.5
    try:
        dt = dateparser.parse(dt_iso)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days = max((now - dt).days, 0)
        return max(0.0, 1.0 - days/30.0)
    except Exception:
        return 0.5

def fetch_one(url, category):
    d = feedparser.parse(url)
    rows=[]
    for e in d.entries:
        title = clean(e.get("title"))
        link  = e.get("link")
        desc  = clean(e.get("summary") or e.get("description") or "")
        pub   = e.get("published") or e.get("updated") or e.get("created")
        pub_iso = dateparser.parse(pub).isoformat() if pub else None

        # primitive keyword detection
        seeds = SEEDS.get(category, [])
        lower = (title + " " + desc).lower()
        hits = [k for k in seeds if k.lower() in lower]
        primary_keyword = hits[0] if hits else ""

        score = round(0.7*len(hits) + 0.3*(recency_score(pub_iso)*2.0), 2)

        rows.append({
            "published": pub_iso,
            "title": title,
            "link": link,
            "category": category,
            "primary_keyword": primary_keyword,
            "trend_score": score,
            "status": ""  # leave empty or compute later if you want
        })
    return rows

all_rows=[]
for cat, feed_list in FEEDS.items():
    for u in feed_list:
        try:
            all_rows += fetch_one(u, cat)
            time.sleep(0.2)
        except Exception:
            pass

df = pd.DataFrame(all_rows)
df = df.sort_values(["category","published"], ascending=[True, False])
os.makedirs("docs", exist_ok=True)
df.to_csv("docs/signals_simple.csv", index=False)
print("✅ wrote docs/signals_simple.csv with", len(df), "rows")
