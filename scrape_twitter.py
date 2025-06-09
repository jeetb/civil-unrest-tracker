import snscrape.modules.twitter as sntwitter
import pandas as pd
from datetime import datetime

# Keywords and time window
QUERY = '(protest OR riot OR shooting OR looting OR march OR unrest) since:2025-06-01'
LIMIT = 100  # Adjust later

results = []

for tweet in sntwitter.TwitterSearchScraper(QUERY).get_items():
    if len(results) >= LIMIT:
        break
    results.append({
        'platform': 'twitter',
        'text': tweet.content,
        'author': tweet.user.username,
        'date': tweet.date.strftime('%Y-%m-%d %H:%M:%S'),
        'url': tweet.url
    })

# Save to CSV or JSON
df = pd.DataFrame(results)
df.to_csv('data/raw/twitter_protest_signals.csv', index=False)
