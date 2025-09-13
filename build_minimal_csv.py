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
        "magnesium","creatine","protein water","gut health","microbiome","prebiotic","ele
