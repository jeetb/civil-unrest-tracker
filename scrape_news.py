import feedparser
import pandas as pd
from datetime import datetime

query_url = 'https://news.google.com/rss/search?q=protest+OR+riot+OR+looting+OR+march&hl=en-US&gl=US&ceid=US:en'
feed = feedparser.parse(query_url)

entries = []
for entry in feed.entries:
    entries.append({
        'platform': 'news',
        'title': entry.title,
        'summary': entry.summary,
        'date': entry.published,
        'url': entry.link,
        'source': entry.get('source', {}).get('title', 'Unknown')
    })

df = pd.DataFrame(entries)
df.to_csv('data/raw/news_signals.csv', index=False)
print(f"Scraped {len(entries)} news articles.")
