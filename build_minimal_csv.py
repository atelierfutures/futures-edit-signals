# builds docs/signals_simple.csv with 7 columns (no notebook needed)
# - pulls RSS feeds
# - sets primary_keyword using seeds OR a simple auto-extractor (no extra libs)
# - scores recency + hits
# - classifies status by percentiles (emerging / bubbling / mainstream)

import os, time, re, feedparser, pandas as pd
from datetime import datetime, timezone
from dateutil import parser as dateparser
from collections import Counter

# ---------- CONFIG ----------
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

# Multilingual seed hints (EN/ES/FR). Add more any time.
SEEDS = {
    "fashion": [
        "quiet luxury","stealth wealth","balletcore","coquette","blokette","mob wife",
        "archival","gorpcore","techwear","digital couture","3d knit","upcycled",
        "deadstock","rental","resale","made-to-order","kitten heels","ballet flats","rosette","bows"
    ],
    "beauty": [
        "skin cycling","skin flooding","skin barrier","slugging","glass skin","jello skin","mochi skin",
        "latte makeup","lip oil","lip stain","peptide","copper peptide","fermented","microbiome",
        "mushroom","adaptogen","spf stick","mineral sunscreen","led mask","red light","microcurrent","scalp care"
    ],
    "wellness": [
        "longevity","glp-1","red light","cold plunge","sauna","heat therapy","breathwork","vagus nerve",
        "magnesium","creatine","protein water","gut health","microbiome","prebiotic","electrolyte",
        "sleep hygiene","mouth taping","hrv","zone 2","rucking","pilates","mobility","lymphatic"
    ],
}
# ---------- /CONFIG ----------

STOP = {
    # tiny multilingual stopword set (EN/ES/FR)
    "the","and","for","with","from","that","this","into","over","under","your","their","our",
    "de","la","el","los","las","un","una","en","con","por","para","del","al","y","que",
    "le","la","les","des","du","de","et","pour","dans","sur","au","aux","une","un",
    "new","news","trend","trends","brand","brands","make","made","just","today","2025","2024"
}

def clean(txt):
    return (txt or "").replace("\n", " ").strip()

def recency_score(dt_iso):
    if not dt_iso: 
        return 0.5
    try:
        dt = dateparser.parse(dt_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days = max((now - dt).days, 0)
        return max(0.0, 1.0 - days/30.0)  # decays over ~30 days
    except Exception:
        return 0.5

def simple_auto_keyword(title, summary):
    """Very small fallback extractor: pick the most frequent non-stopword token
    from title+summary; prefer 2–3 word phrase if the same token repeats adjacently."""
    text = f"{title or ''} {summary or ''}".lower()
    tokens = re.findall(r"[a-záéíóúüñç'-]{3,}", text)
    tokens = [t.strip("-'") for t in tokens if t not in STOP]
    if not tokens:
        return ""
    # try bigram frequency first
    bigrams = [" ".join(p) for p in zip(tokens, tokens[1:])]
    bigrams = [b for b in bigrams if all(w not in STOP for w in b.split())]
    if bigrams:
        top2 = Counter(bigrams).most_common(1)[0][0]
        if len(top2.split()) >= 2:
            return top2
    # fall back to single token
    return Counter(tokens).most_common(1)[0][0]

def fetch_one(url, category):
    d = feedparser.parse(url)
    rows = []
    seeds = [s.lower() for s in SEEDS.get(category, [])]
    for e in d.entries:
        title = clean(e.get("title"))
        link  = e.get("link")
        desc  = clean(e.get("summary") or e.get("description") or "")
        pub   = e.get("published") or e.get("updated") or e.get("created")
        pub_iso = dateparser.parse(pub).isoformat() if pub else None

        text_l = f"{title} {desc}".lower()
        hits = [k for k in seeds if k in text_l]
        primary = hits[0] if hits else simple_auto_keyword(title, desc)

        score = round(0.7*len(hits) + 0.3*(recency_score(pub_iso)*2.0), 2)

        rows.append({
            "published": pub_iso,
            "title": title,
            "link": link,
            "category": category,
            "primary_keyword": primary,
            "trend_score": score,
            "status": ""  # filled later
        })
    return rows

# Crawl feeds
all_rows = []
for cat, urls in FEEDS.items():
    for u in urls:
        try:
            all_rows += fetch_one(u, cat)
            time.sleep(0.2)
        except Exception:
            pass

df = pd.DataFrame(all_rows)
if not df.empty:
    df = df.sort_values(["category","published"], ascending=[True, False])

    # ----- status by percentiles on trend_score -----
    scores = pd.to_numeric(df["trend_score"], errors="coerce").fillna(0)
    p33 = float(scores.quantile(0.33))
    p66 = float(scores.quantile(0.66))

    def status_for(x):
        if x >= p66: return "mainstream"
        if x >= p33: return "bubbling"
        return "emerging"

    df["status"] = scores.apply(status_for)

# Save to docs/ (served by GitHub Pages)
os.makedirs("docs", exist_ok=True)
df.to_csv("docs/signals_simple.csv", index=False)
print("✅ wrote docs/signals_simple.csv with", len(df), "rows")
